package com.fiap.gateway.adapter.out.persistence;

import java.time.Instant;
import java.util.Optional;

import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.out.RefreshTokenRepositoryPort;

@Repository
public class RefreshTokenRepositoryAdapter implements RefreshTokenRepositoryPort {

    private final RefreshTokenJpaRepository repo;

    public RefreshTokenRepositoryAdapter(RefreshTokenJpaRepository repo) {
        this.repo = repo;
    }

    @Override
    @Transactional
    public RefreshToken insert(RefreshToken token) {
        RefreshTokenEntity e = new RefreshTokenEntity();
        e.id = token.id().value();
        e.userId = token.userId().value();
        e.tokenHash = token.tokenHash();
        e.expiresAt = token.expiresAt();
        e.revokedAt = token.revokedAt();
        e.createdAt = token.createdAt();
        repo.save(e);
        return token;
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<RefreshToken> findActiveByHash(String tokenHash) {
        return repo.findByTokenHash(tokenHash)
                .filter(e -> e.revokedAt == null && e.expiresAt.isAfter(Instant.now()))
                .map(this::toDomain);
    }

    @Override
    @Transactional
    public void revoke(RefreshTokenId id, Instant now) {
        repo.revokeById(id.value(), now);
    }

    @Override
    @Transactional
    public void revokeAllForUser(UserId userId, Instant now) {
        repo.revokeAllForUser(userId.value(), now);
    }

    private RefreshToken toDomain(RefreshTokenEntity e) {
        return new RefreshToken(
                new RefreshTokenId(e.id),
                new UserId(e.userId),
                e.tokenHash,
                e.expiresAt,
                e.createdAt,
                e.revokedAt);
    }
}
