package com.fiap.gateway.adapter.out.persistence;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import com.fiap.gateway.PostgresTestcontainersBase;
import com.fiap.gateway.domain.exception.DuplicateEmailException;
import com.fiap.gateway.domain.model.*;

class UserRepositoryIT extends PostgresTestcontainersBase {

    @Autowired UserRepositoryAdapter users;

    @Test
    void inserts_and_finds_by_email() {
        User u =
                User.newUser(
                        new UserId(UUID.randomUUID()),
                        Email.of("a@b.com"),
                        new PasswordHash("$2a$12$x"),
                        "Alice",
                        Instant.parse("2026-05-09T12:00:00Z"));
        users.insertOrThrow(u);
        assertThat(users.findByEmail(Email.of("A@B.COM"))).isPresent();
    }

    @Test
    void rejects_duplicate_email() {
        User u =
                User.newUser(
                        new UserId(UUID.randomUUID()),
                        Email.of("dup@example.com"),
                        new PasswordHash("$2a$12$x"),
                        null,
                        Instant.now());
        users.insertOrThrow(u);

        User u2 =
                User.newUser(
                        new UserId(UUID.randomUUID()),
                        Email.of("dup@example.com"),
                        new PasswordHash("$2a$12$y"),
                        null,
                        Instant.now());
        assertThatThrownBy(() -> users.insertOrThrow(u2))
                .isInstanceOf(DuplicateEmailException.class);
    }
}
