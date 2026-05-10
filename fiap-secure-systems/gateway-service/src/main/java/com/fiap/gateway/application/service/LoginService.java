package com.fiap.gateway.application.service;

import java.time.Duration;
import java.time.Instant;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.exception.InvalidCredentialsException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.LoginUseCase;
import com.fiap.gateway.domain.port.out.*;

@Service
public class LoginService implements LoginUseCase {

    private static final long ACCESS_TTL_SECONDS = 15L * 60;

    private final UserRepositoryPort users;
    private final RefreshTokenRepositoryPort refreshTokens;
    private final PasswordHasherPort hasher;
    private final TokenIssuerPort issuer;
    private final Clock clock;
    private final Duration refreshTtl;

    public LoginService(
            UserRepositoryPort users,
            RefreshTokenRepositoryPort refreshTokens,
            PasswordHasherPort hasher,
            TokenIssuerPort issuer,
            Clock clock,
            Duration refreshTtl) {
        this.users = users;
        this.refreshTokens = refreshTokens;
        this.hasher = hasher;
        this.issuer = issuer;
        this.clock = clock;
        this.refreshTtl = refreshTtl;
    }

    @Override
    @Transactional
    public TokenPair login(Email email, String plaintextPassword) {
        User u = users.findByEmail(email).orElseThrow(InvalidCredentialsException::new);
        if (!hasher.matches(plaintextPassword, u.passwordHash())) {
            throw new InvalidCredentialsException();
        }
        Instant now = clock.now();

        String accessJws = issuer.issueAccessToken(u.id(), now);
        String refreshPlain = issuer.generateRefreshTokenPlaintext();
        String refreshHash = issuer.hashRefreshToken(refreshPlain);
        refreshTokens.insert(
                RefreshToken.issue(
                        new RefreshTokenId(UUID.randomUUID()),
                        u.id(),
                        refreshHash,
                        now,
                        refreshTtl));

        return new TokenPair(accessJws, refreshPlain, ACCESS_TTL_SECONDS);
    }
}
