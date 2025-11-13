package com.api.controller;

import com.api.dto.FindIdRequest;
import com.api.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/find-id")
@RequiredArgsConstructor
public class FindIdController {
    private final UserService userService;

    @PostMapping
    public ResponseEntity<String> findId(@RequestBody FindIdRequest request) {
        try {
            String userId = userService.findUserId(request.getName(), request.getEmail(), request.getCode());
            return ResponseEntity.ok(userId);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }
    }
} 