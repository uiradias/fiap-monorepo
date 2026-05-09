package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.exception.InvalidTokenException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.LoginUseCase;
import com.fiap.gateway.domain.port.in.RefreshTokenUseCase;
import com.fiap.gateway.domain.port.out.RefreshTokenRepositoryPort;
import com.fiap.gateway.domain.port.out.TokenIssuerPort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.Instant;
import java.util.UUID;

@Service
public class RefreshTokenService implements RefreshTokenUseCase {

    private static final long ACCESS_TTL_SECONDS = 15L * 60;

    private final RefreshTokenRepositoryPort refreshTokens;
    private final TokenIssuerPort issuer;
    private final Clock clock;
    private final Duration refreshTtl;

    public RefreshTokenService(RefreshTokenRepositoryPort refreshTokens,
                               TokenIssuerPort issuer, Clock clock, Duration refreshTtl) {
        this.refreshTokens = refreshTokens;
        this.issuer = issuer;
        this.clock = clock;
        this.refreshTtl = refreshTtl;
    }

    @Override
    @Transactional
    public LoginUseCase.TokenPair refresh(String refreshTokenPlain) {
        String hash = issuer.hashRefreshToken(refreshTokenPlain);
        RefreshToken active = refreshTokens.findActiveByHash(hash)
                .orElseThrow(() -> new InvalidTokenException("refresh token not found or revoked"));

        Instant now = clock.now();
        refreshTokens.revoke(active.id(), now);

        String newAccess = issuer.issueAccessToken(active.userId(), now);
        String newPlain = issuer.generateRefreshTokenPlaintext();
        refreshTokens.insert(RefreshToken.issue(
                new RefreshTokenId(UUID.randomUUID()), active.userId(),
                issuer.hashRefreshToken(newPlain), now, refreshTtl));

        return new LoginUseCase.TokenPair(newAccess, newPlain, ACCESS_TTL_SECONDS);
    }
}
