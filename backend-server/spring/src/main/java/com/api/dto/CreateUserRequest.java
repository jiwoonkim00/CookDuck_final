package com.api.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class CreateUserRequest {
    private String userId;
    private String email;
    private String password;
    private String name;
    private String grade;
}

