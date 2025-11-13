package com.api.repository;

import com.api.entity.KakaoUser;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface KakaoUserRepository extends JpaRepository<KakaoUser, Long> {
    Optional<KakaoUser> findByKakaoId(Long kakaoId);
    Optional<KakaoUser> findByEmail(String email);
    boolean existsByKakaoId(Long kakaoId);
}

