package com.api.service;

import com.api.entity.UserSeasoningPivot;
import com.api.repository.UserSeasoningPivotRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class UserSeasoningService {
    private final UserSeasoningPivotRepository userSeasoningPivotRepository;

    @Transactional
    public void saveUserSeasonings(String userId, List<String> seasonings) {
        UserSeasoningPivot pivot = userSeasoningPivotRepository.findById(userId)
                .orElse(new UserSeasoningPivot());
        
        pivot.setUserId(userId);
        pivot.set간장(seasonings.contains("간장"));
        pivot.set된장(seasonings.contains("된장"));
        pivot.set고추장(seasonings.contains("고추장"));
        pivot.set소금(seasonings.contains("소금"));
        pivot.set후추(seasonings.contains("후추"));
        pivot.set설탕(seasonings.contains("설탕"));
        pivot.set고춧가루(seasonings.contains("고춧가루"));
        pivot.set식초(seasonings.contains("식초"));
        pivot.set참기름(seasonings.contains("참기름"));
        
        userSeasoningPivotRepository.save(pivot);
    }

    public Map<String, Boolean> getUserSeasoningsAsBoolean(String userId) {
        UserSeasoningPivot pivot = userSeasoningPivotRepository.findById(userId)
                .orElse(new UserSeasoningPivot());
        
        Map<String, Boolean> result = new HashMap<>();
        result.put("간장", pivot.is간장());
        result.put("된장", pivot.is된장());
        result.put("고추장", pivot.is고추장());
        result.put("소금", pivot.is소금());
        result.put("후추", pivot.is후추());
        result.put("설탕", pivot.is설탕());
        result.put("고춧가루", pivot.is고춧가루());
        result.put("식초", pivot.is식초());
        result.put("참기름", pivot.is참기름());
        
        return result;
    }
} 