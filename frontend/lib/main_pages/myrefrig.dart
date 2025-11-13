import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:cookduck/services/api_service.dart';

class Myrefrig extends StatefulWidget {
  const Myrefrig({super.key});

  @override
  State<Myrefrig> createState() => _MyrefrigState();
}

class _MyrefrigState extends State<Myrefrig> {
  List<String> seasonings = [];
  List<String> mainIngredients = [];
  List<String> subIngredients = [];
  List<String> allIngredients = [];
  bool isLoading = true;
  String? errorMsg;

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getString('user_id');
      print('[냉장고] SharedPreferences user_id: ${userId ?? 'null'}');
      if (userId == null || userId.isEmpty) {
        setState(() {
          errorMsg = '로그인 정보가 없습니다.';
          isLoading = false;
        });
        print('[냉장고] user_id 없음, 로그인 필요');
        return;
      }
      
      // 조미료와 재료를 동시에 불러오기
      await Future.wait([
        _fetchSeasonings(userId),
        _fetchIngredients(userId),
      ]);
      
      setState(() {
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        errorMsg = '데이터를 불러오는 중 오류가 발생했습니다: $e';
        isLoading = false;
      });
      print('[냉장고] 오류: $e');
    }
  }

  Future<void> _fetchSeasonings(String userId) async {
    try {
      final apiService = ApiService();
      final data = await apiService.get('/user-seasonings/$userId');
      print('[냉장고] 조미료 파싱된 데이터: $data');
      final List<String> result = [];
      if (data is Map<String, dynamic>) {
        data.forEach((key, value) {
          if (value == true) {
            result.add(key);
          }
        });
      }
      setState(() {
        seasonings = result;
      });
    } catch (e) {
      print('[냉장고] 조미료 조회 오류: $e');
    }
  }

  Future<void> _fetchIngredients(String userId) async {
    try {
      final apiService = ApiService();
      final data = await apiService.get('/user-ingredients/$userId');
      print('[냉장고] 재료 파싱된 데이터: $data');
      
      List<String> main = [];
      List<String> sub = [];
      List<String> all = [];
      
      if (data is Map<String, dynamic>) {
        if (data['main_ingredients'] is List) {
          main = List<String>.from(data['main_ingredients']);
        }
        if (data['sub_ingredients'] is List) {
          sub = List<String>.from(data['sub_ingredients']);
        }
        if (data['all_ingredients'] is List) {
          all = List<String>.from(data['all_ingredients']);
        }
      }
      
      setState(() {
        mainIngredients = main;
        subIngredients = sub;
        allIngredients = all.isNotEmpty ? all : [...main, ...sub];
      });
    } catch (e) {
      print('[냉장고] 재료 조회 오류: $e');
      setState(() {
        mainIngredients = [];
        subIngredients = [];
        allIngredients = [];
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Color(0xFFE8EB87),
      appBar: AppBar(
        backgroundColor: Color(0xFFE8EB87),
        title: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('냉장고'),
            Image(image: AssetImage('assets/logo.png'), width: 40),
          ],
        ),
        titleTextStyle: TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w500,
          color: Colors.black,
        ),
      ),
      body: Container(
        width: 340,
        height: 500,
        margin: EdgeInsets.all(40),
        padding: EdgeInsets.all(5),
        decoration: BoxDecoration(
          color: Colors.white.withAlpha(175),
          borderRadius: BorderRadius.circular(35),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 20),
            const Text(
              '조미료',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.black12),
              ),
              child:
                  isLoading
                      ? const Text('불러오는 중...')
                      : errorMsg != null
                      ? Text(
                        errorMsg!,
                        style: const TextStyle(color: Colors.red),
                      )
                      : Text(
                        seasonings.isNotEmpty
                            ? seasonings.join(', ')
                            : '조미료 정보 없음',
                      ),
            ),
            const SizedBox(height: 24),
            const Text(
              '식재료',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.black12),
              ),
              child: isLoading
                  ? const Text('불러오는 중...')
                  : errorMsg != null
                      ? Text(
                          errorMsg!,
                          style: const TextStyle(color: Colors.red),
                        )
                      : allIngredients.isNotEmpty
                          ? Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                if (mainIngredients.isNotEmpty) ...[
                                  const Text(
                                    '주재료:',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 14,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    mainIngredients.join(', '),
                                    style: const TextStyle(fontSize: 14),
                                  ),
                                  if (subIngredients.isNotEmpty)
                                    const SizedBox(height: 8),
                                ],
                                if (subIngredients.isNotEmpty) ...[
                                  const Text(
                                    '부재료:',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 14,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    subIngredients.join(', '),
                                    style: const TextStyle(fontSize: 14),
                                  ),
                                ],
                              ],
                            )
                          : const Text(
                              '저장된 식재료가 없습니다.\n사진을 촬영하여 재료를 인식해보세요!',
                              style: TextStyle(color: Colors.grey),
                            ),
            ),
          ],
        ),
      ),
    );
  }
}
