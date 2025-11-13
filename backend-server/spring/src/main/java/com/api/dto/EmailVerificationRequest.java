package com.api.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Schema(description = "이메일 인증 요청")
public class EmailVerificationRequest {
    @Schema(description = "이메일", example = "user@example.com")
    private String email;

    @Schema(description = "인증 코드", example = "123456")
    private String verificationCode;
} 