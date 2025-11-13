package com.api.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;

@Entity
@Table(name = "user_seasoning_pivot")
@Getter
@Setter
public class UserSeasoningPivot {
    @Id
    private String userId;

    private boolean 간장;
    private boolean 된장;
    private boolean 고추장;
    private boolean 소금;
    private boolean 후추;
    private boolean 설탕;
    private boolean 고춧가루;
    private boolean 식초;
    private boolean 참기름;
} 