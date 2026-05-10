package com.fiap.orchestrator;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;
import org.springframework.scheduling.annotation.EnableScheduling;

import com.fiap.orchestrator.infrastructure.config.OutboxRelayProperties;

@SpringBootApplication
@EnableScheduling
@ConfigurationPropertiesScan(basePackageClasses = OutboxRelayProperties.class)
public class OrchestratorApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrchestratorApplication.class, args);
    }
}
