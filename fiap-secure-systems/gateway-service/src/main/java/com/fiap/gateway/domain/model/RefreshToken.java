package com.fiap.gateway.domain.model;

import java.time.Instant;
import java.util.Objects;
import java.util.Optional;

public record RefreshToken(
        RefreshTokenId id,
        UserId userId,
        String tokenHash,
        Instant expiresAt,
        Instant createdAt,
        Instant revokedAt) {

    public RefreshToken {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(userId, "userId");
        Objects.requireNonNull(tokenHash, "tokenHash");
        Objects.requireNonNull(expiresAt, "expiresAt");
        Objects.requireNonNull(createdAt, "createdAt");
    }

    public static RefreshToken issue(
            RefreshTokenId id,
            UserId userId,
            String tokenHash,
            Instant now,
            java.time.Duration ttl) {
        return new RefreshToken(id, userId, tokenHash, now.plus(ttl), now, null);
    }

    public RefreshToken revoke(Instant now) {
        return new RefreshToken(id, userId, tokenHash, expiresAt, createdAt, now);
    }

    public boolean isActive(Instant now) {
        return revokedAt == null && now.isBefore(expiresAt);
    }

    public Optional<Instant> revokedAtOpt() {
        return Optional.ofNullable(revokedAt);
    }
}
