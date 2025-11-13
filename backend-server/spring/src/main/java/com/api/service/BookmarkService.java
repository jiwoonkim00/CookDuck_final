package com.api.service;

import com.api.entity.Bookmark;
import com.api.repository.BookmarkRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional
public class BookmarkService {
    private final BookmarkRepository bookmarkRepository;

    public void addBookmark(String userId, String recipeId) {
        // 이미 북마크되어 있는지 확인
        if (bookmarkRepository.existsByUserIdAndRecipeId(userId, recipeId)) {
            throw new IllegalArgumentException("이미 북마크된 레시피입니다.");
        }

        Bookmark bookmark = new Bookmark();
        bookmark.setUserId(userId);
        bookmark.setRecipeId(recipeId);
        bookmarkRepository.save(bookmark);
    }

    public void removeBookmark(String userId, String recipeId) {
        Bookmark bookmark = bookmarkRepository.findByUserIdAndRecipeId(userId, recipeId)
                .orElseThrow(() -> new IllegalArgumentException("북마크가 존재하지 않습니다."));

        bookmarkRepository.delete(bookmark);
    }

    public List<Bookmark> getBookmarks(String userId) {
        return bookmarkRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    public boolean isBookmarked(String userId, String recipeId) {
        return bookmarkRepository.existsByUserIdAndRecipeId(userId, recipeId);
    }
}

