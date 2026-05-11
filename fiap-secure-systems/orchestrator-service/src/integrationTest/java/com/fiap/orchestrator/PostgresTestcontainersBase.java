package com.fiap.orchestrator;

import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

// Singleton container pattern: POSTGRES is started once in the static initializer and runs for
// the JVM lifetime (Ryuk reaps it at shutdown). Using `@Testcontainers` + `@Container` on a
// static field stops the container at the END of each test class, but later classes still see
// the same static reference — the next start() call leaves them with a dead port mapping.
@SpringBootTest(
        classes = OrchestratorApplication.class,
        webEnvironment = SpringBootTest.WebEnvironment.NONE)
public abstract class PostgresTestcontainersBase {

    static final PostgreSQLContainer<?> POSTGRES;

    static {
        POSTGRES =
                new PostgreSQLContainer<>("postgres:16-alpine")
                        .withDatabaseName("orchestrator_db")
                        .withUsername("orchestrator_user")
                        .withPassword("orchestrator_pwd");
        POSTGRES.start();
    }

    @DynamicPropertySource
    static void registerPgProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("spring.jpa.hibernate.ddl-auto", () -> "validate");
        registry.add("spring.flyway.enabled", () -> "true");
    }
}
