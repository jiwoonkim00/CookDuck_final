import 'package:flutter/material.dart';
import 'widgets/recipe_category_screen.dart';

class CuisineSnack extends StatelessWidget {
  const CuisineSnack({super.key});

  @override
  Widget build(BuildContext context) {
    return const RecipeCategoryScreen(
      title: '분식',
      apiCategory: '분식',
      accentColor: Color(0xFFFFE4EC),
      emoji: '🍡',
    );
  }
}
