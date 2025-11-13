import 'package:flutter/material.dart';
import 'widgets/recipe_category_screen.dart';

class CuisineFusion extends StatelessWidget {
  const CuisineFusion({super.key});

  @override
  Widget build(BuildContext context) {
    return const RecipeCategoryScreen(
      title: '퓨전',
      apiCategory: '퓨전',
      accentColor: Color(0xFFE6DAFF),
      emoji: '🌀',
    );
  }
}
