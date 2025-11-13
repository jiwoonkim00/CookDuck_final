package com.api.controller;

import com.api.dto.FindPasswordRequest;
import com.api.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/find-password")
@RequiredArgsConstructor
public class FindPasswordController {
    private final UserService userService;

    @PostMapping
    public ResponseEntity<String> findAndResetPassword(@RequestBody FindPasswordRequest request) {
        try {
            userService.findAndResetPassword(
                request.getUserId(),
                request.getEmail(),
                request.getCode(),
                request.getNewPassword()
            );
            return ResponseEntity.ok().build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(e.getMessage());
        }
    }
} 