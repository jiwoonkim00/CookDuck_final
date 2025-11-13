package com.api.cookduck;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@OpenAPIDefinition(
	info = @Info(
		title = "COOKDUCK API",
		description = "Spring Boot로 구현한 회원가입 API",
		version = "v1.0.0"
	)
)
@SpringBootApplication
@ComponentScan(basePackages = "com.api")
@EntityScan("com.api.entity")
@EnableJpaRepositories("com.api.repository")
public class CookduckApplication {

	public static void main(String[] args) {
		SpringApplication.run(CookduckApplication.class, args);
	}

}
