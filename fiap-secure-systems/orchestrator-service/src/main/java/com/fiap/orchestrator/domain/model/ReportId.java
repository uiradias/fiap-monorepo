package com.fiap.orchestrator.domain.model;

import java.util.Objects;
import java.util.UUID;

public record ReportId(UUID value) {
    public ReportId {
        Objects.requireNonNull(value, "ReportId.value");
    }

    public static ReportId of(UUID value) {
        return new ReportId(value);
    }

    @Override
    public String toString() {
        return value.toString();
    }
}
