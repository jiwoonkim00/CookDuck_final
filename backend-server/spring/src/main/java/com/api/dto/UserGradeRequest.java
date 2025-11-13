package com.api.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UserGradeRequest {
    private String userId;
    private String grade; // "초보", "중급", "고급", "마스터"
} 