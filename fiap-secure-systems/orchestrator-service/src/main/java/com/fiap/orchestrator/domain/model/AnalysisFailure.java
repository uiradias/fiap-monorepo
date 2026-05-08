package com.fiap.orchestrator.domain.model;

import java.util.Objects;

public record AnalysisFailure(String code, String message) {
    public AnalysisFailure {
        Objects.requireNonNull(code, "code");
        Objects.requireNonNull(message, "message");
        if (code.isBlank() || message.isBlank()) {
            throw new IllegalArgumentException("code and message must be non-blank");
        }
    }
}
