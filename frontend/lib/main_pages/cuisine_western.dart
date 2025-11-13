import 'package:flutter/material.dart';
import 'widgets/recipe_category_screen.dart';

class CuisineWestern extends StatelessWidget {
  const CuisineWestern({super.key});

  @override
  Widget build(BuildContext context) {
    return const RecipeCategoryScreen(
      title: '양식',
      apiCategory: '양식',
      accentColor: Color(0xFFD6E5FA),
      emoji: '🍽️',
    );
  }
}
