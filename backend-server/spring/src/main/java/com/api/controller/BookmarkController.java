package com.api.controller;

import com.api.dto.BookmarkRequest;
import com.api.dto.BookmarkResponse;
import com.api.entity.Bookmark;
import com.api.service.BookmarkService;
import com.api.service.RecipeService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Tag(name = "북마크 관리", description = "레시피 북마크 관리 API")
@RestController
@RequestMapping("/api/bookmarks")
@RequiredArgsConstructor
public class BookmarkController {
    private final BookmarkService bookmarkService;
    private final RecipeService recipeService;

    @Operation(summary = "북마크 추가", description = "사용자의 레시피 북마크를 추가합니다.")
    @PostMapping("/{userId}")
    public ResponseEntity<Void> addBookmark(
            @PathVariable String userId,
            @RequestBody BookmarkRequest request) {
        bookmarkService.addBookmark(userId, request.getRecipeId());
        return ResponseEntity.ok().build();
    }

    @Operation(summary = "북마크 삭제", description = "사용자의 레시피 북마크를 삭제합니다.")
    @DeleteMapping("/{userId}/{recipeId}")
    public ResponseEntity<Void> removeBookmark(
            @PathVariable String userId,
            @PathVariable String recipeId) {
        bookmarkService.removeBookmark(userId, recipeId);
        return ResponseEntity.ok().build();
    }

    @Operation(summary = "북마크 목록 조회", description = "사용자의 모든 북마크 목록을 조회합니다.")
    @GetMapping("/{userId}")
    public ResponseEntity<List<BookmarkResponse>> getBookmarks(@PathVariable String userId) {
        List<Bookmark> bookmarks = bookmarkService.getBookmarks(userId);
        List<BookmarkResponse> response = bookmarks.stream()
                .map(bookmark -> {
                    Map<String, Object> recipeInfo = Map.of();
                    try {
                        Long recipeId = Long.parseLong(bookmark.getRecipeId());
                        recipeInfo = recipeService.getRecipeById(recipeId);
                    } catch (NumberFormatException ignored) {
                    } catch (IllegalArgumentException ignored) {
                    }
                    return new BookmarkResponse(
                        bookmark.getId(),
                        bookmark.getUserId(),
                        bookmark.getRecipeId(),
                            bookmark.getCreatedAt(),
                            recipeInfo
                    );
                })
                .collect(Collectors.toList());
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "북마크 여부 확인", description = "특정 레시피가 북마크되어 있는지 확인합니다.")
    @GetMapping("/{userId}/{recipeId}")
    public ResponseEntity<Map<String, Boolean>> isBookmarked(
            @PathVariable String userId,
            @PathVariable String recipeId) {
        boolean isBookmarked = bookmarkService.isBookmarked(userId, recipeId);
        Map<String, Boolean> response = new HashMap<>();
        response.put("isBookmarked", isBookmarked);
        return ResponseEntity.ok(response);
    }
}

