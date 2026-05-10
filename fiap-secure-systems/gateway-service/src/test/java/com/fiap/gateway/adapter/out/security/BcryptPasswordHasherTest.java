package com.fiap.gateway.adapter.out.security;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

import com.fiap.gateway.domain.model.PasswordHash;

class BcryptPasswordHasherTest {

    private final BcryptPasswordHasher hasher = new BcryptPasswordHasher();

    @Test
    void hashes_round_trip() {
        PasswordHash h = hasher.hash("hunter2");
        assertThat(hasher.matches("hunter2", h)).isTrue();
    }

    @Test
    void rejects_wrong_password() {
        PasswordHash h = hasher.hash("hunter2");
        assertThat(hasher.matches("HUNTER2", h)).isFalse();
        assertThat(hasher.matches("", h)).isFalse();
    }

    @Test
    void hash_uses_cost_12() {
        PasswordHash h = hasher.hash("x");
        // bcrypt format: $2a$12$...
        assertThat(h.value()).startsWith("$2a$12$");
    }
}
