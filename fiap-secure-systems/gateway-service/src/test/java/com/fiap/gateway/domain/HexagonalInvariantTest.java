package com.fiap.gateway.domain;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;

import org.junit.jupiter.api.Test;

class HexagonalInvariantTest {

    private static final List<String> FORBIDDEN_PREFIXES =
            List.of(
                    "import org.springframework.",
                    "import jakarta.persistence.",
                    "import jakarta.servlet.",
                    "import com.fasterxml.jackson.",
                    "import software.amazon.awssdk.",
                    "import com.auth0.jwt.",
                    "import io.micrometer.",
                    "import io.opentelemetry.");

    @Test
    void domain_has_no_framework_imports() throws IOException {
        Path root = Path.of("src/main/java/com/fiap/gateway/domain");
        try (Stream<Path> walk = Files.walk(root)) {
            walk.filter(p -> p.toString().endsWith(".java"))
                    .forEach(
                            p -> {
                                try {
                                    List<String> lines = Files.readAllLines(p);
                                    for (String line : lines) {
                                        for (String forbidden : FORBIDDEN_PREFIXES) {
                                            assertThat(line.startsWith(forbidden))
                                                    .as("forbidden import in %s: %s", p, line)
                                                    .isFalse();
                                        }
                                    }
                                } catch (IOException e) {
                                    throw new RuntimeException(e);
                                }
                            });
        }
    }
}
