package com.api.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class FindPasswordRequest {
    private String userId;
    private String email;
    private String code;
    private String newPassword;
} 