package com.fiap.gateway.application.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Duration;
import java.time.Instant;
import java.util.UUID;

import org.junit.jupiter.api.Test;

import com.fiap.gateway.domain.exception.InvalidTokenException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.LoginUseCase;

class RefreshTokenServiceTest {

    private final InMemoryFakes.FakeUsers users = new InMemoryFakes.FakeUsers();
    private final Clock clock = () -> Instant.parse("2026-05-09T12:00:00Z");
    private final InMemoryFakes.FakeRefreshTokens tokens =
            new InMemoryFakes.FakeRefreshTokens(clock);
    private final InMemoryFakes.FakeHasher hasher = new InMemoryFakes.FakeHasher();
    private final InMemoryFakes.FakeTokens issuer = new InMemoryFakes.FakeTokens();

    private final LoginService login =
            new LoginService(users, tokens, hasher, issuer, clock, Duration.ofDays(7));
    private final RefreshTokenService refresh =
            new RefreshTokenService(tokens, issuer, clock, Duration.ofDays(7));

    @Test
    void rotates_and_revokes_old_token() {
        UserId uid = new UserId(UUID.randomUUID());
        users.insertOrThrow(
                User.newUser(uid, Email.of("a@b.com"), hasher.hash("p"), null, clock.now()));
        LoginUseCase.TokenPair p1 = login.login(Email.of("a@b.com"), "p");

        LoginUseCase.TokenPair p2 = refresh.refresh(p1.refreshToken());

        assertThat(p2.refreshToken()).isNotEqualTo(p1.refreshToken());
        // old token now revoked; using it again must fail
        assertThatThrownBy(() -> refresh.refresh(p1.refreshToken()))
                .isInstanceOf(InvalidTokenException.class);
    }

    @Test
    void rejects_unknown_token() {
        assertThatThrownBy(() -> refresh.refresh("totally-bogus"))
                .isInstanceOf(InvalidTokenException.class);
    }
}
