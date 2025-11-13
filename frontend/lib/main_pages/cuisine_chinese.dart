import 'package:flutter/material.dart';
import 'widgets/recipe_category_screen.dart';

class CuisineChinese extends StatelessWidget {
  const CuisineChinese({super.key});

  @override
  Widget build(BuildContext context) {
    return const RecipeCategoryScreen(
      title: '중식',
      apiCategory: '중식',
      accentColor: Color(0xFFFFD7C2),
      emoji: '🥡',
    );
  }
}
