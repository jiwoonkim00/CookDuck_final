package com.api.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UserInfoResponse {
    private String userId;
    private String email;
    private String name;
    private String grade;
    
    public UserInfoResponse(String userId, String email, String name, String grade) {
        this.userId = userId;
        this.email = email;
        this.name = name;
        this.grade = grade;
    }
} 