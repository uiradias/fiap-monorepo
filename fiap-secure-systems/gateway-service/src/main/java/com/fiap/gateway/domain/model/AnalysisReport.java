package com.fiap.gateway.domain.model;

import java.time.Instant;
import java.util.Map;
import java.util.Objects;

public record AnalysisReport(
        ReportId id,
        SessionId sessionId,
        String summary,
        String confidence,
        Map<String, Object> payload,
        Map<String, Object> modelMetadata,
        Instant createdAt) {

    public AnalysisReport {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(sessionId, "sessionId");
        Objects.requireNonNull(summary, "summary");
        Objects.requireNonNull(confidence, "confidence");
        Objects.requireNonNull(payload, "payload");
        Objects.requireNonNull(modelMetadata, "modelMetadata");
        Objects.requireNonNull(createdAt, "createdAt");
    }
}
