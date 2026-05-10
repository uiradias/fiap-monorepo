package com.fiap.gateway.domain.port.out;

import java.util.Optional;

import com.fiap.gateway.domain.model.*;

public interface RefreshTokenRepositoryPort {
    RefreshToken insert(RefreshToken token);

    Optional<RefreshToken> findActiveByHash(String tokenHash);

    void revoke(RefreshTokenId id, java.time.Instant now);

    void revokeAllForUser(UserId userId, java.time.Instant now);
}
