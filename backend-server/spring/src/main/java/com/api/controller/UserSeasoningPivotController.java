package com.api.controller;

import com.api.dto.UserSeasoningPivotRequest;
import com.api.entity.UserSeasoningPivot;
import com.api.service.UserSeasoningPivotService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/user-seasoning-pivot")
@RequiredArgsConstructor
public class UserSeasoningPivotController {
    private final UserSeasoningPivotService service;

    @PostMapping
    public ResponseEntity<Void> saveUserSeasonings(@RequestBody UserSeasoningPivotRequest request) {
        service.saveUserSeasonings(request);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/{userId}")
    
    public ResponseEntity<UserSeasoningPivot> getUserSeasonings(@PathVariable String userId) {
        UserSeasoningPivot result = service.getUserSeasonings(userId);
        if (result == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(result);
    }
} 
