package com.fiap.gateway.domain.model;

import java.time.Instant;
import java.util.Optional;

public record SessionSummary(
        SessionId id,
        UserId userId,
        SessionState state,
        int assetCount,
        String failureReason,
        Instant createdAt,
        Instant updatedAt,
        Optional<ReportId> reportId) {}
