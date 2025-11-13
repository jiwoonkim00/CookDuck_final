package com.api.service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class EmailService {
    private final JavaMailSender mailSender;

    public void sendVerificationEmail(String to, String verificationCode) throws MessagingException {
        MimeMessage message = mailSender.createMimeMessage();
        MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");

        helper.setFrom("noreply@cookduck.com");
        helper.setTo(to);
        helper.setSubject("[CookDuck] 이메일 인증 코드");
        helper.setText(String.format("""
            안녕하세요. CookDuck입니다.
            
            이메일 인증 코드는 다음과 같습니다:
            %s
            
            이 코드는 10분 후에 만료됩니다.
            
            감사합니다.
            CookDuck 팀 드림
            """, verificationCode));

        mailSender.send(message);
        System.out.println("이메일 전송 완료: " + to);
    }
} 