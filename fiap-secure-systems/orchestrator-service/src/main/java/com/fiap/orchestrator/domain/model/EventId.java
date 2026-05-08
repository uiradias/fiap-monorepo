package com.fiap.orchestrator.domain.model;

import java.util.Objects;
import java.util.UUID;

public record EventId(UUID value) {
    public EventId {
        Objects.requireNonNull(value, "EventId.value");
    }
    public static EventId of(UUID value) { return new EventId(value); }
    @Override public String toString() { return value.toString(); }
}
