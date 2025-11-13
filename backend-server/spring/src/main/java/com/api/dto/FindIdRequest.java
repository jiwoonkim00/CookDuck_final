package com.api.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class FindIdRequest {
    private String name;
    private String email;
    private String code;
} 