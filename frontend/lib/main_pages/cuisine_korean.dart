import 'package:flutter/material.dart';
import 'widgets/recipe_category_screen.dart';

class CuisineKorean extends StatelessWidget {
  const CuisineKorean({super.key});

  @override
  Widget build(BuildContext context) {
    return const RecipeCategoryScreen(
      title: '한식',
      apiCategory: '한식',
      accentColor: Color(0xFFE8EB87),
      emoji: '🍚',
    );
  }
}
