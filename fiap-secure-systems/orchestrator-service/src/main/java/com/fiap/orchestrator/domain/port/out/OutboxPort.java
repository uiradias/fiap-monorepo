package com.fiap.orchestrator.domain.port.out;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import com.fiap.orchestrator.domain.model.SessionId;

public interface OutboxPort {

    enum Destination {
        SNS_SESSION_EVENTS,
        SQS_ANALYSIS_JOBS
    }

    record OutboxEntry(
            UUID id,
            SessionId aggregateId,
            Destination destination,
            String eventType,
            Map<String, Object> payload,
            Instant createdAt,
            int attempts,
            String lastError) {}

    void append(
            SessionId aggregateId,
            Destination destination,
            String eventType,
            Map<String, Object> payload,
            Instant now);

    List<OutboxEntry> fetchUnpublished(int limit);

    void markPublished(UUID id, Instant now);

    void recordFailure(UUID id, String errorMessage);

    long countUnpublished();
}
