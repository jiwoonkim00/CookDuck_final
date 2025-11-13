package com.api.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Schema(description = "로그인 요청")
public class LoginRequest {
    @Schema(description = "사용자 아이디", example = "user123")
    private String userId;

    @Schema(description = "비밀번호", example = "password123")
    private String password;
}