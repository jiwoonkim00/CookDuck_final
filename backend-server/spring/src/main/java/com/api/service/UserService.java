package com.api.service;

import com.api.dto.LoginResponse;
import com.api.entity.KakaoUser;
import com.api.entity.LoginAttempt;
import com.api.entity.User;
import com.api.repository.KakaoUserRepository;
import com.api.repository.LoginAttemptRepository;
import com.api.repository.UserRepository;
import com.api.security.JwtTokenProvider;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.api.repository.UserSeasoningPivotRepository;
import com.api.dto.UserInfoResponse;

import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
@Transactional
public class UserService {

    private final UserRepository userRepository;
    private final KakaoUserRepository kakaoUserRepository;
    private final LoginAttemptRepository loginAttemptRepository;
    private final HttpServletRequest request;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final AuthenticationManager authenticationManager;
    private final EmailVerificationService emailVerificationService;
    private final UserSeasoningPivotRepository userSeasoningPivotRepository;

    public void registerUser(User user) {
        if (userRepository.existsByUserId(user.getUserId())) {
            throw new IllegalArgumentException("이미 사용 중인 아이디입니다.");
        }
        if (userRepository.existsByEmail(user.getEmail())) {
            throw new IllegalArgumentException("이미 사용 중인 이메일입니다.");
        }
        
        // 비밀번호 암호화
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        userRepository.save(user);
    }

    public LoginResponse login(String userId, String password) {
        LoginAttempt loginAttempt = new LoginAttempt();
        loginAttempt.setUserId(userId);
        loginAttempt.setAttemptTime(LocalDateTime.now());
        loginAttempt.setIpAddress(getClientIp());

        try {
            User user = userRepository.findByUserId(userId)
                    .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));

            if (!passwordEncoder.matches(password, user.getPassword())) {
                loginAttempt.setStatus("FAILED");
                loginAttemptRepository.save(loginAttempt);
                throw new IllegalArgumentException("비밀번호가 일치하지 않습니다.");
            }

            loginAttempt.setStatus("SUCCESS");

            // JWT 토큰 생성
            Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(userId, password)
            );
            String jwt = jwtTokenProvider.generateToken(authentication);
            loginAttempt.setJwtToken(jwt);

            loginAttemptRepository.save(loginAttempt);

            return new LoginResponse(user.getUserId(), user.getName(), user.getEmail(), jwt);
        } catch (Exception e) {
            loginAttempt.setStatus("FAILED");
            loginAttemptRepository.save(loginAttempt);
            throw e;
        }
    }

    public void resetPassword(String userId, String email, String newPassword) {
        User user = userRepository.findByUserId(userId)
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));

        // 이메일 일치 여부 확인
        if (!user.getEmail().equals(email)) {
            throw new IllegalArgumentException("이메일이 일치하지 않습니다.");
        }

        // 새 비밀번호 암호화
        String encodedPassword = passwordEncoder.encode(newPassword);
        user.setPassword(encodedPassword);
        userRepository.save(user);
    }

    public String findUserId(String name, String email, String code) {
        if (!emailVerificationService.verifyCode(email, code)) {
            throw new IllegalArgumentException("인증 코드가 올바르지 않습니다.");
        }
        User user = userRepository.findByNameAndEmail(name, email)
            .orElseThrow(() -> new IllegalArgumentException("일치하는 사용자가 없습니다."));
        return user.getUserId();
    }

    public void findAndResetPassword(String userId, String email, String code, String newPassword) {
        if (!emailVerificationService.verifyCode(email, code)) {
            throw new IllegalArgumentException("인증 코드가 올바르지 않습니다.");
        }
        User user = userRepository.findByUserId(userId)
            .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));
        if (!user.getEmail().equals(email)) {
            throw new IllegalArgumentException("이메일이 일치하지 않습니다.");
        }
        user.setPassword(passwordEncoder.encode(newPassword));
        userRepository.save(user);
    }

    public void deleteUser(String userId) {
        userSeasoningPivotRepository.deleteById(userId);
        userRepository.deleteByUserId(userId);
    }

    public void updateUserGrade(String userId, String grade) {
        User user = userRepository.findByUserId(userId)
            .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));
        user.setGrade(grade);
        userRepository.save(user);
    }

    public String getUserGrade(String userId) {
        // 카카오 사용자인지 확인 (userId가 "kakao_"로 시작하는 경우)
        if (userId != null && userId.startsWith("kakao_")) {
            String kakaoIdStr = userId.substring(6); // "kakao_" 제거
            try {
                Long kakaoId = Long.parseLong(kakaoIdStr);
                KakaoUser kakaoUser = kakaoUserRepository.findByKakaoId(kakaoId)
                    .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));
                return kakaoUser.getGrade();
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException("잘못된 사용자 ID입니다.");
            }
        }
        
        // 일반 사용자
        User user = userRepository.findByUserId(userId)
            .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));
        return user.getGrade();
    }

    public UserInfoResponse getUserInfo(String userId) {
        // 카카오 사용자인지 확인 (userId가 "kakao_"로 시작하는 경우)
        if (userId != null && userId.startsWith("kakao_")) {
            String kakaoIdStr = userId.substring(6); // "kakao_" 제거
            try {
                Long kakaoId = Long.parseLong(kakaoIdStr);
                KakaoUser kakaoUser = kakaoUserRepository.findByKakaoId(kakaoId)
                    .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));
                
                return new UserInfoResponse(
                    userId,
                    kakaoUser.getEmail() != null ? kakaoUser.getEmail() : "",
                    kakaoUser.getNickname(),
                    kakaoUser.getGrade()
                );
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException("잘못된 사용자 ID입니다.");
            }
        }
        
        // 일반 사용자
        User user = userRepository.findByUserId(userId)
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));
        
        return new UserInfoResponse(
            user.getUserId(),
            user.getEmail(),
            user.getName(),
            user.getGrade()
        );
    }

    public void changePassword(String userId, String currentPassword, String newPassword) {
        User user = userRepository.findByUserId(userId)
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 사용자입니다."));

        // 현재 비밀번호 확인
        if (!passwordEncoder.matches(currentPassword, user.getPassword())) {
            throw new IllegalArgumentException("현재 비밀번호가 일치하지 않습니다.");
        }

        // 새 비밀번호 암호화
        String encodedPassword = passwordEncoder.encode(newPassword);
        user.setPassword(encodedPassword);
        userRepository.save(user);
    }

    private String getClientIp() {
        String ipAddress = request.getHeader("X-Forwarded-For");
        if (ipAddress == null || ipAddress.isEmpty() || "unknown".equalsIgnoreCase(ipAddress)) {
            ipAddress = request.getHeader("Proxy-Client-IP");
        }
        if (ipAddress == null || ipAddress.isEmpty() || "unknown".equalsIgnoreCase(ipAddress)) {
            ipAddress = request.getHeader("WL-Proxy-Client-IP");
        }
        if (ipAddress == null || ipAddress.isEmpty() || "unknown".equalsIgnoreCase(ipAddress)) {
            ipAddress = request.getRemoteAddr();
        }
        return ipAddress;
    }
} 