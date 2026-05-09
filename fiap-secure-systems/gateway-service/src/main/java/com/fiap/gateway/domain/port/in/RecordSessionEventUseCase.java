package com.fiap.gateway.domain.port.in;

import com.fiap.gateway.domain.model.*;

import java.time.Instant;
import java.util.Map;

public interface RecordSessionEventUseCase {
    /**
     * Idempotent on eventId. Returns true if the event was newly recorded;
     * false if it was a duplicate (already in session_event_log).
     */
    boolean record(EventId eventId, SessionId sessionId, UserId userId,
                   SessionState fromState, SessionState toState,
                   Map<String, Object> payload, Instant occurredAt, Instant receivedAt);
}
