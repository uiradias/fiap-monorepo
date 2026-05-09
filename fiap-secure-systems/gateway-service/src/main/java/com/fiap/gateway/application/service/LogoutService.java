package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.exception.InvalidTokenException;
import com.fiap.gateway.domain.port.in.LogoutUseCase;
import com.fiap.gateway.domain.port.out.RefreshTokenRepositoryPort;
import com.fiap.gateway.domain.port.out.TokenIssuerPort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class LogoutService implements LogoutUseCase {

    private final RefreshTokenRepositoryPort refreshTokens;
    private final TokenIssuerPort issuer;
    private final Clock clock;

    public LogoutService(RefreshTokenRepositoryPort refreshTokens, TokenIssuerPort issuer, Clock clock) {
        this.refreshTokens = refreshTokens;
        this.issuer = issuer;
        this.clock = clock;
    }

    @Override
    @Transactional
    public void logout(String refreshTokenPlain) {
        var active = refreshTokens.findActiveByHash(issuer.hashRefreshToken(refreshTokenPlain))
                .orElseThrow(() -> new InvalidTokenException("refresh token not found or revoked"));
        refreshTokens.revoke(active.id(), clock.now());
    }
}
