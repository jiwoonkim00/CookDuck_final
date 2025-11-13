package com.api.repository;

import com.api.entity.Bookmark;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface BookmarkRepository extends JpaRepository<Bookmark, Long> {
    boolean existsByUserIdAndRecipeId(String userId, String recipeId);
    Optional<Bookmark> findByUserIdAndRecipeId(String userId, String recipeId);
    List<Bookmark> findByUserIdOrderByCreatedAtDesc(String userId);
    void deleteByUserIdAndRecipeId(String userId, String recipeId);
    void deleteByUserId(String userId);
}

