package com.api.dto;

import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;
import java.util.Map;

@Getter
@Setter
public class BookmarkResponse {
    private Long id;
    private String userId;
    private String recipeId;
    private LocalDateTime createdAt;
    private Map<String, Object> recipe;

    public BookmarkResponse(Long id, String userId, String recipeId, LocalDateTime createdAt, Map<String, Object> recipe) {
        this.id = id;
        this.userId = userId;
        this.recipeId = recipeId;
        this.createdAt = createdAt;
        this.recipe = recipe;
    }
}

