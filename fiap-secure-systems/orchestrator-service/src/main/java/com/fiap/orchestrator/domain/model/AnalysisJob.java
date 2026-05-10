package com.fiap.orchestrator.domain.model;

import java.time.Instant;
import java.util.List;
import java.util.Objects;

public record AnalysisJob(
        JobId jobId,
        SessionId sessionId,
        UserId userId,
        List<AssetRef> assets,
        String promptVersion,
        Instant submittedAt) {
    public AnalysisJob {
        Objects.requireNonNull(jobId, "jobId");
        Objects.requireNonNull(sessionId, "sessionId");
        Objects.requireNonNull(userId, "userId");
        Objects.requireNonNull(assets, "assets");
        Objects.requireNonNull(promptVersion, "promptVersion");
        Objects.requireNonNull(submittedAt, "submittedAt");
        if (assets.isEmpty() || assets.size() > 20) {
            throw new IllegalArgumentException("assets must have 1..20 elements");
        }
        assets = List.copyOf(assets);
    }
}
