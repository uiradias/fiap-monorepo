package com.fiap.gateway.infrastructure.schema;

import org.junit.jupiter.api.Test;

import java.io.File;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ContractValidatorTest {

    private final ContractValidator validator = new ContractValidator(
            new File("../infrastructure/contracts").getAbsoluteFile());

    @Test
    void accepts_a_minimal_valid_session_event() {
        Map<String, Object> body = Map.of(
                "schemaVersion", 1,
                "eventId", UUID.randomUUID().toString(),
                "sessionId", UUID.randomUUID().toString(),
                "userId", UUID.randomUUID().toString(),
                "fromState", "ASSETS_UPLOADED",
                "toState", "QUEUED_FOR_ANALYSIS",
                "payload", Map.of(),
                "occurredAt", Instant.now().toString());
        validator.validateSessionEvent(body);
    }

    @Test
    void rejects_unknown_toState() {
        Map<String, Object> body = Map.of(
                "schemaVersion", 1,
                "eventId", UUID.randomUUID().toString(),
                "sessionId", UUID.randomUUID().toString(),
                "userId", UUID.randomUUID().toString(),
                "toState", "BOGUS",
                "occurredAt", Instant.now().toString());
        assertThatThrownBy(() -> validator.validateSessionEvent(body))
                .isInstanceOf(InvalidPayloadException.class);
    }

    @Test
    void rejects_missing_required_field() {
        Map<String, Object> body = Map.of(
                "schemaVersion", 1,
                "eventId", UUID.randomUUID().toString(),
                "sessionId", UUID.randomUUID().toString(),
                "occurredAt", Instant.now().toString());
        assertThat(catchExceptionFor(body)).isInstanceOf(InvalidPayloadException.class);
    }

    private static Throwable catchExceptionFor(Map<String, Object> body) {
        try {
            new ContractValidator(new File("../infrastructure/contracts").getAbsoluteFile())
                    .validateSessionEvent(body);
            return null;
        } catch (Throwable t) { return t; }
    }
}
