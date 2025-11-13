package com.api.service;

import com.api.dto.UserSeasoningPivotRequest;
import com.api.entity.UserSeasoningPivot;
import com.api.repository.UserSeasoningPivotRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class UserSeasoningPivotService {
    private final UserSeasoningPivotRepository repository;

    @Transactional
    public void saveUserSeasonings(UserSeasoningPivotRequest request) {
        UserSeasoningPivot entity = new UserSeasoningPivot();
        entity.setUserId(request.getUserId());
        entity.set간장(request.is간장());
        entity.set된장(request.is된장());
        entity.set고추장(request.is고추장());
        entity.set소금(request.is소금());
        entity.set후추(request.is후추());
        entity.set설탕(request.is설탕());
        entity.set고춧가루(request.is고춧가루());
        entity.set식초(request.is식초());
        entity.set참기름(request.is참기름());
        repository.save(entity);
    }

    public UserSeasoningPivot getUserSeasonings(String userId) {
        return repository.findById(userId).orElse(null);
    }
} 