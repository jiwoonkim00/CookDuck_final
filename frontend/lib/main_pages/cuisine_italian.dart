import 'package:flutter/material.dart';
import 'widgets/recipe_category_screen.dart';

class CuisineItalian extends StatelessWidget {
  const CuisineItalian({super.key});

  @override
  Widget build(BuildContext context) {
    return const RecipeCategoryScreen(
      title: '이탈리아',
      apiCategory: '이탈리아',
      accentColor: Color(0xFFD9F0B1),
      emoji: '🍝',
    );
  }
}
