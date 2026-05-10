package com.fiap.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

import com.fiap.gateway.infrastructure.config.RateLimitProperties;

@SpringBootApplication
@ConfigurationPropertiesScan(basePackageClasses = RateLimitProperties.class)
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}
