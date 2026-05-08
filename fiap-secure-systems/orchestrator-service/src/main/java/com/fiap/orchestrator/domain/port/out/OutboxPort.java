package com.fiap.orchestrator.domain.port.out;

import com.fiap.orchestrator.domain.model.SessionId;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

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
            String lastError
    ) {}

    void append(SessionId aggregateId, Destination destination, String eventType,
                Map<String, Object> payload, Instant now);

    List<OutboxEntry> fetchUnpublished(int limit);

    void markPublished(UUID id, Instant now);

    void recordFailure(UUID id, String errorMessage);
}
