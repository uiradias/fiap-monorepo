package com.fiap.gateway.adapter.in.rest.dto;

import java.time.Instant;
import java.util.UUID;

import com.fiap.gateway.domain.model.SessionSummary;

public record SessionSummaryResponse(
        UUID id,
        UUID userId,
        String state,
        int assetCount,
        String failureReason,
        Instant createdAt,
        Instant updatedAt,
        UUID reportId) {
    public static SessionSummaryResponse of(SessionSummary s) {
        return new SessionSummaryResponse(
                s.id().value(),
                s.userId().value(),
                s.state().name(),
                s.assetCount(),
                s.failureReason(),
                s.createdAt(),
                s.updatedAt(),
                s.reportId().map(r -> r.value()).orElse(null));
    }
}
