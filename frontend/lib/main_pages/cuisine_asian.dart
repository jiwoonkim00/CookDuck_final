import 'package:flutter/material.dart';
import 'widgets/recipe_category_screen.dart';

class CuisineAsian extends StatelessWidget {
  const CuisineAsian({super.key});

  @override
  Widget build(BuildContext context) {
    return const RecipeCategoryScreen(
      title: '아시안',
      apiCategory: '동남아시아',
      accentColor: Color(0xFFFFE4B5),
      emoji: '🍜',
    );
  }
}
