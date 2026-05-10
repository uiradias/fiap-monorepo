package com.fiap.orchestrator.domain.model;

import java.util.Objects;
import java.util.UUID;

public record SessionId(UUID value) {
    public SessionId {
        Objects.requireNonNull(value, "SessionId.value");
    }

    public static SessionId of(UUID value) {
        return new SessionId(value);
    }

    @Override
    public String toString() {
        return value.toString();
    }
}
