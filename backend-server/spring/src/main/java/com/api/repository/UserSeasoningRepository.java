package com.api.repository;

import com.api.entity.UserSeasoning;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface UserSeasoningRepository extends JpaRepository<UserSeasoning, Long> {
    List<UserSeasoning> findByUserId(String userId);
    void deleteByUserId(String userId);
} 