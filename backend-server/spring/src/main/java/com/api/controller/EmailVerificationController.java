package com.api.controller;

import com.api.dto.EmailVerificationRequest;
import com.api.dto.EmailSendRequest;
import com.api.service.EmailVerificationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Tag(name = "이메일 인증", description = "이메일 인증 API")
@RestController
@RequestMapping("/api/email-verification")
@RequiredArgsConstructor
public class EmailVerificationController {
    private final EmailVerificationService emailVerificationService;

    @Operation(summary = "인증 코드 전송", description = "이메일로 인증 코드를 전송합니다.")
    @PostMapping("/send")
    public ResponseEntity<Void> sendVerificationCode(@RequestBody EmailSendRequest request) {
        try {
            emailVerificationService.sendVerificationCode(request.getEmail());
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            throw new RuntimeException("이메일 전송에 실패했습니다.", e);
        }
    }

    @Operation(summary = "인증 코드 확인", description = "이메일 인증 코드를 확인합니다.")
    @PostMapping("/verify")
    public ResponseEntity<Boolean> verifyCode(@RequestBody EmailVerificationRequest request) {
        boolean isVerified = emailVerificationService.verifyCode(request.getEmail(), request.getVerificationCode());
        return ResponseEntity.ok(isVerified);
    }
} 