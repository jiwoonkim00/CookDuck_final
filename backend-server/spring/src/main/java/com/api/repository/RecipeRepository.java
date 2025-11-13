package com.api.repository;

import com.api.entity.Recipe;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface RecipeRepository extends JpaRepository<Recipe, Long> {
    List<Recipe> findByCuisine(String cuisine);
    List<Recipe> findByCuisineContaining(String cuisine);
    List<Recipe> findTop50ByTitleContainingIgnoreCaseOrSummaryContainingIgnoreCaseOrIngredientsContainingIgnoreCase(
        String titleKeyword,
        String summaryKeyword,
        String ingredientsKeyword
    );
}

