package com.fiap.orchestrator.domain.model;

import java.time.Instant;
import java.util.Map;
import java.util.Objects;

public record SessionEvent(
        EventId id,
        SessionId sessionId,
        SessionState fromState, // null for the initial event
        SessionState toState,
        Map<String, Object> payload,
        Instant occurredAt) {
    public SessionEvent {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(sessionId, "sessionId");
        Objects.requireNonNull(toState, "toState");
        Objects.requireNonNull(payload, "payload");
        Objects.requireNonNull(occurredAt, "occurredAt");
        payload = Map.copyOf(payload);
    }

    public static SessionEvent initial(
            EventId id,
            SessionId sessionId,
            SessionState toState,
            Map<String, Object> payload,
            Instant occurredAt) {
        return new SessionEvent(id, sessionId, null, toState, payload, occurredAt);
    }

    public static SessionEvent transition(
            EventId id,
            SessionId sessionId,
            SessionState fromState,
            SessionState toState,
            Map<String, Object> payload,
            Instant occurredAt) {
        Objects.requireNonNull(fromState, "fromState (use initial() for null)");
        if (fromState == toState) {
            throw new IllegalArgumentException(
                    "transition must change state (got " + fromState + " → " + toState + ")");
        }
        return new SessionEvent(id, sessionId, fromState, toState, payload, occurredAt);
    }
}
