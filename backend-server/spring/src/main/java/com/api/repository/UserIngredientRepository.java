package com.api.repository;

import com.api.entity.UserIngredient;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface UserIngredientRepository extends JpaRepository<UserIngredient, Long> {
    List<UserIngredient> findByUserId(String userId);
    
    List<UserIngredient> findByUserIdAndIngredientType(String userId, String ingredientType);
    
    boolean existsByUserIdAndIngredient(String userId, String ingredient);
    
    @Modifying
    @Query("DELETE FROM UserIngredient u WHERE u.userId = :userId")
    void deleteAllByUserId(@Param("userId") String userId);
    
    @Modifying
    @Query("DELETE FROM UserIngredient u WHERE u.userId = :userId AND u.ingredient = :ingredient")
    void deleteByUserIdAndIngredient(@Param("userId") String userId, @Param("ingredient") String ingredient);
}

