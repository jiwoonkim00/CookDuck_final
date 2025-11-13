import 'package:flutter/material.dart';
import 'package:cookduck/services/api_service.dart';
import 'package:cookduck/models/recipe.dart';
import 'package:cookduck/cooking/recipe_detail_screen.dart';

class RecipeCategoryScreen extends StatefulWidget {
  const RecipeCategoryScreen({
    super.key,
    required this.title,
    required this.apiCategory,
    this.accentColor = const Color(0xFFE8EB87),
    this.emoji,
  });

  final String title;
  final String apiCategory;
  final Color accentColor;
  final String? emoji;

  @override
  State<RecipeCategoryScreen> createState() => _RecipeCategoryScreenState();
}

class _RecipeCategoryScreenState extends State<RecipeCategoryScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _searchController = TextEditingController();

  List<Map<String, dynamic>> _recipes = [];
  bool _isLoading = true;
  String? _errorMessage;
  String _keyword = '';

  @override
  void initState() {
    super.initState();
    _loadRecipes();
    _searchController.addListener(() {
      final nextKeyword = _searchController.text.trim();
      if (nextKeyword != _keyword) {
        setState(() {
          _keyword = nextKeyword;
        });
      }
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadRecipes() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final data = await _apiService.get(
        '/recipes/cuisine/${widget.apiCategory}',
        includeAuth: false,
      );

      if (!mounted) return;

      if (data is List) {
        setState(() {
          _recipes = data.cast<Map<String, dynamic>>();
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = '레시피를 불러올 수 없습니다.';
          _isLoading = false;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = '오류가 발생했습니다: ${e.toString()}';
        _isLoading = false;
      });
    }
  }

  List<Map<String, dynamic>> get _filteredRecipes {
    if (_keyword.isEmpty) {
      return _recipes;
    }

    final lowerKeyword = _keyword.toLowerCase();
    return _recipes.where((recipe) {
      final title = recipe['title']?.toString().toLowerCase() ?? '';
      final summary = recipe['summary']?.toString().toLowerCase() ?? '';
      final ingredients = recipe['ingredients']?.toString().toLowerCase() ?? '';
      return title.contains(lowerKeyword) ||
          summary.contains(lowerKeyword) ||
          ingredients.contains(lowerKeyword);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
        titleSpacing: 0,
        title: Row(
          children: [
            Text(
              widget.title,
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w700,
                color: Colors.black87,
              ),
            ),
            if (widget.emoji != null) ...[
              const SizedBox(width: 8),
              Text(widget.emoji!, style: const TextStyle(fontSize: 22)),
            ],
          ],
        ),
        centerTitle: false,
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              widget.accentColor.withOpacity(0.4),
              Colors.white,
            ],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
                child: _buildSearchField(),
              ),
              Expanded(
                child: RefreshIndicator(
                  onRefresh: _loadRecipes,
                  child: _buildRecipeList(),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSearchField() {
    return TextField(
      controller: _searchController,
      decoration: InputDecoration(
        prefixIcon: const Icon(Icons.search),
        hintText: '${widget.title} 레시피 검색',
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide(color: Colors.black.withOpacity(0.05)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide(color: Colors.black.withOpacity(0.05)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide(color: widget.accentColor, width: 1.6),
        ),
      ),
    );
  }

  Widget _buildRecipeList() {
    if (_isLoading) {
      return ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        children: const [
          SizedBox(height: 160),
          Center(child: CircularProgressIndicator()),
          SizedBox(height: 160),
        ],
      );
    }

    if (_errorMessage != null) {
      return ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 80),
        children: [
          Icon(Icons.error_outline, size: 48, color: Colors.redAccent.withOpacity(0.9)),
          const SizedBox(height: 12),
          Text(
            _errorMessage!,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 15),
          ),
          const SizedBox(height: 20),
          ElevatedButton.icon(
            onPressed: _loadRecipes,
            icon: const Icon(Icons.refresh),
            label: const Text('다시 불러오기'),
            style: ElevatedButton.styleFrom(
              elevation: 0,
              backgroundColor: widget.accentColor,
              foregroundColor: Colors.black87,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),
        ],
      );
    }

    final filtered = _filteredRecipes;
    if (filtered.isEmpty) {
      return ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 120),
        children: [
          Icon(
            Icons.search_off,
            size: 48,
            color: Colors.black.withOpacity(0.3),
          ),
          const SizedBox(height: 12),
          Text(
            '검색 조건에 맞는 레시피가 없어요.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 15,
              color: Colors.black.withOpacity(0.6),
            ),
          ),
        ],
      );
    }

    return ListView.builder(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
      itemCount: filtered.length,
      itemBuilder: (context, index) {
        final recipeJson = filtered[index];
        final recipe = Recipe.fromJson(recipeJson);
        return _RecipeListTile(
          accentColor: widget.accentColor,
          recipe: recipe,
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => RecipeDetailScreen(
                  recipe: recipe,
                  accentColor: widget.accentColor,
                ),
              ),
            );
          },
        );
      },
    );
  }
}

class _RecipeListTile extends StatelessWidget {
  const _RecipeListTile({
    required this.recipe,
    required this.accentColor,
    this.onTap,
  });

  final Recipe recipe;
  final Color accentColor;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final servings = recipe.servings ?? '';
    final displayTitle = servings.isNotEmpty ? '${recipe.title} ($servings)' : recipe.title;
    final summary = recipe.description;

    return Card(
      elevation: 2,
      margin: const EdgeInsets.symmetric(vertical: 10),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                displayTitle,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                ),
              ),
              if (summary.isNotEmpty) ...[
                const SizedBox(height: 10),
                Text(
                  summary,
                  style: TextStyle(
                    fontSize: 14,
                    height: 1.5,
                    color: Colors.black.withOpacity(0.65),
                  ),
                ),
              ],
              const SizedBox(height: 14),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Text(
                    '자세히 보기',
                    style: TextStyle(
                      fontSize: 13,
                      color: accentColor.darken(0.25),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Icon(
                    Icons.chevron_right,
                    color: accentColor.darken(0.25),
                    size: 20,
                  ),
                ],
              )
            ],
          ),
        ),
      ),
    );
  }
}

extension on Color {
  Color darken([double amount = .1]) {
    assert(amount >= 0 && amount <= 1);
    final hsl = HSLColor.fromColor(this);
    final hslDark = hsl.withLightness((hsl.lightness - amount).clamp(0.0, 1.0));
    return hslDark.toColor();
  }
}

