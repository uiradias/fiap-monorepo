package com.fiap.gateway.domain.model;

import java.util.Objects;

public record PasswordHash(String value) {
    public PasswordHash {
        Objects.requireNonNull(value, "value");
        if (value.isBlank()) throw new IllegalArgumentException("hash required");
    }

    @Override
    public String toString() {
        return "PasswordHash{***}";
    } // never log the hash
}
