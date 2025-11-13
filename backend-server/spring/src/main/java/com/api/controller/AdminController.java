package com.api.controller;

import com.api.service.AdminService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/admin")
@RequiredArgsConstructor
@Tag(name = "데이터베이스 관리", description = "데이터베이스 관리 API")
public class AdminController {

    private final AdminService adminService;

    @Operation(summary = "데이터베이스 통계 조회", description = "모든 테이블의 레코드 수 및 통계 정보를 조회합니다.")
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getDatabaseStatistics() {
        try {
            Map<String, Object> stats = adminService.getDatabaseStatistics();
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            log.error("데이터베이스 통계 조회 실패", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "테이블 스키마 조회", description = "모든 테이블의 스키마 정보를 조회합니다.")
    @GetMapping("/schemas")
    public ResponseEntity<Map<String, List<Map<String, String>>>> getTableSchemas() {
        try {
            Map<String, List<Map<String, String>>> schemas = adminService.getTableSchemas();
            return ResponseEntity.ok(schemas);
        } catch (Exception e) {
            log.error("테이블 스키마 조회 실패", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "테이블 데이터 조회", description = "지정된 테이블의 모든 데이터를 조회합니다.")
    @GetMapping("/table/{tableName}")
    public ResponseEntity<List<Map<String, Object>>> getTableData(
            @Parameter(description = "테이블명 (users, kakao_users, user_seasonings, user_seasoning_pivot, login_attempts)", required = true)
            @PathVariable String tableName
    ) {
        try {
            List<Map<String, Object>> data = adminService.getTableData(tableName);
            return ResponseEntity.ok(data);
        } catch (IllegalArgumentException e) {
            log.error("잘못된 테이블명: {}", tableName);
            return ResponseEntity.badRequest().build();
        } catch (Exception e) {
            log.error("테이블 데이터 조회 실패: {}", tableName, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "Users 데이터 조회", description = "일반 사용자 테이블의 모든 데이터를 조회합니다.")
    @GetMapping("/users")
    public ResponseEntity<List<Map<String, Object>>> getAllUsers() {
        try {
            List<Map<String, Object>> users = adminService.getAllUsers();
            return ResponseEntity.ok(users);
        } catch (Exception e) {
            log.error("Users 조회 실패", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "KakaoUsers 데이터 조회", description = "카카오 사용자 테이블의 모든 데이터를 조회합니다.")
    @GetMapping("/kakao-users")
    public ResponseEntity<List<Map<String, Object>>> getAllKakaoUsers() {
        try {
            List<Map<String, Object>> kakaoUsers = adminService.getAllKakaoUsers();
            return ResponseEntity.ok(kakaoUsers);
        } catch (Exception e) {
            log.error("KakaoUsers 조회 실패", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "UserSeasonings 데이터 조회", description = "사용자 조미료 테이블의 모든 데이터를 조회합니다.")
    @GetMapping("/user-seasonings")
    public ResponseEntity<List<Map<String, Object>>> getAllUserSeasonings() {
        try {
            List<Map<String, Object>> seasonings = adminService.getAllUserSeasonings();
            return ResponseEntity.ok(seasonings);
        } catch (Exception e) {
            log.error("UserSeasonings 조회 실패", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "UserSeasoningPivot 데이터 조회", description = "사용자 조미료 피벗 테이블의 모든 데이터를 조회합니다.")
    @GetMapping("/user-seasoning-pivots")
    public ResponseEntity<List<Map<String, Object>>> getAllUserSeasoningPivots() {
        try {
            List<Map<String, Object>> pivots = adminService.getAllUserSeasoningPivots();
            return ResponseEntity.ok(pivots);
        } catch (Exception e) {
            log.error("UserSeasoningPivot 조회 실패", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "LoginAttempts 데이터 조회", description = "로그인 시도 테이블의 모든 데이터를 조회합니다.")
    @GetMapping("/login-attempts")
    public ResponseEntity<List<Map<String, Object>>> getAllLoginAttempts() {
        try {
            List<Map<String, Object>> attempts = adminService.getAllLoginAttempts();
            return ResponseEntity.ok(attempts);
        } catch (Exception e) {
            log.error("LoginAttempts 조회 실패", e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "User 삭제", description = "지정된 ID의 일반 사용자를 삭제합니다.")
    @DeleteMapping("/users/{id}")
    public ResponseEntity<Map<String, String>> deleteUser(
            @Parameter(description = "사용자 ID", required = true)
            @PathVariable Long id
    ) {
        try {
            adminService.deleteUser(id);
            return ResponseEntity.ok(Map.of("message", "User deleted successfully", "id", String.valueOf(id)));
        } catch (Exception e) {
            log.error("User 삭제 실패: {}", id, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "KakaoUser 삭제", description = "지정된 ID의 카카오 사용자를 삭제합니다.")
    @DeleteMapping("/kakao-users/{id}")
    public ResponseEntity<Map<String, String>> deleteKakaoUser(
            @Parameter(description = "카카오 사용자 ID", required = true)
            @PathVariable Long id
    ) {
        try {
            adminService.deleteKakaoUser(id);
            return ResponseEntity.ok(Map.of("message", "KakaoUser deleted successfully", "id", String.valueOf(id)));
        } catch (Exception e) {
            log.error("KakaoUser 삭제 실패: {}", id, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "UserSeasoning 삭제", description = "지정된 ID의 사용자 조미료를 삭제합니다.")
    @DeleteMapping("/user-seasonings/{id}")
    public ResponseEntity<Map<String, String>> deleteUserSeasoning(
            @Parameter(description = "조미료 ID", required = true)
            @PathVariable Long id
    ) {
        try {
            adminService.deleteUserSeasoning(id);
            return ResponseEntity.ok(Map.of("message", "UserSeasoning deleted successfully", "id", String.valueOf(id)));
        } catch (Exception e) {
            log.error("UserSeasoning 삭제 실패: {}", id, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "UserSeasoningPivot 삭제", description = "지정된 userId의 조미료 피벗을 삭제합니다.")
    @DeleteMapping("/user-seasoning-pivots/{userId}")
    public ResponseEntity<Map<String, String>> deleteUserSeasoningPivot(
            @Parameter(description = "사용자 ID", required = true)
            @PathVariable String userId
    ) {
        try {
            adminService.deleteUserSeasoningPivot(userId);
            return ResponseEntity.ok(Map.of("message", "UserSeasoningPivot deleted successfully", "userId", userId));
        } catch (Exception e) {
            log.error("UserSeasoningPivot 삭제 실패: {}", userId, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "LoginAttempt 삭제", description = "지정된 ID의 로그인 시도를 삭제합니다.")
    @DeleteMapping("/login-attempts/{id}")
    public ResponseEntity<Map<String, String>> deleteLoginAttempt(
            @Parameter(description = "로그인 시도 ID", required = true)
            @PathVariable Long id
    ) {
        try {
            adminService.deleteLoginAttempt(id);
            return ResponseEntity.ok(Map.of("message", "LoginAttempt deleted successfully", "id", String.valueOf(id)));
        } catch (Exception e) {
            log.error("LoginAttempt 삭제 실패: {}", id, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "테이블 전체 삭제", description = "지정된 테이블의 모든 데이터를 삭제합니다. (주의: 복구 불가능)")
    @DeleteMapping("/table/{tableName}/truncate")
    public ResponseEntity<Map<String, String>> truncateTable(
            @Parameter(description = "테이블명", required = true)
            @PathVariable String tableName
    ) {
        try {
            adminService.truncateTable(tableName);
            return ResponseEntity.ok(Map.of("message", "Table truncated successfully", "table", tableName));
        } catch (IllegalArgumentException e) {
            log.error("잘못된 테이블명: {}", tableName);
            return ResponseEntity.badRequest().build();
        } catch (Exception e) {
            log.error("테이블 삭제 실패: {}", tableName, e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @Operation(summary = "일반 사용자 추가", description = "새로운 일반 사용자를 생성합니다.")
    @PostMapping("/users")
    public ResponseEntity<?> createUser(
            @Parameter(description = "사용자 정보", required = true)
            @RequestBody com.api.dto.CreateUserRequest request
    ) {
        try {
            com.api.entity.User user = adminService.createUser(
                    request.getUserId(),
                    request.getEmail(),
                    request.getPassword(),
                    request.getName(),
                    request.getGrade()
            );
            
            Map<String, Object> response = new LinkedHashMap<>();
            response.put("message", "User created successfully");
            response.put("id", user.getId());
            response.put("userId", user.getUserId());
            response.put("email", user.getEmail());
            response.put("name", user.getName());
            response.put("grade", user.getGrade());
            
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            log.error("사용자 추가 실패 - 유효성 검사 오류: {}", e.getMessage());
            return ResponseEntity.badRequest().body(Map.of("error", e.getMessage()));
        } catch (Exception e) {
            log.error("사용자 추가 실패", e);
            return ResponseEntity.internalServerError().body(Map.of("error", "사용자 추가 중 오류가 발생했습니다."));
        }
    }
}

