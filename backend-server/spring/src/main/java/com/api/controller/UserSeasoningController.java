package com.api.controller;

import com.api.service.UserSeasoningService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/user-seasonings")
@RequiredArgsConstructor
public class UserSeasoningController {
    private final UserSeasoningService userSeasoningService;

    @PostMapping("/{userId}")
    public ResponseEntity<Void> saveUserSeasonings(
            @PathVariable String userId,
            @RequestBody List<String> seasonings) {
        userSeasoningService.saveUserSeasonings(userId, seasonings);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/{userId}")
    public ResponseEntity<Map<String, Boolean>> getUserSeasonings(@PathVariable String userId) {
        return ResponseEntity.ok(userSeasoningService.getUserSeasoningsAsBoolean(userId));
    }
} 