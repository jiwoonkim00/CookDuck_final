import 'package:flutter/material.dart';
import 'widgets/recipe_category_screen.dart';

class CuisineJapanese extends StatelessWidget {
  const CuisineJapanese({super.key});

  @override
  Widget build(BuildContext context) {
    return const RecipeCategoryScreen(
      title: '일식',
      apiCategory: '일식',
      accentColor: Color(0xFFFFF0C7),
      emoji: '🍣',
    );
  }
}
