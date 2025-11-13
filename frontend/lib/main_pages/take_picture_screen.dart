import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import 'package:cookduck/main_pages/recipe_result_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:cookduck/services/api_service.dart';

class TakePictureScreen extends StatefulWidget {
  const TakePictureScreen({super.key});

  @override
  State<TakePictureScreen> createState() => _TakePictureScreenState();
}

class _TakePictureScreenState extends State<TakePictureScreen> {
  XFile? _image;
  final ImagePicker _picker = ImagePicker();
  bool _isLoading = false;
  List<String> seasonings = [];

  Future<void> _takePicture() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.camera);
    if (image != null) {
      setState(() {
        _image = image;
      });
      await _analyzeImage();
    }
  }

  Future<void> _pickFromGallery() async {
    final XFile? image = await _picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      setState(() {
        _image = image;
      });
      await _analyzeImage();
    }
  }

  Future<void> _analyzeImage() async {
    if (_image == null) return;

    setState(() {
      _isLoading = true;
    });

    try {
      // 1. userId 불러오기
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getString('user_id') ?? '';
      print('조미료 API 요청 userId: $userId');
      if (userId.isEmpty) throw Exception('userId를 찾을 수 없습니다.');

      // 2. 조미료 API 호출
      final apiService = ApiService();
      final seasoningData = await apiService.get('/user-seasonings/$userId');
      print('조미료 API 응답: \\n$seasoningData');
      final List<String> result = [];
      if (seasoningData is Map<String, dynamic>) {
        seasoningData.forEach((key, value) {
          if (value == true) {
            result.add(key);
          }
        });
      }
      seasonings = result;

      // 3. 이미지 분석(식재료) API 호출
      final ingredientsData = await apiService.postMultipart(
        '/fastapi/predict',
        'image',
        _image!.path,
        includeAuth: false,
      );
      print('식재료 분석 API 응답: \\n$ingredientsData');
      var ingredients = List<String>.from(ingredientsData);

      // 4. 주재료/부재료 구분
      // 조미료 키워드 리스트 (FastAPI의 classify_user_ingredients와 동일)
      final subIngredientKeywords = [
        '소금', '설탕', '후추', '간장', '된장', '고추장', '식초', '참기름',
        '식용유', '물', '마늘', '파', '양파'
      ];
      
      // 이미지에서 인식된 재료는 주재료로, 조미료는 부재료로 분류
      List<String> mainIngredients = [];
      List<String> subIngredients = [];
      
      // 이미지에서 인식된 재료 처리
      for (var ing in ingredients) {
        bool isSub = false;
        for (var keyword in subIngredientKeywords) {
          if (ing.contains(keyword)) {
            isSub = true;
            break;
          }
        }
        if (isSub) {
          subIngredients.add(ing);
        } else {
          mainIngredients.add(ing);
        }
      }
      
      // 조미료는 모두 부재료로 추가
      subIngredients.addAll(seasonings);
      
      // 전체 재료 목록 (주재료 + 부재료)
      final allIngredients = [...mainIngredients, ...subIngredients];
      
      print('주재료: $mainIngredients');
      print('부재료: $subIngredients');
      print('전체 재료: $allIngredients');

      // 4-1. 재료 DB 저장
      try {
        await apiService.post(
          '/user-ingredients/$userId',
          {
            'main_ingredients': mainIngredients,
            'sub_ingredients': subIngredients,
          },
        );
        print('재료 DB 저장 완료');
      } catch (e) {
        print('재료 DB 저장 중 오류: $e');
        // 저장 실패해도 레시피 추천은 계속 진행
      }

      // 5. 레시피 추천 API 호출 (RAG 활성화)
      print('레시피 추천 API 호출 시작...');
      List<Map<String, dynamic>> recipesDynamic = [];
      bool ragRequestSucceeded = false;
      try {
        final recommendData = await apiService.post(
          '/fastapi/recommend?use_rag=true',
          {
            'ingredients': allIngredients,
            'main_ingredients': mainIngredients,
            'sub_ingredients': subIngredients,
          },
        );
        print('레시피 추천 API 응답 (RAG 활성화): \n$recommendData');
        if (recommendData is List) {
          recipesDynamic = recommendData.cast<Map<String, dynamic>>();
          ragRequestSucceeded = true;
          print('추천된 레시피 수 (RAG): ${recipesDynamic.length}');
        }
      } catch (e) {
        print('레시피 추천 실패 (RAG): $e');
      }

      if (!ragRequestSucceeded) {
        print('RAG 추천 실패 → 기본 추천(use_rag=false) 재시도');
        try {
          final fallbackData = await apiService.post(
            '/fastapi/recommend',
            {
              'ingredients': allIngredients,
              'main_ingredients': mainIngredients,
              'sub_ingredients': subIngredients,
            },
          );
          print('레시피 추천 API 응답 (기본 모드): \n$fallbackData');
          if (fallbackData is List) {
            recipesDynamic = fallbackData.cast<Map<String, dynamic>>();
            print('추천된 레시피 수 (기본 모드): ${recipesDynamic.length}');
          }
        } catch (e) {
          print('레시피 추천 실패 (기본 모드): $e');
        }
      }

      if (!mounted) return;

      Navigator.push(
        context,
        MaterialPageRoute(
          builder:
              (context) => RecipeResultScreen(
                ingredients: allIngredients,  // 전체 재료 (주재료 + 부재료)
                seasonings: seasonings,
                recipes: recipesDynamic,
              ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('이미지 분석 중 오류가 발생했습니다: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE8EB87),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE8EB87),
        elevation: 0,
        title: const Text('사진 촬영', style: TextStyle(color: Colors.black)),
        centerTitle: true,
        iconTheme: const IconThemeData(color: Colors.black),
      ),
      body: Stack(
        children: [
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              child: Column(
                children: [
                  const SizedBox(height: 24),
                  Container(
                    width: 260,
                    height: 260,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(32),
                      border: Border.all(color: Color(0xFF1EA7FF), width: 2),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black12,
                          blurRadius: 8,
                          offset: Offset(0, 4),
                        ),
                      ],
                    ),
                    child:
                        _image == null
                            ? const Center(
                              child: Text(
                                '사진을 촬영해 주세요.',
                                style: TextStyle(
                                  fontSize: 18,
                                  color: Colors.black54,
                                ),
                              ),
                            )
                            : ClipRRect(
                              borderRadius: BorderRadius.circular(30),
                              child: Image.file(
                                File(_image!.path),
                                width: 250,
                                height: 250,
                                fit: BoxFit.cover,
                              ),
                            ),
                  ),
                  const SizedBox(height: 32),
                  const Text(
                    '음식 사진을 촬영해 주세요!\n촬영된 사진은 미리보기로 확인할 수 있습니다.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 16, color: Colors.black87),
                  ),
                  const Spacer(),
                  Row(
                    children: [
                      Expanded(
                        child: SizedBox(
                          height: 60,
                          child: ElevatedButton.icon(
                            icon: const Icon(Icons.photo_library, size: 28),
                            label: const Text(
                              '갤러리',
                              style: TextStyle(fontSize: 20),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFFFDEDDC),
                              foregroundColor: Colors.black,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(30),
                              ),
                              elevation: 2,
                            ),
                            onPressed: _isLoading ? null : _pickFromGallery,
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: SizedBox(
                          height: 60,
                          child: ElevatedButton.icon(
                            icon: const Icon(Icons.camera_alt, size: 28),
                            label: const Text(
                              '촬영하기',
                              style: TextStyle(fontSize: 20),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF1EA7FF),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(30),
                              ),
                              elevation: 2,
                            ),
                            onPressed: _isLoading ? null : _takePicture,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                ],
              ),
            ),
          ),
          if (_isLoading)
            Container(
              color: Colors.black54,
              child: const Center(child: CircularProgressIndicator()),
            ),
        ],
      ),
    );
  }
}
