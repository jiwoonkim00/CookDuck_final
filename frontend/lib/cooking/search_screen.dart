import 'dart:async';

import 'package:flutter/material.dart';
import 'package:cookduck/models/recipe.dart';
import 'package:cookduck/services/api_service.dart';
import 'package:cookduck/cooking/recipe_detail_screen.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _controller = TextEditingController();
  final ApiService _apiService = ApiService();

  List<Recipe> _searchResults = [];
  bool _isLoading = false;
  String? _errorMessage;
  String _currentQuery = '';
  Timer? _debounce;

  static const _debounceDuration = Duration(milliseconds: 350);

  @override
  void dispose() {
    _debounce?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    _debounce?.cancel();
    _debounce = Timer(_debounceDuration, () {
      _performSearch(query.trim());
    });
    setState(() {
      _currentQuery = query;
    });
  }

  Future<void> _performSearch(String query) async {
    if (!mounted) return;
    if (query.isEmpty) {
      setState(() {
        _searchResults = [];
        _errorMessage = null;
        _isLoading = false;
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await _apiService.get(
        '/recipes/search',
        includeAuth: false,
        queryParameters: {
          'keyword': query,
          'limit': '50',
        },
      );

      if (!mounted) return;

      if (response is List) {
        final recipes = response
            .whereType<Map<String, dynamic>>()
            .map((item) => Recipe.fromJson(item))
            .toList();
        setState(() {
          _searchResults = recipes;
          _isLoading = false;
        });
      } else {
        setState(() {
          _errorMessage = '검색 결과를 불러오지 못했습니다.';
          _isLoading = false;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = '검색 중 오류가 발생했습니다: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE8EB87),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE8EB87),
        title: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(
            color: Colors.white.withAlpha(175),
            borderRadius: BorderRadius.circular(25),
          ),
          child: Row(
            children: [
              const Icon(Icons.search, color: Colors.black),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: _controller,
                  decoration: const InputDecoration(
                    hintText: '레시피를 검색해 보세요',
                    border: InputBorder.none,
                  ),
                  onChanged: _onSearchChanged,
                  textInputAction: TextInputAction.search,
                ),
              ),
              IconButton(
                icon: const Icon(Icons.clear, color: Colors.black),
                onPressed: () {
                  _controller.clear();
                  _onSearchChanged('');
                },
              ),
            ],
          ),
        ),
      ),
      body: Container(
        width: 340,
        margin: const EdgeInsets.all(40),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
        decoration: BoxDecoration(
          color: Colors.white.withAlpha(175),
          borderRadius: BorderRadius.circular(35),
        ),
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_errorMessage != null) {
      return Center(
        child: Text(
          _errorMessage!,
          textAlign: TextAlign.center,
          style: const TextStyle(color: Colors.redAccent),
        ),
      );
    }

    if (_currentQuery.trim().isEmpty) {
      return const Center(
        child: Text(
          '검색어를 입력하면 레시피 DB에서 찾아드릴게요.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 16),
        ),
      );
    }

    if (_searchResults.isEmpty) {
      return const Center(
        child: Text(
          '검색 결과가 없습니다.',
          style: TextStyle(fontSize: 16),
        ),
      );
    }

    return ListView.separated(
      itemCount: _searchResults.length,
      separatorBuilder: (_, __) => const Divider(height: 1, color: Colors.black12),
      itemBuilder: (context, index) {
        final recipe = _searchResults[index];
        final summary = recipe.description.isNotEmpty
            ? recipe.description
            : (recipe.ingredients.isNotEmpty ? recipe.ingredients.join(', ') : '상세 설명이 없습니다.');

        return ListTile(
          leading: recipe.imageUrl.isNotEmpty
              ? Image.network(
                  recipe.imageUrl,
                  width: 52,
                  height: 52,
                  fit: BoxFit.cover,
                )
              : Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.orange.shade100,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.restaurant, color: Colors.black54),
                ),
          title: Text(recipe.title),
          subtitle: Text(
            summary,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => RecipeDetailScreen(
                  recipe: recipe,
                ),
              ),
            );
          },
        );
      },
    );
  }
}
