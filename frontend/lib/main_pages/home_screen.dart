import 'package:flutter/material.dart';
import 'package:cookduck/mypages/bookmark.dart';
import 'package:cookduck/mypages/cook_story.dart';
import 'package:cookduck/main_pages/cuisine_korean.dart';
import 'package:cookduck/main_pages/cuisine_chinese.dart';
import 'package:cookduck/main_pages/cuisine_japanese.dart';
import 'package:cookduck/main_pages/cuisine_western.dart';
import 'package:cookduck/main_pages/cuisine_asian.dart';
import 'package:cookduck/main_pages/cuisine_italian.dart';
import 'package:cookduck/main_pages/cuisine_fusion.dart';
import 'package:cookduck/cooking/search_screen.dart';
import 'package:cookduck/cooking/recipe_detail_screen.dart';
import 'package:cookduck/models/recipe.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:cookduck/services/api_service.dart';

class MyhomeScreen extends StatefulWidget {
  const MyhomeScreen({super.key});

  @override
  State<MyhomeScreen> createState() => _MyhomeScreenState();
}

class _MyhomeScreenState extends State<MyhomeScreen> {
  final PageController _recommendationPageController = PageController(viewportFraction: 0.9);

  String? userGrade;
  bool _isLoadingRecommendations = false;
  String? _recommendationError;
  List<Recipe> _recommendedRecipes = [];

  @override
  void initState() {
    super.initState();
    _loadUserGrade();
    _loadRecommendations();
  }

  Future<void> _loadUserGrade() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getString('user_id');
      if (userId == null || userId.isEmpty) {
        print('[홈] user_id 없음');
        return;
      }
      
      final apiService = ApiService();
      final data = await apiService.get('/user-grade/$userId');
      
      final grade = data['userGrade'] ?? '';
      setState(() {
        userGrade = grade;
      });
      print('[홈] 사용자 등급: $grade');
    } catch (e) {
      print('[홈] 등급 로드 오류: $e');
    }
  }

  Future<void> _loadRecommendations() async {
    setState(() {
      _isLoadingRecommendations = true;
      _recommendationError = null;
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getString('user_id');
      if (userId == null || userId.isEmpty) {
        setState(() {
          _recommendedRecipes = [];
          _recommendationError = '로그인 후 추천 레시피를 볼 수 있습니다.';
          _isLoadingRecommendations = false;
        });
        return;
      }

      final apiService = ApiService();

      // 재료 조회
      final ingredientData = await apiService.get('/user-ingredients/$userId');
      List<String> mainIngredients = [];
      List<String> subIngredients = [];
      List<String> allIngredients = [];
      if (ingredientData is Map<String, dynamic>) {
        if (ingredientData['main_ingredients'] is List) {
          mainIngredients = List<String>.from(ingredientData['main_ingredients']);
        }
        if (ingredientData['sub_ingredients'] is List) {
          subIngredients = List<String>.from(ingredientData['sub_ingredients']);
        }
        if (ingredientData['all_ingredients'] is List) {
          allIngredients = List<String>.from(ingredientData['all_ingredients']);
        }
      }
      if (allIngredients.isEmpty) {
        allIngredients = [...mainIngredients, ...subIngredients];
      }

      // 조미료 조회
      final seasoningData = await apiService.get('/user-seasonings/$userId');
      final List<String> seasonings = [];
      if (seasoningData is Map<String, dynamic>) {
        seasoningData.forEach((key, value) {
          if (value == true) {
            seasonings.add(key);
          }
        });
      }

      if (mainIngredients.isEmpty && subIngredients.isEmpty && seasonings.isEmpty) {
        setState(() {
          _recommendedRecipes = [];
          _recommendationError = '저장된 재료가 없습니다.\n사진 촬영으로 재료를 등록해보세요!';
          _isLoadingRecommendations = false;
        });
        return;
      }

      final combinedSub = {...subIngredients, ...seasonings}.toList();
      final combinedAll = {...allIngredients, ...seasonings}.toList();

      // Spring Boot 추천 API 호출
      List<Recipe> recommendations = [];
      
      try {
        final response = await apiService.post(
          '/recommend?use_rag=true',
          {
            'ingredients': combinedAll,
            'main_ingredients': mainIngredients,
            'sub_ingredients': combinedSub,
          },
        );

        if (response is List) {
          recommendations = response
              .whereType<Map<String, dynamic>>()
              .map((item) => Recipe.fromJson(item))
              .toList();
        }
      } catch (e) {
        print('[홈] 추천 실패: $e');
        // RAG 실패 시 기본 추천으로 재시도
        try {
          final fallbackResponse = await apiService.post(
            '/recommend?use_rag=false',
            {
              'ingredients': combinedAll,
              'main_ingredients': mainIngredients,
              'sub_ingredients': combinedSub,
            },
          );

          if (fallbackResponse is List) {
            recommendations = fallbackResponse
                .whereType<Map<String, dynamic>>()
                .map((item) => Recipe.fromJson(item))
                .toList();
          }
        } catch (e2) {
          print('[홈] 기본 추천 실패: $e2');
          throw e2; // 최종 실패 시 예외를 다시 던져서 catch 블록에서 처리
        }
      }

      setState(() {
        _recommendedRecipes = recommendations;
        _isLoadingRecommendations = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _recommendedRecipes = [];
        _recommendationError = '추천을 불러오는 중 오류가 발생했습니다.';
        _isLoadingRecommendations = false;
      });
      print('[홈] 추천 로드 오류: $e');
    }
  }

  void _onCategoryTapped(String category) {
    Widget page = const CuisineKorean();
    switch (category) {
      case '한식':
        page = const CuisineKorean();
        break;
      case '중식':
        page = const CuisineChinese();
        break;
      case '일식':
        page = const CuisineJapanese();
        break;
      case '양식':
        page = const CuisineWestern();
        break;
      case '동남아시아':
      case '아시안':
        page = const CuisineAsian();
        break;
      case '이탈리아':
        page = const CuisineItalian();
        break;
      case '퓨전':
        page = const CuisineFusion();
        break;
    }
    Navigator.push(context, MaterialPageRoute(builder: (_) => page));
  }

  Widget _buildCategoryItem(
    String label,
    String icon, [
    Color? backgroundColor,
  ]) {
    return InkWell(
      onTap: () => _onCategoryTapped(label),
      child: Column(
        children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: backgroundColor ?? Colors.grey[200],
              shape: BoxShape.circle,
            ),
            child: Center(
              child: Text(icon, style: const TextStyle(fontSize: 22)),
            ),
          ),
          const SizedBox(height: 8),
          Text(label),
        ],
      ),
    );
  }

  String _getGradeImage(String? grade) {
    final g = grade?.trim();
    switch (g) {
      case '초보':
      case 'newbie':
        return 'assets/newbie.png';
      case '중급':
      case 'intermediate':
        return 'assets/intermediate.png';
      case '고급':
      case 'high':
        return 'assets/high.png';
      case '마스터':
      case 'master':
        return 'assets/master.png';
      default:
        return ''; // 기본 이미지 없음, null 반환
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE8EB87),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 검색 바
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(
                      vertical: 12,
                      horizontal: 16,
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => const SearchScreen()),
                    );
                  },
                  child: Row(
                    children: const [
                      Icon(Icons.search, color: Colors.black, size: 26.0),
                      SizedBox(width: 12),
                      Text(
                        '검색',
                        style: TextStyle(fontSize: 17, color: Colors.black87),
                      ),
                    ],
                  ),
                ),
              ),

              // 카테고리 박스
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0),
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildCategoryItem(
                            '한식',
                            '🥘',
                            Colors.orange.shade200,
                          ),
                          _buildCategoryItem('중식', '🍜', Colors.red.shade200),
                          _buildCategoryItem(
                            '동남아시아',
                            '🌶️',
                            Colors.purple.shade100,
                          ),
                          _buildCategoryItem('양식', '🍝', Colors.green.shade200),
                        ],
                      ),
                      const SizedBox(height: 20),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildCategoryItem(
                            '이탈리아',
                            '🍕',
                            Colors.teal.shade100,
                          ),
                          _buildCategoryItem(
                            '퓨전',
                            '🍽️',
                            Colors.yellow.shade200,
                          ),
                          _buildCategoryItem('일식', '🍣', Colors.blue.shade100),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              // 프로필, CookStory, 북마크
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: () {},
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          height: 160,
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(15),
                          ),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              CircleAvatar(
                                radius: 32,
                                backgroundImage:
                                    userGrade != null &&
                                            _getGradeImage(userGrade).isNotEmpty
                                        ? AssetImage(_getGradeImage(userGrade))
                                        : null,
                                child:
                                    userGrade == null ||
                                            _getGradeImage(userGrade).isEmpty
                                        ? Icon(Icons.person, size: 32)
                                        : null,
                              ),
                              SizedBox(height: 16),
                              Text(
                                userGrade ?? '등급',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        children: [
                          _infoTile(Icons.book, 'MyDuck\nCookStory', () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => CookStory(),
                              ),
                            );
                          }),
                          const SizedBox(height: 16),
                          _infoTile(Icons.bookmark, '북마크', () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const Bookmark(),
                              ),
                            );
                          }),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              _buildRecommendationSection(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _infoTile(IconData icon, String label, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        height: 72,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(15),
        ),
        child: Row(
          children: [
            Icon(icon, size: 24),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecommendationSection() {
    Widget child;

    if (_isLoadingRecommendations) {
      child = const Center(child: CircularProgressIndicator());
    } else if (_recommendationError != null) {
      child = Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Text(
            _recommendationError!,
            style: const TextStyle(fontSize: 15, color: Colors.black54),
            textAlign: TextAlign.center,
          ),
        ),
      );
    } else if (_recommendedRecipes.isEmpty) {
      child = const Center(
        child: Padding(
          padding: EdgeInsets.all(24.0),
          child: Text(
            '추천할 레시피가 없습니다.\n사진 촬영으로 재료를 등록해보세요!',
            style: TextStyle(fontSize: 15, color: Colors.black54),
            textAlign: TextAlign.center,
          ),
        ),
      );
    } else {
      final recipes = _recommendedRecipes.take(5).toList();
      child = PageView.builder(
        controller: _recommendationPageController,
        itemCount: recipes.length,
        itemBuilder: (context, index) {
          final recipe = recipes[index];
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 4.0, vertical: 8),
            child: _RecommendationCard(
              recipe: recipe,
              onTap: () async {
                final changed = await Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => RecipeDetailScreen(recipe: recipe),
                  ),
                );
                if (changed == true) {
                  // 북마크 상태만 변경된 것이므로 추천을 다시 불러오지는 않음
                  // 필요 시 추후 확장
                }
              },
            ),
          );
        },
      );
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12),
      child: Container(
        height: 260,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
        ),
        child: child,
      ),
    );
  }

  @override
  void dispose() {
    _recommendationPageController.dispose();
    super.dispose();
  }
}

class _RecommendationCard extends StatelessWidget {
  const _RecommendationCard({
    required this.recipe,
    required this.onTap,
  });

  final Recipe recipe;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final visibleIngredients = recipe.ingredients.take(4).toList();

    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Colors.black12),
          color: Colors.white,
          boxShadow: const [
            BoxShadow(
              color: Colors.black12,
              blurRadius: 4,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFFF6F6F6),
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(18),
                    topRight: Radius.circular(18),
                  ),
                ),
                child: const Center(
                  child: Icon(
                    Icons.restaurant,
                    size: 48,
                    color: Colors.black38,
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    recipe.title,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    '재료 기반 추천 레시피',
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.black54,
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (visibleIngredients.isNotEmpty)
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: visibleIngredients
                          .map(
                            (ingredient) => Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                              decoration: BoxDecoration(
                                color: const Color(0xFFE8EB87).withOpacity(0.7),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                ingredient,
                                style: const TextStyle(fontSize: 12, color: Colors.black87),
                              ),
                            ),
                          )
                          .toList(),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
