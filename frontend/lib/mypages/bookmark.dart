import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:cookduck/models/recipe.dart';
import 'package:cookduck/cooking/recipe_detail_screen.dart';
import 'package:cookduck/services/api_service.dart';

class _BookmarkItem {
  const _BookmarkItem({
    required this.bookmarkId,
    required this.recipeId,
    this.recipe,
    this.createdAt,
  });

  final String bookmarkId;
  final String recipeId;
  final Recipe? recipe;
  final DateTime? createdAt;
}

class Bookmark extends StatefulWidget {
  const Bookmark({super.key});

  @override
  State<Bookmark> createState() => _BookmarkState();
}

class _BookmarkState extends State<Bookmark> {
  final ApiService _apiService = ApiService();
  List<_BookmarkItem> _bookmarks = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadBookmarks();
  }

  Future<void> _loadBookmarks() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getString('user_id');
      
      if (userId == null) {
        setState(() {
          _loading = false;
        });
        return;
      }

      final data = await _apiService.get('/bookmarks/$userId');

      if (mounted) {
        final List<dynamic> bookmarksList = data is List ? data : [];
        setState(() {
          _bookmarks = bookmarksList
              .whereType<Map<String, dynamic>>()
              .map((item) {
                final recipeId = item['recipeId']?.toString() ?? '';
                Recipe? recipe;
                final recipeMap = item['recipe'];
                if (recipeMap is Map<String, dynamic> && recipeMap.isNotEmpty) {
                  recipe = Recipe.fromJson(Map<String, dynamic>.from(recipeMap));
                }
                DateTime? createdAt;
                final created = item['createdAt']?.toString();
                if (created != null) {
                  try {
                    createdAt = DateTime.parse(created);
                  } catch (_) {}
                }
                return _BookmarkItem(
                  bookmarkId: item['id']?.toString() ?? '',
                  recipeId: recipeId,
                  recipe: recipe,
                  createdAt: createdAt,
                );
              })
              .toList();
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  Future<void> _removeBookmark(String recipeId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getString('user_id');
      
      if (userId == null) return;

      await _apiService.delete('/bookmarks/$userId/$recipeId');

      if (mounted) {
        await _loadBookmarks();
      }
    } catch (e) {
      print('북마크 삭제 오류: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE8EB87),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE8EB87),
        title: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('북마크'),
            Image(image: const AssetImage('assets/logo.png'), width: 40),
          ],
        ),
        titleTextStyle: const TextStyle(
          fontSize: 22,
          fontWeight: FontWeight.w500,
          color: Colors.black,
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Container(
          width: double.infinity,
          // let height expand; use padding/margins for spacing
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.white.withAlpha(175),
            borderRadius: BorderRadius.circular(20),
          ),
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _bookmarks.isEmpty
                  ? const Center(child: Text('북마크된 항목이 없습니다.'))
                  : ListView.separated(
                      itemCount: _bookmarks.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        final item = _bookmarks[index];
                        final recipe = item.recipe;
                        final recipeId = item.recipeId;
                        final title = recipe?.title.isNotEmpty == true ? recipe!.title : '레시피 $recipeId';
                        final summary = recipe?.description ?? '';

                        return InkWell(
                          onTap: () => _openDetail(item),
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(15),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  height: 140,
                                  decoration: BoxDecoration(
                                    color: Colors.grey[300],
                                    borderRadius: const BorderRadius.only(
                                      topLeft: Radius.circular(15),
                                      topRight: Radius.circular(15),
                                    ),
                                  ),
                                  child: const Center(
                                    child: Icon(
                                      Icons.restaurant,
                                      size: 48,
                                      color: Colors.grey,
                                    ),
                                  ),
                                ),
                                Padding(
                                  padding: const EdgeInsets.all(12.0),
                                  child: Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              title,
                                              style: const TextStyle(
                                                fontSize: 16,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                            if (summary.isNotEmpty) ...[
                                              const SizedBox(height: 6),
                                              Text(
                                                summary,
                                                maxLines: 2,
                                                overflow: TextOverflow.ellipsis,
                                                style: const TextStyle(
                                                  fontSize: 13,
                                                  color: Colors.grey,
                                                ),
                                              ),
                                            ],
                                          ],
                                        ),
                                      ),
                                      IconButton(
                                        icon: const Icon(Icons.delete_outline),
                                        onPressed: recipeId.isEmpty ? null : () => _removeBookmark(recipeId),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
        ),
      ),
    );
  }

  Future<void> _openDetail(_BookmarkItem item) async {
    if (item.recipeId.isEmpty) return;

    Recipe? recipe = item.recipe;
    if (recipe == null || recipe.content.trim().isEmpty) {
      try {
        final data = await _apiService.get('/recipes/${item.recipeId}', includeAuth: false);
        if (data is Map<String, dynamic>) {
          recipe = Recipe.fromJson(data);
        }
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('레시피 정보를 불러오지 못했습니다.')),
        );
        return;
      }
    }

    if (!mounted || recipe == null) return;

    final changed = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => RecipeDetailScreen(
          recipe: recipe!,
          accentColor: const Color(0xFFE8EB87),
        ),
      ),
    );

    if (changed == true && mounted) {
      await _loadBookmarks();
    }
  }
}
