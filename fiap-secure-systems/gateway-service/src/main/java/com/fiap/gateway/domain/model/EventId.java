package com.fiap.gateway.domain.model;

import java.util.Objects;
import java.util.UUID;

public record EventId(UUID value) {
    public EventId {
        Objects.requireNonNull(value, "value");
    }

    public static EventId of(String s) {
        return new EventId(UUID.fromString(s));
    }

    @Override
    public String toString() {
        return value.toString();
    }
}
