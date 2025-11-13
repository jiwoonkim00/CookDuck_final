class Recipe {
  final String id;
  final String title;
  final String description;
  final String content;
  final List<String> ingredients;
  final List<String> steps;
  final String imageUrl;
  final String? mainIngredients; // 주재료 (쉼표로 구분된 문자열)
  final String? subIngredients; // 부재료 (쉼표로 구분된 문자열)
  final List<String>? matchedMainIngredients; // 매칭된 주재료
  final List<String>? matchedSubIngredients; // 매칭된 부재료
  final double? score; // 추천 점수
  final String? servings;
  final String? cuisine;

  Recipe({
    required this.id,
    required this.title,
    required this.description,
    required this.content,
    required this.ingredients,
    required this.steps,
    required this.imageUrl,
    this.mainIngredients,
    this.subIngredients,
    this.matchedMainIngredients,
    this.matchedSubIngredients,
    this.score,
    this.servings,
    this.cuisine,
  });

  factory Recipe.fromJson(Map<String, dynamic> json) {
    return Recipe(
      id: json['id']?.toString() ?? '',
      title: json['title'] ?? '',
      description: json['summary'] ?? json['content'] ?? json['description'] ?? '',
      content: json['content']?.toString() ?? '',
      ingredients: _parseStringList(json['ingredients']),
      steps: _parseStringList(json['steps']),
      imageUrl: json['imageUrl'] ?? '',
      mainIngredients: json['mainIngredients'] ?? json['main_ingredients'],
      subIngredients: json['subIngredients'] ?? json['sub_ingredients'],
      matchedMainIngredients: _parseNullableStringList(json['matched_main_ingredients']),
      matchedSubIngredients: _parseNullableStringList(json['matched_sub_ingredients']),
      score: json['score'] != null ? double.tryParse(json['score'].toString()) : null,
      servings: json['servings']?.toString(),
      cuisine: json['cuisine']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'content': content,
      'ingredients': ingredients,
      'steps': steps,
      'imageUrl': imageUrl,
      'main_ingredients': mainIngredients,
      'sub_ingredients': subIngredients,
      'matched_main_ingredients': matchedMainIngredients,
      'matched_sub_ingredients': matchedSubIngredients,
      'score': score,
      'servings': servings,
      'cuisine': cuisine,
    };
  }

  static List<String> _parseStringList(dynamic value) {
    if (value == null) return [];
    if (value is String) {
      return value
          .split(',')
          .map((e) => e.trim())
          .where((element) => element.isNotEmpty)
          .toList();
    }
    if (value is Iterable) {
      return value.map((e) => e?.toString() ?? '').where((e) => e.isNotEmpty).toList();
    }
    return [];
  }

  static List<String>? _parseNullableStringList(dynamic value) {
    final list = _parseStringList(value);
    return list.isEmpty ? null : list;
  }
}
