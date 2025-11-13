package com.api.controller;

import com.api.dto.UserGradeRequest;
import com.api.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/user-grade")
@RequiredArgsConstructor
public class UserGradeController {
    private final UserService userService;

    @PostMapping("/update")
    public ResponseEntity<Void> updateGrade(@RequestBody UserGradeRequest request) {
        userService.updateUserGrade(request.getUserId(), request.getGrade());
        return ResponseEntity.ok().build();
    }

    @GetMapping("/{userId}")
    public ResponseEntity<Map<String, String>> getGrade(@PathVariable String userId) {
        String grade = userService.getUserGrade(userId);
        Map<String, String> result = new HashMap<>();
        result.put("userGrade", grade);
        return ResponseEntity.ok(result);
    }
} 