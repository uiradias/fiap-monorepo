package com.fiap.gateway.adapter.in.rest.dto;

import com.fiap.gateway.domain.model.AnalysisReport;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public record ReportResponse(
        UUID id, UUID sessionId, String summary, String confidence,
        Map<String, Object> payload, Map<String, Object> modelMetadata, Instant createdAt) {
    public static ReportResponse of(AnalysisReport r) {
        return new ReportResponse(r.id().value(), r.sessionId().value(),
                r.summary(), r.confidence(), r.payload(), r.modelMetadata(), r.createdAt());
    }
}
