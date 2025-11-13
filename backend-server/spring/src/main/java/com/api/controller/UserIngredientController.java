package com.api.controller;

import com.api.service.UserIngredientService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/user-ingredients")
@RequiredArgsConstructor
public class UserIngredientController {
    private final UserIngredientService userIngredientService;

    /**
     * 사용자 재료 저장 (기존 재료에 추가, 중복 제거)
     * POST /api/user-ingredients/{userId}
     * Body: {
     *   "main_ingredients": ["재료1", "재료2"],
     *   "sub_ingredients": ["재료3", "재료4"],
     *   "replace": false  // true면 기존 재료 삭제 후 새로 저장, false면 추가 (기본값: false)
     * }
     */
    @PostMapping("/{userId}")
    public ResponseEntity<?> saveUserIngredients(
            @PathVariable String userId,
            @RequestBody Map<String, Object> request) {
        try {
            @SuppressWarnings("unchecked")
            List<String> mainIngredients = (List<String>) request.get("main_ingredients");
            @SuppressWarnings("unchecked")
            List<String> subIngredients = (List<String>) request.get("sub_ingredients");
            Boolean replace = (Boolean) request.getOrDefault("replace", false);
            
            if (mainIngredients == null) mainIngredients = List.of();
            if (subIngredients == null) subIngredients = List.of();
            
            if (Boolean.TRUE.equals(replace)) {
                // 기존 재료 삭제 후 새로 저장
                userIngredientService.replaceUserIngredients(userId, mainIngredients, subIngredients);
                return ResponseEntity.ok(Map.of(
                        "success", true,
                        "message", "재료가 교체되었습니다.",
                        "main_count", mainIngredients.size(),
                        "sub_count", subIngredients.size()
                ));
            } else {
                // 기존 재료에 추가 (중복 제거)
                userIngredientService.saveUserIngredients(userId, mainIngredients, subIngredients);
                return ResponseEntity.ok(Map.of(
                        "success", true,
                        "message", "재료가 추가되었습니다. (중복 제거됨)",
                        "main_count", mainIngredients.size(),
                        "sub_count", subIngredients.size()
                ));
            }
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "message", "재료 저장 중 오류가 발생했습니다: " + e.getMessage()
            ));
        }
    }

    /**
     * 사용자 재료 조회
     * GET /api/user-ingredients/{userId}
     */
    @GetMapping("/{userId}")
    public ResponseEntity<?> getUserIngredients(@PathVariable String userId) {
        try {
            Map<String, List<String>> ingredients = userIngredientService.getUserIngredients(userId);
            return ResponseEntity.ok(ingredients);
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "message", "재료 조회 중 오류가 발생했습니다: " + e.getMessage()
            ));
        }
    }

    /**
     * 사용자 재료 삭제
     * DELETE /api/user-ingredients/{userId}
     */
    @DeleteMapping("/{userId}")
    public ResponseEntity<?> deleteUserIngredients(@PathVariable String userId) {
        try {
            userIngredientService.deleteUserIngredients(userId);
            return ResponseEntity.ok(Map.of(
                    "success", true,
                    "message", "재료가 삭제되었습니다."
            ));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "message", "재료 삭제 중 오류가 발생했습니다: " + e.getMessage()
            ));
        }
    }
}

