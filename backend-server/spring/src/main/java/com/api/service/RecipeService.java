package com.api.service;

import com.api.entity.Recipe;
import com.api.repository.RecipeRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class RecipeService {
    private final RecipeRepository recipeRepository;

    /**
     * 카테고리별 레시피 조회
     */
    public List<Map<String, Object>> getRecipesByCuisine(String cuisine) {
        // 카테고리 매핑 (프론트엔드 카테고리명 -> DB 카테고리명)
        Map<String, String> cuisineMapping = new HashMap<>();
        cuisineMapping.put("한식", "한식");
        cuisineMapping.put("중식", "중식");
        cuisineMapping.put("일식", "일식");
        cuisineMapping.put("양식", "양식");
        cuisineMapping.put("아시안", "동남아시아");
        cuisineMapping.put("동남아시아", "동남아시아");
        cuisineMapping.put("이탈리아", "이탈리아");
        cuisineMapping.put("퓨전", "퓨전");
        cuisineMapping.put("분식", "분식");

        String dbCuisine = cuisineMapping.getOrDefault(cuisine, cuisine);
        
        List<Recipe> recipes = recipeRepository.findByCuisineContaining(dbCuisine);

        return recipes.stream()
                .map(this::convertToRecipeMap)
                .collect(Collectors.toList());
    }

    /**
     * 키워드 기반 레시피 검색
     */
    public List<Map<String, Object>> searchRecipes(String keyword, int limit) {
        if (keyword == null || keyword.trim().isEmpty()) {
            return Collections.emptyList();
        }

        int resolvedLimit = limit > 0 ? limit : 50;
        List<Recipe> recipes = recipeRepository
                .findTop50ByTitleContainingIgnoreCaseOrSummaryContainingIgnoreCaseOrIngredientsContainingIgnoreCase(
                        keyword, keyword, keyword
                );

        return recipes.stream()
                .limit(resolvedLimit)
                .map(this::convertToRecipeMap)
                .collect(Collectors.toList());
    }

    /**
     * 레시피 상세 조회
     */
    public Map<String, Object> getRecipeById(Long recipeId) {
        Recipe recipe = recipeRepository.findById(recipeId)
                .orElseThrow(() -> new IllegalArgumentException("레시피를 찾을 수 없습니다."));
        return convertToRecipeMap(recipe);
    }

    private Map<String, Object> convertToRecipeMap(Recipe recipe) {
        Map<String, Object> recipeMap = new HashMap<>();
        recipeMap.put("id", recipe.getId());
        recipeMap.put("title", recipe.getTitle() != null ? recipe.getTitle() : "");
        recipeMap.put("ingredients", recipe.getIngredients() != null ? recipe.getIngredients() : "");
        recipeMap.put("mainIngredients", recipe.getMainIngredients() != null ? recipe.getMainIngredients() : "");
        recipeMap.put("subIngredients", recipe.getSubIngredients() != null ? recipe.getSubIngredients() : "");
        recipeMap.put("content", recipe.getContent() != null ? recipe.getContent() : "");
        recipeMap.put("summary", recipe.getSummary() != null ? recipe.getSummary() : "");
        recipeMap.put("servings", recipe.getServings() != null ? recipe.getServings() : "");
        recipeMap.put("cuisine", recipe.getCuisine() != null ? recipe.getCuisine() : "");
        return recipeMap;
    }
}

