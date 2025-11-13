package com.api.controller;

import com.api.dto.KakaoLoginRequest;
import com.api.dto.KakaoLoginResponse;
import com.api.service.KakaoAuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/auth/kakao")
@RequiredArgsConstructor
@Tag(name = "카카오 로그인", description = "카카오 소셜 로그인 API")
public class KakaoAuthController {

    private final KakaoAuthService kakaoAuthService;

    @Value("${kakao.client-id}")
    private String kakaoClientId;

    @Value("${kakao.redirect-uri}")
    private String kakaoRedirectUri;

    @Operation(summary = "카카오 로그인 URL 조회", description = "카카오 로그인 페이지 URL을 반환합니다.")
    @GetMapping("/login-url")
    public ResponseEntity<Map<String, String>> getKakaoLoginUrl() {
        String kakaoAuthUrl = String.format(
                "https://kauth.kakao.com/oauth/authorize?client_id=%s&redirect_uri=%s&response_type=code",
                kakaoClientId,
                kakaoRedirectUri
        );

        Map<String, String> response = new HashMap<>();
        response.put("loginUrl", kakaoAuthUrl);
        
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "카카오 로그인 콜백", description = "카카오 인가 코드로 로그인을 처리합니다.")
    @PostMapping("/callback")
    public ResponseEntity<KakaoLoginResponse> kakaoCallback(
            @Parameter(description = "카카오 인가 코드", required = true)
            @RequestBody KakaoLoginRequest request
    ) {
        try {
            log.info("카카오 로그인 콜백 시작 - code: {}", request.getCode());
            KakaoLoginResponse response = kakaoAuthService.kakaoLogin(request.getCode());
            log.info("카카오 로그인 성공 - kakaoId: {}, isNewUser: {}", response.getKakaoId(), response.isNewUser());
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("카카오 로그인 실패", e);
            throw new RuntimeException("카카오 로그인 처리 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    @Operation(summary = "카카오 로그인 콜백 (GET)", description = "카카오 인가 코드로 로그인을 처리합니다. (리다이렉트용)")
    @GetMapping("/callback")
    public ResponseEntity<KakaoLoginResponse> kakaoCallbackGet(
            @Parameter(description = "카카오 인가 코드", required = true)
            @RequestParam String code
    ) {
        try {
            log.info("카카오 로그인 콜백 (GET) 시작 - code: {}", code);
            KakaoLoginResponse response = kakaoAuthService.kakaoLogin(code);
            log.info("카카오 로그인 성공 - kakaoId: {}, isNewUser: {}", response.getKakaoId(), response.isNewUser());
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("카카오 로그인 실패", e);
            throw new RuntimeException("카카오 로그인 처리 중 오류가 발생했습니다: " + e.getMessage());
        }
    }

    @Operation(summary = "카카오 연동 해제", description = "카카오 계정 연동을 해제합니다.")
    @PostMapping("/unlink")
    public ResponseEntity<Map<String, String>> unlinkKakao(
            @Parameter(description = "카카오 사용자 ID", required = true)
            @RequestParam Long kakaoId
    ) {
        // TODO: 카카오 연동 해제 API 호출 구현
        Map<String, String> response = new HashMap<>();
        response.put("message", "카카오 연동 해제 기능은 추후 구현 예정입니다.");
        return ResponseEntity.ok(response);
    }
}

