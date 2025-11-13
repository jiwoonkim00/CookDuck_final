package com.api.service;

import com.api.entity.*;
import com.api.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AdminService {

    private final UserRepository userRepository;
    private final KakaoUserRepository kakaoUserRepository;
    private final UserSeasoningRepository userSeasoningRepository;
    private final UserSeasoningPivotRepository userSeasoningPivotRepository;
    private final LoginAttemptRepository loginAttemptRepository;
    private final org.springframework.security.crypto.password.PasswordEncoder passwordEncoder;

    /**
     * 모든 테이블의 통계 정보 조회
     */
    public Map<String, Object> getDatabaseStatistics() {
        Map<String, Object> stats = new LinkedHashMap<>();
        
        Map<String, Long> tableCounts = new LinkedHashMap<>();
        tableCounts.put("users", userRepository.count());
        tableCounts.put("kakao_users", kakaoUserRepository.count());
        tableCounts.put("user_seasonings", userSeasoningRepository.count());
        tableCounts.put("user_seasoning_pivot", userSeasoningPivotRepository.count());
        tableCounts.put("login_attempts", loginAttemptRepository.count());
        
        stats.put("tableCounts", tableCounts);
        stats.put("totalRecords", tableCounts.values().stream().mapToLong(Long::longValue).sum());
        
        return stats;
    }

    /**
     * Users 테이블 전체 조회
     */
    public List<Map<String, Object>> getAllUsers() {
        return userRepository.findAll().stream()
                .map(this::convertUserToMap)
                .collect(Collectors.toList());
    }

    /**
     * KakaoUsers 테이블 전체 조회
     */
    public List<Map<String, Object>> getAllKakaoUsers() {
        return kakaoUserRepository.findAll().stream()
                .map(this::convertKakaoUserToMap)
                .collect(Collectors.toList());
    }

    /**
     * UserSeasonings 테이블 전체 조회
     */
    public List<Map<String, Object>> getAllUserSeasonings() {
        return userSeasoningRepository.findAll().stream()
                .map(this::convertUserSeasoningToMap)
                .collect(Collectors.toList());
    }

    /**
     * UserSeasoningPivot 테이블 전체 조회
     */
    public List<Map<String, Object>> getAllUserSeasoningPivots() {
        return userSeasoningPivotRepository.findAll().stream()
                .map(this::convertUserSeasoningPivotToMap)
                .collect(Collectors.toList());
    }

    /**
     * LoginAttempts 테이블 전체 조회
     */
    public List<Map<String, Object>> getAllLoginAttempts() {
        return loginAttemptRepository.findAll().stream()
                .map(this::convertLoginAttemptToMap)
                .collect(Collectors.toList());
    }

    /**
     * 테이블명으로 데이터 조회
     */
    public List<Map<String, Object>> getTableData(String tableName) {
        return switch (tableName.toLowerCase()) {
            case "users" -> getAllUsers();
            case "kakao_users" -> getAllKakaoUsers();
            case "user_seasonings" -> getAllUserSeasonings();
            case "user_seasoning_pivot" -> getAllUserSeasoningPivots();
            case "login_attempts" -> getAllLoginAttempts();
            default -> throw new IllegalArgumentException("Unknown table: " + tableName);
        };
    }

    /**
     * User 삭제
     */
    @Transactional
    public void deleteUser(Long id) {
        userRepository.deleteById(id);
    }

    /**
     * KakaoUser 삭제
     */
    @Transactional
    public void deleteKakaoUser(Long id) {
        kakaoUserRepository.deleteById(id);
    }

    /**
     * UserSeasoning 삭제
     */
    @Transactional
    public void deleteUserSeasoning(Long id) {
        userSeasoningRepository.deleteById(id);
    }

    /**
     * UserSeasoningPivot 삭제
     */
    @Transactional
    public void deleteUserSeasoningPivot(String userId) {
        userSeasoningPivotRepository.deleteById(userId);
    }

    /**
     * LoginAttempt 삭제
     */
    @Transactional
    public void deleteLoginAttempt(Long id) {
        loginAttemptRepository.deleteById(id);
    }

    /**
     * 테이블의 모든 데이터 삭제
     */
    @Transactional
    public void truncateTable(String tableName) {
        switch (tableName.toLowerCase()) {
            case "users" -> userRepository.deleteAll();
            case "kakao_users" -> kakaoUserRepository.deleteAll();
            case "user_seasonings" -> userSeasoningRepository.deleteAll();
            case "user_seasoning_pivot" -> userSeasoningPivotRepository.deleteAll();
            case "login_attempts" -> loginAttemptRepository.deleteAll();
            default -> throw new IllegalArgumentException("Unknown table: " + tableName);
        }
    }

    /**
     * 일반 사용자 추가
     */
    @Transactional
    public User createUser(String userId, String email, String password, String name, String grade) {
        // 중복 체크
        if (userRepository.findByUserId(userId).isPresent()) {
            throw new IllegalArgumentException("이미 존재하는 사용자 ID입니다: " + userId);
        }
        if (userRepository.findByEmail(email).isPresent()) {
            throw new IllegalArgumentException("이미 존재하는 이메일입니다: " + email);
        }

        // 사용자 생성
        User user = new User();
        user.setUserId(userId);
        user.setEmail(email);
        user.setPassword(passwordEncoder.encode(password));
        user.setName(name);
        user.setGrade(grade != null && !grade.isEmpty() ? grade : "초보");

        return userRepository.save(user);
    }

    // Converter methods
    private Map<String, Object> convertUserToMap(User user) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", user.getId());
        map.put("userId", user.getUserId());
        map.put("email", user.getEmail());
        map.put("name", user.getName());
        map.put("grade", user.getGrade());
        map.put("password", "******"); // 비밀번호는 숨김
        return map;
    }

    private Map<String, Object> convertKakaoUserToMap(KakaoUser user) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", user.getId());
        map.put("kakaoId", user.getKakaoId());
        map.put("nickname", user.getNickname());
        map.put("email", user.getEmail());
        map.put("profileImageUrl", user.getProfileImageUrl());
        map.put("thumbnailImageUrl", user.getThumbnailImageUrl());
        map.put("grade", user.getGrade());
        map.put("createdAt", user.getCreatedAt());
        map.put("updatedAt", user.getUpdatedAt());
        return map;
    }

    private Map<String, Object> convertUserSeasoningToMap(UserSeasoning seasoning) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", seasoning.getId());
        map.put("userId", seasoning.getUserId());
        map.put("seasoning", seasoning.getSeasoning());
        return map;
    }

    private Map<String, Object> convertUserSeasoningPivotToMap(UserSeasoningPivot pivot) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("userId", pivot.getUserId());
        map.put("간장", pivot.is간장());
        map.put("된장", pivot.is된장());
        map.put("고추장", pivot.is고추장());
        map.put("소금", pivot.is소금());
        map.put("후추", pivot.is후추());
        map.put("설탕", pivot.is설탕());
        map.put("고춧가루", pivot.is고춧가루());
        map.put("식초", pivot.is식초());
        map.put("참기름", pivot.is참기름());
        return map;
    }

    private Map<String, Object> convertLoginAttemptToMap(LoginAttempt attempt) {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", attempt.getId());
        map.put("userId", attempt.getUserId());
        map.put("attemptTime", attempt.getAttemptTime());
        map.put("status", attempt.getStatus());
        map.put("ipAddress", attempt.getIpAddress());
        map.put("jwtToken", attempt.getJwtToken() != null ? "******" : null);
        return map;
    }

    /**
     * 테이블 스키마 정보 조회
     */
    public Map<String, List<Map<String, String>>> getTableSchemas() {
        Map<String, List<Map<String, String>>> schemas = new LinkedHashMap<>();
        
        // Users
        List<Map<String, String>> usersSchema = new ArrayList<>();
        usersSchema.add(createColumn("id", "Long", "PRIMARY KEY"));
        usersSchema.add(createColumn("userId", "String", "UNIQUE, NOT NULL"));
        usersSchema.add(createColumn("email", "String", "UNIQUE, NOT NULL"));
        usersSchema.add(createColumn("password", "String", "NOT NULL"));
        usersSchema.add(createColumn("name", "String", "NOT NULL"));
        usersSchema.add(createColumn("grade", "String", "DEFAULT '초보'"));
        schemas.put("users", usersSchema);
        
        // KakaoUsers
        List<Map<String, String>> kakaoUsersSchema = new ArrayList<>();
        kakaoUsersSchema.add(createColumn("id", "Long", "PRIMARY KEY"));
        kakaoUsersSchema.add(createColumn("kakaoId", "Long", "UNIQUE, NOT NULL"));
        kakaoUsersSchema.add(createColumn("nickname", "String", "NOT NULL"));
        kakaoUsersSchema.add(createColumn("email", "String", "UNIQUE"));
        kakaoUsersSchema.add(createColumn("profileImageUrl", "String", ""));
        kakaoUsersSchema.add(createColumn("thumbnailImageUrl", "String", ""));
        kakaoUsersSchema.add(createColumn("grade", "String", "DEFAULT '초보'"));
        kakaoUsersSchema.add(createColumn("createdAt", "DateTime", "NOT NULL"));
        kakaoUsersSchema.add(createColumn("updatedAt", "DateTime", "NOT NULL"));
        schemas.put("kakao_users", kakaoUsersSchema);
        
        // UserSeasonings
        List<Map<String, String>> userSeasoningsSchema = new ArrayList<>();
        userSeasoningsSchema.add(createColumn("id", "Long", "PRIMARY KEY"));
        userSeasoningsSchema.add(createColumn("userId", "String", "NOT NULL"));
        userSeasoningsSchema.add(createColumn("seasoning", "String", "NOT NULL"));
        schemas.put("user_seasonings", userSeasoningsSchema);
        
        // UserSeasoningPivot
        List<Map<String, String>> pivotSchema = new ArrayList<>();
        pivotSchema.add(createColumn("userId", "String", "PRIMARY KEY"));
        pivotSchema.add(createColumn("간장", "Boolean", ""));
        pivotSchema.add(createColumn("된장", "Boolean", ""));
        pivotSchema.add(createColumn("고추장", "Boolean", ""));
        pivotSchema.add(createColumn("소금", "Boolean", ""));
        pivotSchema.add(createColumn("후추", "Boolean", ""));
        pivotSchema.add(createColumn("설탕", "Boolean", ""));
        pivotSchema.add(createColumn("고춧가루", "Boolean", ""));
        pivotSchema.add(createColumn("식초", "Boolean", ""));
        pivotSchema.add(createColumn("참기름", "Boolean", ""));
        schemas.put("user_seasoning_pivot", pivotSchema);
        
        // LoginAttempts
        List<Map<String, String>> loginAttemptsSchema = new ArrayList<>();
        loginAttemptsSchema.add(createColumn("id", "Long", "PRIMARY KEY"));
        loginAttemptsSchema.add(createColumn("userId", "String", "NOT NULL"));
        loginAttemptsSchema.add(createColumn("attemptTime", "DateTime", "NOT NULL"));
        loginAttemptsSchema.add(createColumn("status", "String", "NOT NULL"));
        loginAttemptsSchema.add(createColumn("ipAddress", "String", ""));
        loginAttemptsSchema.add(createColumn("jwtToken", "String", ""));
        schemas.put("login_attempts", loginAttemptsSchema);
        
        return schemas;
    }

    private Map<String, String> createColumn(String name, String type, String constraint) {
        Map<String, String> column = new LinkedHashMap<>();
        column.put("name", name);
        column.put("type", type);
        column.put("constraint", constraint);
        return column;
    }
}

