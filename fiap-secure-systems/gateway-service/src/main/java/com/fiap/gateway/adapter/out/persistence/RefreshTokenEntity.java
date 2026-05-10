package com.fiap.gateway.adapter.out.persistence;

import java.time.Instant;
import java.util.UUID;

import jakarta.persistence.*;

@Entity
@Table(name = "refresh_tokens")
public class RefreshTokenEntity {
    @Id public UUID id;

    @Column(name = "user_id", nullable = false)
    public UUID userId;

    @Column(name = "token_hash", nullable = false, unique = true)
    public String tokenHash;

    @Column(name = "expires_at", nullable = false)
    public Instant expiresAt;

    @Column(name = "revoked_at")
    public Instant revokedAt;

    @Column(name = "created_at", nullable = false)
    public Instant createdAt;
}
