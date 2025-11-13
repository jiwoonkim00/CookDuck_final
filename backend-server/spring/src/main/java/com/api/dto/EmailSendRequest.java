package com.api.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Schema(description = "이메일 인증 코드 전송 요청")
public class EmailSendRequest {
    @Schema(description = "이메일", example = "user@example.com")
    private String email;
} 