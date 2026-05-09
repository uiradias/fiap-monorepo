package com.fiap.gateway.domain.port.out;

import com.fiap.gateway.domain.model.*;

import java.util.Optional;

public interface RefreshTokenRepositoryPort {
    RefreshToken insert(RefreshToken token);
    Optional<RefreshToken> findActiveByHash(String tokenHash);
    void revoke(RefreshTokenId id, java.time.Instant now);
    void revokeAllForUser(UserId userId, java.time.Instant now);
}
