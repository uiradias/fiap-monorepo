package com.fiap.orchestrator.adapter.in.rest.dto;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import com.fiap.orchestrator.domain.model.AnalysisReport;

public record ReportResponse(
        UUID reportId,
        UUID sessionId,
        String summary,
        String confidence,
        Map<String, Object> payload,
        Map<String, Object> modelMetadata,
        Instant createdAt) {
    public static ReportResponse from(AnalysisReport r) {
        return new ReportResponse(
                r.id().value(),
                r.sessionId().value(),
                r.summary(),
                r.confidence(),
                r.payload(),
                r.modelMetadata(),
                r.createdAt());
    }
}
