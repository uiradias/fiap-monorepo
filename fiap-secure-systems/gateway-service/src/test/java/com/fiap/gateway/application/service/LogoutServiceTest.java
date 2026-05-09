package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.exception.InvalidTokenException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.LoginUseCase;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.time.Instant;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

class LogoutServiceTest {

    private final InMemoryFakes.FakeUsers users = new InMemoryFakes.FakeUsers();
    private final Clock clock = () -> Instant.parse("2026-05-09T12:00:00Z");
    private final InMemoryFakes.FakeRefreshTokens tokens = new InMemoryFakes.FakeRefreshTokens(clock);
    private final InMemoryFakes.FakeHasher hasher = new InMemoryFakes.FakeHasher();
    private final InMemoryFakes.FakeTokens issuer = new InMemoryFakes.FakeTokens();

    private final LoginService login = new LoginService(users, tokens, hasher, issuer, clock,
            Duration.ofDays(7));
    private final LogoutService logout = new LogoutService(tokens, issuer, clock);
    private final RefreshTokenService refresh = new RefreshTokenService(tokens, issuer, clock,
            Duration.ofDays(7));

    @Test
    void logout_revokes_token_so_refresh_fails() {
        UserId uid = new UserId(UUID.randomUUID());
        users.insertOrThrow(User.newUser(uid, Email.of("a@b.com"),
                hasher.hash("p"), null, clock.now()));
        LoginUseCase.TokenPair pair = login.login(Email.of("a@b.com"), "p");

        logout.logout(pair.refreshToken());

        // after logout the token is revoked; refresh must fail
        assertThatThrownBy(() -> refresh.refresh(pair.refreshToken()))
                .isInstanceOf(InvalidTokenException.class);
    }
}
