package com.fiap.gateway.domain.model;

import java.time.Instant;

public record User(
        UserId id,
        Email email,
        PasswordHash passwordHash,
        String displayName,
        Instant createdAt,
        Instant updatedAt) {

    public static User newUser(
            UserId id, Email email, PasswordHash hash, String displayName, Instant now) {
        return new User(id, email, hash, displayName, now, now);
    }
}
