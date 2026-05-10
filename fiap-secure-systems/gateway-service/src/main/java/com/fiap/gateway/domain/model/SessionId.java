package com.fiap.gateway.domain.model;

import java.util.Objects;
import java.util.UUID;

public record SessionId(UUID value) {
    public SessionId {
        Objects.requireNonNull(value, "value");
    }

    public static SessionId of(String s) {
        return new SessionId(UUID.fromString(s));
    }

    @Override
    public String toString() {
        return value.toString();
    }
}
