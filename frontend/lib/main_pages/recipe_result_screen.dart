import 'package:flutter/material.dart';
import 'package:cookduck/models/recipe.dart';
import 'package:cookduck/cooking/recipe_detail_screen.dart';

class RecipeResultScreen extends StatelessWidget {
  final List<String> seasonings;
  final List<String> ingredients;
  final List<Map<String, dynamic>> recipes;

  const RecipeResultScreen({
    super.key,
    required this.seasonings,
    required this.ingredients,
    required this.recipes,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE8EB87),
      body: SafeArea(
        child: Center(
          child: Container(
            width: 340,
            height: 900,
            margin: const EdgeInsets.symmetric(vertical: 16),
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 12),
            decoration: BoxDecoration(
              color: const Color(0xFFF9F9E3),
              borderRadius: BorderRadius.circular(32),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.black26),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '보유 조미료: ${seasonings.join(', ')}',
                        style: const TextStyle(
                          fontSize: 16,
                          color: Colors.blueGrey,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        '보유 식재료: ${ingredients.join(', ')}',
                        style: const TextStyle(fontSize: 16),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                Expanded(
                  child: ListView.separated(
                    itemCount: recipes.length,
                    separatorBuilder:
                        (context, idx) => const SizedBox(height: 18),
                    itemBuilder: (context, idx) {
                      final recipe = recipes[idx];
                      final title = recipe['title'] ?? '';
                      final content = recipe['content'] ?? recipe['desc'] ?? '';
                      final mainIngredients = recipe['main_ingredients'] ?? '';
                      final subIngredients = recipe['sub_ingredients'] ?? '';
                      final matchedMain = (recipe['matched_main_ingredients'] as List?)
                              ?.cast<String>() ??
                          const <String>[];
                      final matchedSub = (recipe['matched_sub_ingredients'] as List?)
                              ?.cast<String>() ??
                          const <String>[];
                      
                      final recipeModel = Recipe.fromJson(recipe);

                      return InkWell(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => RecipeDetailScreen(
                                recipe: recipeModel,
                                accentColor: const Color(0xFFE8EB87),
                              ),
                            ),
                          );
                        },
                        child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.black38),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                              title,
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w500,
                              ),
                                    ),
                                  ),
                                  const Icon(
                                    Icons.chevron_right,
                                    color: Colors.black38,
                                  ),
                                ],
                            ),
                            if (mainIngredients.isNotEmpty || subIngredients.isNotEmpty) ...[
                              const SizedBox(height: 6),
                              if (mainIngredients.isNotEmpty)
                                Text(
                                  '주재료: $mainIngredients',
                                  style: const TextStyle(
                                    fontSize: 13,
                                    color: Color(0xFF1EA7FF),
                                  ),
                                ),
                              if (subIngredients.isNotEmpty)
                                Text(
                                  '부재료: $subIngredients',
                                  style: const TextStyle(
                                    fontSize: 13,
                                    color: Colors.orange,
                                  ),
                                ),
                            ],
                              if (matchedMain.isNotEmpty) ...[
                                const SizedBox(height: 4),
                                Text(
                                  '매칭 주재료: ${matchedMain.join(', ')}',
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: Colors.green,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ],
                              if (matchedSub.isNotEmpty) ...[
                              const SizedBox(height: 4),
                              Text(
                                  '매칭 부재료: ${matchedSub.join(', ')}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Colors.green,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                            const SizedBox(height: 4),
                            Text(
                              content.length > 100 ? '${content.substring(0, 100)}...' : content,
                              style: const TextStyle(fontSize: 14),
                              maxLines: 3,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
