package com.api.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class ChangePasswordRequest {
    @Schema(description = "사용자 ID", example = "wkp48")
    private String userId;

    @Schema(description = "현재 비밀번호", example = "currentPassword123")
    private String currentPassword;

    @Schema(description = "새로운 비밀번호", example = "newPassword123")
    private String newPassword;
} 