package com.fiap.gateway.domain.model;

import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

public record SessionEventLogEntry(
        EventId eventId,
        SessionId sessionId,
        UserId userId,
        SessionState fromState,        // null on the very first event
        SessionState toState,
        Map<String, Object> payload,
        Instant occurredAt,
        Instant receivedAt) {

    public SessionEventLogEntry {
        Objects.requireNonNull(eventId, "eventId");
        Objects.requireNonNull(sessionId, "sessionId");
        Objects.requireNonNull(userId, "userId");
        Objects.requireNonNull(toState, "toState");
        Objects.requireNonNull(payload, "payload");
        Objects.requireNonNull(occurredAt, "occurredAt");
        Objects.requireNonNull(receivedAt, "receivedAt");
    }

    public Optional<SessionState> fromStateOpt() {
        return Optional.ofNullable(fromState);
    }
}
