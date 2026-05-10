package com.fiap.gateway.application.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;

import org.junit.jupiter.api.Test;

import com.fiap.gateway.domain.exception.DuplicateEmailException;
import com.fiap.gateway.domain.model.*;

class RegisterUserServiceTest {

    private final InMemoryFakes.FakeUsers users = new InMemoryFakes.FakeUsers();
    private final InMemoryFakes.FakeHasher hasher = new InMemoryFakes.FakeHasher();
    private final RegisterUserService svc =
            new RegisterUserService(users, hasher, () -> Instant.parse("2026-05-09T12:00:00Z"));

    @Test
    void registers_a_new_user_with_hashed_password() {
        User u = svc.register(Email.of("Foo@Bar.com"), "hunter2!", "Foo");
        assertThat(u.email().value()).isEqualTo("foo@bar.com");
        assertThat(u.passwordHash().value()).isEqualTo("hash:hunter2!");
        assertThat(u.displayName()).isEqualTo("Foo");
    }

    @Test
    void rejects_duplicate_email() {
        svc.register(Email.of("a@b.com"), "password1", null);
        assertThatThrownBy(() -> svc.register(Email.of("a@b.com"), "password2", null))
                .isInstanceOf(DuplicateEmailException.class);
    }
}
