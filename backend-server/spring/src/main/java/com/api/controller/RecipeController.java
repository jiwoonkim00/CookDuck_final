package com.api.controller;

import com.api.service.FastApiService;
import com.api.service.RecipeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class RecipeController {
    
    @Autowired
    private FastApiService fastApiService;
    
    @Autowired
    private RecipeService recipeService;
    
    /**
     * FAISS 기반 레시피 추천
     */
    @PostMapping("/recommend")
    public ResponseEntity<?> recommendRecipes(
            @RequestBody Map<String, Object> request,
            @RequestParam(value = "use_rag", defaultValue = "true") boolean useRag) {
        @SuppressWarnings("unchecked")
        List<String> ingredients = (List<String>) request.get("ingredients");
        
        if (ingredients == null || ingredients.isEmpty()) {
            return ResponseEntity.badRequest().body(
                Map.of("error", "재료 목록이 비어있습니다.")
            );
        }
        
        // 주재료/부재료 정보 추출 (옵션)
        @SuppressWarnings("unchecked")
        List<String> mainIngredients = (List<String>) request.get("main_ingredients");
        @SuppressWarnings("unchecked")
        List<String> subIngredients = (List<String>) request.get("sub_ingredients");
        
        return fastApiService.getRecommendations(ingredients, mainIngredients, subIngredients, useRag);
    }
    
    /**
     * 시스템 상태 확인
     */
    @GetMapping("/system/status")
    public ResponseEntity<?> getSystemStatus() {
        return fastApiService.getSystemStatus();
    }
    
    /**
     * 성능 측정
     */
    @PostMapping("/recommend/performance")
    public ResponseEntity<?> measurePerformance(@RequestBody Map<String, Object> request) {
        @SuppressWarnings("unchecked")
        List<String> ingredients = (List<String>) request.get("ingredients");
        
        if (ingredients == null || ingredients.isEmpty()) {
            return ResponseEntity.badRequest().body(
                Map.of("error", "재료 목록이 비어있습니다.")
            );
        }
        
        return fastApiService.measurePerformance(ingredients);
    }
    
    /**
     * WebSocket URL 반환
     */
    @GetMapping("/chat/ws")
    public ResponseEntity<?> getChatWebSocket() {
        return fastApiService.getWebSocketUrl();
    }
    
    /**
     * 헬스 체크
     */
    @GetMapping("/health")
    public ResponseEntity<?> healthCheck() {
        return ResponseEntity.ok(Map.of(
            "status", "UP",
            "service", "Spring Boot + FastAPI Integration",
            "timestamp", System.currentTimeMillis()
        ));
    }
    
    /**
     * 카테고리별 레시피 조회
     */
    @GetMapping("/recipes/cuisine/{cuisine}")
    public ResponseEntity<?> getRecipesByCuisine(@PathVariable String cuisine) {
        try {
            List<Map<String, Object>> recipes = recipeService.getRecipesByCuisine(cuisine);
            return ResponseEntity.ok(recipes);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of(
                "error", "레시피 조회 실패: " + e.getMessage()
            ));
        }
    }

    /**
     * 키워드 검색
     */
    @GetMapping("/recipes/search")
    public ResponseEntity<?> searchRecipes(
            @RequestParam("keyword") String keyword,
            @RequestParam(value = "limit", defaultValue = "50") int limit
    ) {
        try {
            List<Map<String, Object>> recipes = recipeService.searchRecipes(keyword, limit);
            return ResponseEntity.ok(recipes);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of(
                    "error", "레시피 검색 실패: " + e.getMessage()
            ));
        }
    }

    /**
     * 레시피 상세 조회
     */
    @GetMapping("/recipes/{recipeId}")
    public ResponseEntity<?> getRecipeDetail(@PathVariable Long recipeId) {
        try {
            return ResponseEntity.ok(recipeService.getRecipeById(recipeId));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of(
                    "error", "레시피 조회 실패: " + e.getMessage()
            ));
        }
    }
}
