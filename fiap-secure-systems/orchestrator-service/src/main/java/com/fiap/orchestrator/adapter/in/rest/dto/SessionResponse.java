package com.fiap.orchestrator.adapter.in.rest.dto;

import java.time.Instant;
import java.util.UUID;

import com.fiap.orchestrator.domain.model.Session;

public record SessionResponse(
        UUID sessionId,
        UUID userId,
        String state,
        int assetCount,
        String failureReason,
        Instant createdAt,
        Instant updatedAt,
        long version) {
    public static SessionResponse from(Session s) {
        return new SessionResponse(
                s.id().value(),
                s.userId().value(),
                s.state().name(),
                s.assetCount(),
                s.failureReason(),
                s.createdAt(),
                s.updatedAt(),
                s.version());
    }
}
