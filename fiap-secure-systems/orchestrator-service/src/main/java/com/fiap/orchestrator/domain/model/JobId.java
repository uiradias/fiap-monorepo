package com.fiap.orchestrator.domain.model;

import java.util.Objects;
import java.util.UUID;

public record JobId(UUID value) {
    public JobId {
        Objects.requireNonNull(value, "JobId.value");
    }

    public static JobId of(UUID value) {
        return new JobId(value);
    }

    @Override
    public String toString() {
        return value.toString();
    }
}
