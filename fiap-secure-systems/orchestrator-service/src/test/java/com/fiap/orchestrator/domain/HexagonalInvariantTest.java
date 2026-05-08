package com.fiap.orchestrator.domain;

import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.assertThat;

class HexagonalInvariantTest {

    private static final List<String> FORBIDDEN_PREFIXES = List.of(
            "import org.springframework",
            "import org.hibernate",
            "import jakarta.persistence",
            "import jakarta.servlet",
            "import software.amazon.awssdk",
            "import com.fasterxml.jackson"
    );

    @Test
    void domain_classes_have_no_framework_imports() throws IOException {
        Path domainRoot = Path.of("src/main/java/com/fiap/orchestrator/domain");
        try (Stream<Path> files = Files.walk(domainRoot)) {
            files.filter(p -> p.toString().endsWith(".java")).forEach(p -> {
                String src;
                try {
                    src = Files.readString(p);
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
                for (String forbidden : FORBIDDEN_PREFIXES) {
                    assertThat(src)
                            .as("domain file %s must not contain '%s'", p, forbidden)
                            .doesNotContain(forbidden);
                }
            });
        }
    }
}
