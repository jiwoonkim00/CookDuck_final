package com.api.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Schema(description = "비밀번호 재설정 요청")
public class ResetPasswordRequest {
    @Schema(description = "사용자 아이디", example = "user123")
    private String userId;

    @Schema(description = "이메일", example = "user@example.com")
    private String email;

    @Schema(description = "새로운 비밀번호", example = "newPassword123")
    private String newPassword;
} 