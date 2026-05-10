package com.fiap.orchestrator.domain.model;

import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

public record AnalysisOutcome(
        JobId jobId,
        SessionId sessionId,
        AnalysisStatus status,
        Map<String, Object> result, // null unless SUCCEEDED
        Map<String, Object> modelMetadata, // null unless SUCCEEDED
        AnalysisFailure failure, // null unless FAILED
        Instant completedAt) {
    public AnalysisOutcome {
        Objects.requireNonNull(jobId, "jobId");
        Objects.requireNonNull(sessionId, "sessionId");
        Objects.requireNonNull(status, "status");
        Objects.requireNonNull(completedAt, "completedAt");
        switch (status) {
            case SUCCEEDED -> {
                if (result == null || modelMetadata == null) {
                    throw new IllegalArgumentException(
                            "SUCCEEDED requires result and modelMetadata");
                }
                result = Map.copyOf(result);
                modelMetadata = Map.copyOf(modelMetadata);
            }
            case FAILED -> {
                if (failure == null) {
                    throw new IllegalArgumentException("FAILED requires a failure");
                }
            }
            case STARTED -> {
                if (result != null || modelMetadata != null || failure != null) {
                    throw new IllegalArgumentException("STARTED carries no result/failure");
                }
            }
        }
    }

    /** Convenience: result wrapped in Optional. */
    public Optional<Map<String, Object>> resultOpt() {
        return Optional.ofNullable(result);
    }

    /** Convenience: modelMetadata wrapped in Optional. */
    public Optional<Map<String, Object>> modelMetadataOpt() {
        return Optional.ofNullable(modelMetadata);
    }

    /** Convenience: failure wrapped in Optional. */
    public Optional<AnalysisFailure> failureOpt() {
        return Optional.ofNullable(failure);
    }
}
