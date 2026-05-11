package com.fiap.gateway;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.util.Base64;

import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

// Singleton container pattern: POSTGRES is started once in the static initializer and runs
// for the JVM lifetime (Ryuk reaps it at shutdown). Using `@Testcontainers` + `@Container` on
// a static field stops the container at the END of each test class, but later classes still
// see the same static reference — the next start() call leaves them with a dead port mapping.
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)
public abstract class PostgresTestcontainersBase {

    static final PostgreSQLContainer<?> POSTGRES;

    private static final Path JWT_PRIVATE_KEY_PATH;
    private static final Path JWT_PUBLIC_KEY_PATH;

    static {
        POSTGRES =
                new PostgreSQLContainer<>("postgres:16-alpine")
                        .withDatabaseName("gateway_db")
                        .withUsername("gateway_user")
                        .withPassword("gateway_pwd");
        POSTGRES.start();

        try {
            KeyPairGenerator gen = KeyPairGenerator.getInstance("RSA");
            gen.initialize(2048);
            KeyPair kp = gen.generateKeyPair();
            Base64.Encoder pem = Base64.getMimeEncoder(64, "\n".getBytes());
            JWT_PRIVATE_KEY_PATH = Files.createTempFile("fss-it-jwt-", ".pem");
            JWT_PUBLIC_KEY_PATH = Files.createTempFile("fss-it-jwt-pub-", ".pem");
            Files.writeString(
                    JWT_PRIVATE_KEY_PATH,
                    "-----BEGIN PRIVATE KEY-----\n"
                            + pem.encodeToString(kp.getPrivate().getEncoded())
                            + "\n-----END PRIVATE KEY-----\n");
            Files.writeString(
                    JWT_PUBLIC_KEY_PATH,
                    "-----BEGIN PUBLIC KEY-----\n"
                            + pem.encodeToString(kp.getPublic().getEncoded())
                            + "\n-----END PUBLIC KEY-----\n");
            JWT_PRIVATE_KEY_PATH.toFile().deleteOnExit();
            JWT_PUBLIC_KEY_PATH.toFile().deleteOnExit();
        } catch (IOException | java.security.NoSuchAlgorithmException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    @DynamicPropertySource
    static void registerPostgresProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", POSTGRES::getJdbcUrl);
        registry.add("spring.datasource.username", POSTGRES::getUsername);
        registry.add("spring.datasource.password", POSTGRES::getPassword);
        registry.add("gateway.jwt.private-key-path", JWT_PRIVATE_KEY_PATH::toString);
        registry.add("gateway.jwt.public-key-path", JWT_PUBLIC_KEY_PATH::toString);
    }
}
