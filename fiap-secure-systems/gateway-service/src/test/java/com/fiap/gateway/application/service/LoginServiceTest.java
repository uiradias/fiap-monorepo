package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.exception.InvalidCredentialsException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.LoginUseCase;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.time.Instant;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class LoginServiceTest {

    private final InMemoryFakes.FakeUsers users = new InMemoryFakes.FakeUsers();
    private final Clock clock = () -> Instant.parse("2026-05-09T12:00:00Z");
    private final InMemoryFakes.FakeRefreshTokens tokens = new InMemoryFakes.FakeRefreshTokens(clock);
    private final InMemoryFakes.FakeHasher hasher = new InMemoryFakes.FakeHasher();
    private final InMemoryFakes.FakeTokens issuer = new InMemoryFakes.FakeTokens();

    private final LoginService svc = new LoginService(users, tokens, hasher, issuer, clock,
            Duration.ofDays(7));

    @Test
    void issues_token_pair_on_correct_password() {
        UserId uid = new UserId(UUID.randomUUID());
        users.insertOrThrow(User.newUser(uid, Email.of("a@b.com"),
                hasher.hash("hunter2"), null, clock.now()));

        LoginUseCase.TokenPair pair = svc.login(Email.of("A@B.com"), "hunter2");
        assertThat(pair.accessToken()).startsWith("access:");
        assertThat(pair.refreshToken()).startsWith("refresh:");
        assertThat(pair.expiresInSeconds()).isEqualTo(15 * 60);
        assertThat(tokens.byId).hasSize(1);
    }

    @Test
    void rejects_wrong_password() {
        UserId uid = new UserId(UUID.randomUUID());
        users.insertOrThrow(User.newUser(uid, Email.of("a@b.com"),
                hasher.hash("hunter2"), null, clock.now()));
        assertThatThrownBy(() -> svc.login(Email.of("a@b.com"), "WRONG"))
                .isInstanceOf(InvalidCredentialsException.class);
    }

    @Test
    void rejects_unknown_user() {
        assertThatThrownBy(() -> svc.login(Email.of("nope@b.com"), "x"))
                .isInstanceOf(InvalidCredentialsException.class);
    }
}
