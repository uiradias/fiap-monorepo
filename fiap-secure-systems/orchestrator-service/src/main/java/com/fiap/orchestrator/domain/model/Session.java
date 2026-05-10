package com.fiap.orchestrator.domain.model;

import java.time.Instant;
import java.util.Objects;

public record Session(
        SessionId id,
        UserId userId,
        SessionState state,
        int assetCount,
        String failureReason,
        Instant createdAt,
        Instant updatedAt,
        long version) {
    public Session {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(userId, "userId");
        Objects.requireNonNull(state, "state");
        Objects.requireNonNull(createdAt, "createdAt");
        Objects.requireNonNull(updatedAt, "updatedAt");
        if (assetCount <= 0) {
            throw new IllegalArgumentException("assetCount must be > 0 (was " + assetCount + ")");
        }
        if (version < 0) {
            throw new IllegalArgumentException("version must be >= 0");
        }
    }

    public static Session newSession(SessionId id, UserId userId, int assetCount, Instant now) {
        return new Session(
                id, userId, SessionState.ASSETS_UPLOADED, assetCount, null, now, now, 0L);
    }

    public Session withState(SessionState next, Instant now) {
        return new Session(id, userId, next, assetCount, null, createdAt, now, version + 1);
    }

    public Session withFailure(SessionState terminal, String reason, Instant now) {
        if (terminal != SessionState.FAILED && terminal != SessionState.CANCELED) {
            throw new IllegalArgumentException("withFailure requires FAILED or CANCELED");
        }
        return new Session(id, userId, terminal, assetCount, reason, createdAt, now, version + 1);
    }
}
