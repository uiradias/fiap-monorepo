package com.fiap.gateway.domain.model;

import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class UserTest {
    @Test
    void newUser_initializes_timestamps_and_keeps_email_normalized() {
        Instant now = Instant.parse("2026-05-09T12:00:00Z");
        User u = User.newUser(
                new UserId(UUID.randomUUID()),
                Email.of("Foo@Bar.com"),
                new PasswordHash("$2a$12$abc"),
                "Foo Bar",
                now);

        assertThat(u.email().value()).isEqualTo("foo@bar.com");
        assertThat(u.createdAt()).isEqualTo(now);
        assertThat(u.updatedAt()).isEqualTo(now);
        assertThat(u.displayName()).isEqualTo("Foo Bar");
    }

    @Test
    void displayName_can_be_null() {
        User u = User.newUser(
                new UserId(UUID.randomUUID()),
                Email.of("a@b.com"),
                new PasswordHash("h"),
                null,
                Instant.now());
        assertThat(u.displayName()).isNull();
    }
}
