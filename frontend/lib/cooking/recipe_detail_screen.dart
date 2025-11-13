import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:cookduck/models/recipe.dart';
import 'package:cookduck/services/api_service.dart';
import 'package:cookduck/screens/chat_screen.dart';

class RecipeDetailScreen extends StatefulWidget {
  const RecipeDetailScreen({
    super.key,
    required this.recipe,
    this.accentColor = const Color(0xFFE8EB87),
  });

  final Recipe recipe;
  final Color accentColor;

  @override
  State<RecipeDetailScreen> createState() => _RecipeDetailScreenState();
}

class _RecipeDetailScreenState extends State<RecipeDetailScreen> {
  final ApiService _apiService = ApiService();
  bool _isBookmarked = false;
  bool _bookmarkLoading = false;
  bool _bookmarkChanged = false;
  String? _userId;

  @override
  void initState() {
    super.initState();
    _initBookmarkState();
  }

  Future<void> _initBookmarkState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final userId = prefs.getString('user_id');
      if (!mounted) return;

      setState(() {
        _userId = userId;
      });

      if (userId == null || userId.isEmpty) {
        return;
      }

      final response = await _apiService.get(
        '/bookmarks/$userId/${widget.recipe.id}',
        includeAuth: true,
      );

      if (mounted && response is Map<String, dynamic>) {
        final value = response['isBookmarked'];
        if (value is bool) {
          setState(() {
            _isBookmarked = value;
          });
        }
      }
    } catch (_) {
      // ignore errors silently for bookmark state
    }
  }

  void _showSnack(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Future<void> _toggleBookmark() async {
    if (_userId == null || _userId!.isEmpty) {
      _showSnack('로그인이 필요한 기능입니다.');
      return;
    }

    setState(() {
      _bookmarkLoading = true;
    });

    try {
      if (_isBookmarked) {
        await _apiService.delete('/bookmarks/${_userId!}/${widget.recipe.id}');
        if (mounted) {
          setState(() {
            _isBookmarked = false;
            _bookmarkChanged = true;
          });
        }
        _showSnack('북마크에서 제거했습니다.');
      } else {
        await _apiService.post('/bookmarks/${_userId!}', {
          'recipeId': widget.recipe.id,
        });
        if (mounted) {
          setState(() {
            _isBookmarked = true;
            _bookmarkChanged = true;
          });
        }
        _showSnack('북마크에 추가했습니다.');
      }
    } catch (e) {
      _showSnack('북마크 처리 중 오류가 발생했습니다.');
    } finally {
      if (mounted) {
        setState(() {
          _bookmarkLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final recipe = widget.recipe;
    final ingredients = recipe.ingredients;
    final steps = _parseInstructions(recipe.content);

    return WillPopScope(
      onWillPop: () async {
        Navigator.of(context).pop(_bookmarkChanged);
        return false;
      },
      child: Scaffold(
        backgroundColor: widget.accentColor,
        appBar: AppBar(
          backgroundColor: widget.accentColor,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back_ios_new, color: Colors.black87),
            onPressed: () => Navigator.of(context).pop(_bookmarkChanged),
          ),
          title: Text(
            recipe.title,
            style: const TextStyle(
              color: Colors.black,
              fontSize: 20,
              fontWeight: FontWeight.w600,
            ),
          ),
          centerTitle: true,
          actions: [
            IconButton(
              icon: _bookmarkLoading
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(
                      _isBookmarked ? Icons.bookmark : Icons.bookmark_border,
                      color: Colors.black87,
                    ),
              onPressed: _bookmarkLoading ? null : _toggleBookmark,
            ),
          ],
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.92),
                borderRadius: BorderRadius.circular(32),
              ),
              padding: const EdgeInsets.fromLTRB(24, 28, 24, 32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (recipe.description.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: Text(
                        recipe.description,
                        style: const TextStyle(
                          fontSize: 16,
                          height: 1.5,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                  if (recipe.servings != null && recipe.servings!.trim().isNotEmpty)
                    _InfoBadge(
                      label: '분량',
                      value: recipe.servings!.trim(),
                      icon: Icons.people_alt_outlined,
                    ),
                  if (recipe.cuisine != null && recipe.cuisine!.trim().isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: _InfoBadge(
                        label: '카테고리',
                        value: recipe.cuisine!.trim(),
                        icon: Icons.local_dining_outlined,
                      ),
                    ),
                  _SectionTitle(title: '필요 재료'),
                  if (ingredients.isNotEmpty)
                    ...ingredients.map(
                      (item) => Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: Text(
                          '• $item',
                          style: const TextStyle(
                            fontSize: 15,
                            height: 1.5,
                            color: Colors.black87,
                          ),
                        ),
                      ),
                    )
                  else
                    const Padding(
                      padding: EdgeInsets.only(bottom: 12),
                      child: Text(
                        '등록된 재료 정보가 없습니다.',
                        style: TextStyle(color: Colors.black54),
                      ),
                    ),
                  const SizedBox(height: 20),
                  _SectionTitle(title: '레시피'),
                  if (steps.isNotEmpty)
                    ...steps.map(
                      (step) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Text(
                          step,
                          style: const TextStyle(
                            fontSize: 15,
                            height: 1.6,
                            color: Colors.black87,
                          ),
                        ),
                      ),
                    )
                  else if (recipe.content.trim().isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: Text(
                        recipe.content,
                        style: const TextStyle(fontSize: 15, height: 1.6),
                      ),
                    )
                  else
                    const Padding(
                      padding: EdgeInsets.only(bottom: 16),
                      child: Text(
                        '상세 조리법이 아직 등록되지 않았습니다.',
                        style: TextStyle(color: Colors.black54),
                      ),
                    ),
                  const SizedBox(height: 24),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        elevation: 0,
                        backgroundColor: const Color(0xFFFFEBCE),
                        foregroundColor: Colors.black,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                          side: const BorderSide(color: Colors.black12),
                        ),
                      ),
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => ChatScreen(recipe: recipe),
                          ),
                        );
                      },
                      child: const Text(
                        '시작하기',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  List<String> _parseInstructions(String content) {
    if (content.trim().isEmpty) return [];
    final normalized = content.replaceAll('\r\n', '\n');
    final lines = normalized.split('\n').map((line) => line.trim()).where((line) => line.isNotEmpty).toList();
    if (lines.length == 1) {
      final matches = RegExp(r'(\d+\.\s*)').allMatches(lines.first);
      if (matches.length > 1) {
        final buffer = <String>[];
        final pattern = RegExp(r'(\d+\.\s*)');
        final segments = lines.first.split(pattern);
        String? currentNumber;
        for (final segment in segments) {
          if (segment.trim().isEmpty) continue;
          if (RegExp(r'^\d+\.').hasMatch(segment)) {
            currentNumber = segment.trim();
          } else if (currentNumber != null) {
            buffer.add('$currentNumber ${segment.trim()}');
            currentNumber = null;
          } else {
            buffer.add(segment.trim());
          }
        }
        if (buffer.isNotEmpty) {
          return buffer;
        }
      }
    }
    return lines;
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _InfoBadge extends StatelessWidget {
  const _InfoBadge({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 18, color: Colors.black54),
          const SizedBox(width: 6),
          Text(
            '$label: $value',
            style: const TextStyle(
              fontSize: 13,
              color: Colors.black87,
            ),
          ),
        ],
      ),
    );
  }
}

