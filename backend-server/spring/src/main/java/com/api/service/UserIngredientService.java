package com.api.service;

import com.api.entity.UserIngredient;
import com.api.repository.UserIngredientRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class UserIngredientService {
    private final UserIngredientRepository userIngredientRepository;

    /**
     * 사용자 재료 저장 (기존 재료에 추가, 중복 제거)
     */
    @Transactional
    public void saveUserIngredients(String userId, List<String> mainIngredients, List<String> subIngredients) {
        // 기존 재료 조회
        List<UserIngredient> existingIngredients = userIngredientRepository.findByUserId(userId);
        Set<String> existingMainSet = existingIngredients.stream()
                .filter(ing -> "main".equals(ing.getIngredientType()))
                .map(ing -> ing.getIngredient().toLowerCase().trim())
                .collect(Collectors.toSet());
        Set<String> existingSubSet = existingIngredients.stream()
                .filter(ing -> "sub".equals(ing.getIngredientType()))
                .map(ing -> ing.getIngredient().toLowerCase().trim())
                .collect(Collectors.toSet());
        
        // 주재료 저장 (중복 체크)
        for (String ingredient : mainIngredients) {
            if (ingredient != null && !ingredient.trim().isEmpty()) {
                String trimmedIngredient = ingredient.trim();
                String lowerIngredient = trimmedIngredient.toLowerCase();
                
                // 중복 체크 (대소문자 무시)
                if (!existingMainSet.contains(lowerIngredient)) {
                    UserIngredient userIngredient = new UserIngredient();
                    userIngredient.setUserId(userId);
                    userIngredient.setIngredient(trimmedIngredient);
                    userIngredient.setIngredientType("main");
                    userIngredientRepository.save(userIngredient);
                    existingMainSet.add(lowerIngredient); // 메모리에도 추가하여 중복 방지
                }
            }
        }
        
        // 부재료 저장 (중복 체크)
        for (String ingredient : subIngredients) {
            if (ingredient != null && !ingredient.trim().isEmpty()) {
                String trimmedIngredient = ingredient.trim();
                String lowerIngredient = trimmedIngredient.toLowerCase();
                
                // 중복 체크 (대소문자 무시)
                if (!existingSubSet.contains(lowerIngredient)) {
                    UserIngredient userIngredient = new UserIngredient();
                    userIngredient.setUserId(userId);
                    userIngredient.setIngredient(trimmedIngredient);
                    userIngredient.setIngredientType("sub");
                    userIngredientRepository.save(userIngredient);
                    existingSubSet.add(lowerIngredient); // 메모리에도 추가하여 중복 방지
                }
            }
        }
    }
    
    /**
     * 사용자 재료 교체 (기존 재료 삭제 후 새로 저장)
     * 냉장고를 완전히 비우고 새로 채울 때 사용
     */
    @Transactional
    public void replaceUserIngredients(String userId, List<String> mainIngredients, List<String> subIngredients) {
        // 기존 재료 삭제
        userIngredientRepository.deleteAllByUserId(userId);
        
        // 주재료 저장
        for (String ingredient : mainIngredients) {
            if (ingredient != null && !ingredient.trim().isEmpty()) {
                UserIngredient userIngredient = new UserIngredient();
                userIngredient.setUserId(userId);
                userIngredient.setIngredient(ingredient.trim());
                userIngredient.setIngredientType("main");
                userIngredientRepository.save(userIngredient);
            }
        }
        
        // 부재료 저장
        for (String ingredient : subIngredients) {
            if (ingredient != null && !ingredient.trim().isEmpty()) {
                UserIngredient userIngredient = new UserIngredient();
                userIngredient.setUserId(userId);
                userIngredient.setIngredient(ingredient.trim());
                userIngredient.setIngredientType("sub");
                userIngredientRepository.save(userIngredient);
            }
        }
    }

    /**
     * 사용자 재료 조회 (주재료/부재료 구분)
     */
    public Map<String, List<String>> getUserIngredients(String userId) {
        List<UserIngredient> ingredients = userIngredientRepository.findByUserId(userId);
        
        List<String> mainIngredients = ingredients.stream()
                .filter(ing -> "main".equals(ing.getIngredientType()))
                .map(UserIngredient::getIngredient)
                .collect(Collectors.toList());
        
        List<String> subIngredients = ingredients.stream()
                .filter(ing -> "sub".equals(ing.getIngredientType()))
                .map(UserIngredient::getIngredient)
                .collect(Collectors.toList());
        
        return Map.of(
                "main_ingredients", mainIngredients,
                "sub_ingredients", subIngredients,
                "all_ingredients", ingredients.stream()
                        .map(UserIngredient::getIngredient)
                        .collect(Collectors.toList())
        );
    }

    /**
     * 사용자 재료 조회 (전체)
     */
    public List<String> getAllUserIngredients(String userId) {
        return userIngredientRepository.findByUserId(userId).stream()
                .map(UserIngredient::getIngredient)
                .collect(Collectors.toList());
    }

    /**
     * 사용자 재료 삭제
     */
    @Transactional
    public void deleteUserIngredients(String userId) {
        userIngredientRepository.deleteAllByUserId(userId);
    }
}

