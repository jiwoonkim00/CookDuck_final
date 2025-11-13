package com.api.dto;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
public class KakaoLoginResponse {
    private String accessToken;
    private Long kakaoId;
    private String nickname;
    private String email;
    private String profileImageUrl;
    private String grade;
    private boolean isNewUser;
}

