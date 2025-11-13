package com.api.service;

import com.api.dto.KakaoLoginResponse;
import com.api.dto.KakaoTokenResponse;
import com.api.dto.KakaoUserInfoResponse;
import com.api.entity.KakaoUser;
import com.api.repository.KakaoUserRepository;
import com.api.security.JwtTokenProvider;
import com.google.gson.Gson;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

@Slf4j
@Service
@RequiredArgsConstructor
public class KakaoAuthService {

    private final KakaoUserRepository kakaoUserRepository;
    private final JwtTokenProvider jwtTokenProvider;
    private final Gson gson;

    @Value("${kakao.client-id}")
    private String kakaoClientId;

    @Value("${kakao.redirect-uri}")
    private String kakaoRedirectUri;

    @Value("${kakao.client-secret:}")
    private String kakaoClientSecret;

    private static final String KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token";
    private static final String KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me";

    /**
     * 카카오 인가 코드로 액세스 토큰 발급
     */
    public KakaoTokenResponse getKakaoAccessToken(String code) {
        WebClient webClient = WebClient.builder()
                .baseUrl(KAKAO_TOKEN_URL)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_FORM_URLENCODED_VALUE)
                .build();

        MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
        params.add("grant_type", "authorization_code");
        params.add("client_id", kakaoClientId);
        params.add("redirect_uri", kakaoRedirectUri);
        params.add("code", code);
        
        if (kakaoClientSecret != null && !kakaoClientSecret.isEmpty()) {
            params.add("client_secret", kakaoClientSecret);
        }

        String response = webClient.post()
                .body(BodyInserters.fromFormData(params))
                .retrieve()
                .bodyToMono(String.class)
                .block();

        log.info("카카오 토큰 응답: {}", response);
        return gson.fromJson(response, KakaoTokenResponse.class);
    }

    /**
     * 카카오 액세스 토큰으로 사용자 정보 조회
     */
    public KakaoUserInfoResponse getKakaoUserInfo(String accessToken) {
        WebClient webClient = WebClient.builder()
                .baseUrl(KAKAO_USER_INFO_URL)
                .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer " + accessToken)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_FORM_URLENCODED_VALUE)
                .build();

        String response = webClient.get()
                .retrieve()
                .bodyToMono(String.class)
                .block();

        log.info("카카오 사용자 정보 응답: {}", response);
        return gson.fromJson(response, KakaoUserInfoResponse.class);
    }

    /**
     * 카카오 로그인 처리 (회원가입 or 로그인)
     */
    @Transactional
    public KakaoLoginResponse kakaoLogin(String code) {
        // 1. 인가 코드로 액세스 토큰 발급
        KakaoTokenResponse tokenResponse = getKakaoAccessToken(code);
        
        // 2. 액세스 토큰으로 사용자 정보 조회
        KakaoUserInfoResponse userInfo = getKakaoUserInfo(tokenResponse.getAccessToken());
        
        // 3. 사용자 정보 추출
        Long kakaoId = userInfo.getId();
        String nickname = extractNickname(userInfo);
        String email = extractEmail(userInfo);
        String profileImageUrl = extractProfileImageUrl(userInfo);
        String thumbnailImageUrl = extractThumbnailImageUrl(userInfo);
        
        // 4. 기존 사용자 확인 또는 신규 등록
        KakaoUser kakaoUser = kakaoUserRepository.findByKakaoId(kakaoId)
                .orElseGet(() -> {
                    KakaoUser newUser = new KakaoUser();
                    newUser.setKakaoId(kakaoId);
                    newUser.setNickname(nickname);
                    newUser.setEmail(email);
                    newUser.setProfileImageUrl(profileImageUrl);
                    newUser.setThumbnailImageUrl(thumbnailImageUrl);
                    newUser.setGrade("초보");
                    return kakaoUserRepository.save(newUser);
                });
        
        boolean isNewUser = kakaoUser.getCreatedAt().equals(kakaoUser.getUpdatedAt());
        
        // 5. JWT 토큰 생성
        String jwtToken = jwtTokenProvider.createToken("kakao_" + kakaoUser.getKakaoId());
        
        // 6. 응답 생성
        return new KakaoLoginResponse(
                jwtToken,
                kakaoUser.getKakaoId(),
                kakaoUser.getNickname(),
                kakaoUser.getEmail(),
                kakaoUser.getProfileImageUrl(),
                kakaoUser.getGrade(),
                isNewUser
        );
    }

    /**
     * 카카오 사용자 정보 업데이트
     */
    @Transactional
    public KakaoUser updateKakaoUser(Long kakaoId, KakaoUserInfoResponse userInfo) {
        KakaoUser kakaoUser = kakaoUserRepository.findByKakaoId(kakaoId)
                .orElseThrow(() -> new RuntimeException("카카오 사용자를 찾을 수 없습니다."));
        
        kakaoUser.setNickname(extractNickname(userInfo));
        kakaoUser.setEmail(extractEmail(userInfo));
        kakaoUser.setProfileImageUrl(extractProfileImageUrl(userInfo));
        kakaoUser.setThumbnailImageUrl(extractThumbnailImageUrl(userInfo));
        
        return kakaoUserRepository.save(kakaoUser);
    }

    // Helper methods
    private String extractNickname(KakaoUserInfoResponse userInfo) {
        if (userInfo.getKakaoAccount() != null && userInfo.getKakaoAccount().getProfile() != null) {
            return userInfo.getKakaoAccount().getProfile().getNickname();
        }
        if (userInfo.getProperties() != null) {
            return userInfo.getProperties().getNickname();
        }
        return "카카오사용자";
    }

    private String extractEmail(KakaoUserInfoResponse userInfo) {
        if (userInfo.getKakaoAccount() != null) {
            return userInfo.getKakaoAccount().getEmail();
        }
        return null;
    }

    private String extractProfileImageUrl(KakaoUserInfoResponse userInfo) {
        if (userInfo.getKakaoAccount() != null && userInfo.getKakaoAccount().getProfile() != null) {
            return userInfo.getKakaoAccount().getProfile().getProfileImageUrl();
        }
        if (userInfo.getProperties() != null) {
            return userInfo.getProperties().getProfileImage();
        }
        return null;
    }

    private String extractThumbnailImageUrl(KakaoUserInfoResponse userInfo) {
        if (userInfo.getKakaoAccount() != null && userInfo.getKakaoAccount().getProfile() != null) {
            return userInfo.getKakaoAccount().getProfile().getThumbnailImageUrl();
        }
        if (userInfo.getProperties() != null) {
            return userInfo.getProperties().getThumbnailImage();
        }
        return null;
    }
}

