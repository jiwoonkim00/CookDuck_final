package com.api.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Random;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class EmailVerificationService {
    private final EmailService emailService;
    private final ConcurrentHashMap<String, String> verificationCodes = new ConcurrentHashMap<>();
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
    private static final long CODE_EXPIRATION_MINUTES = 10;

    @Transactional
    public void sendVerificationCode(String email) {
        // 인증 코드 생성
        String verificationCode = generateVerificationCode();
        
        // 맵에 인증 코드 저장
        verificationCodes.put(email, verificationCode);
        
        // 10분 후 코드 만료
        scheduler.schedule(() -> verificationCodes.remove(email), 
            CODE_EXPIRATION_MINUTES, TimeUnit.MINUTES);
        
        // 이메일 전송
        try {
            emailService.sendVerificationEmail(email, verificationCode);
        } catch (Exception e) {
            // 이메일 전송 실패 시 맵에서도 삭제
            verificationCodes.remove(email);
            System.out.println("이메일 전송 실패: " + e.getMessage());
            throw new RuntimeException("이메일 전송에 실패했습니다.", e);
        }
    }

    @Transactional
    public boolean verifyCode(String email, String code) {
        String storedCode = verificationCodes.get(email);
        
        if (storedCode == null) {
            return false; // 인증 코드가 만료되었거나 존재하지 않음
        }
        
        boolean isValid = storedCode.equals(code);
        
        if (isValid) {
            // 인증 성공 시 맵에서 코드 삭제
            verificationCodes.remove(email);
        }
        
        return isValid;
    }

    private String generateVerificationCode() {
        Random random = new Random();
        int code = 100000 + random.nextInt(900000); // 6자리 숫자
        return String.valueOf(code);
    }
} 