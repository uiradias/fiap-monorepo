package com.fiap.gateway.domain.model;

import java.util.Objects;

public record Email(String value) {
    public Email {
        Objects.requireNonNull(value, "value");
    }

    public static Email of(String raw) {
        if (raw == null) throw new IllegalArgumentException("email required");
        String normalized = raw.trim().toLowerCase();
        if (normalized.isEmpty()) throw new IllegalArgumentException("email required");
        if (!normalized.contains("@") || normalized.indexOf('@') != normalized.lastIndexOf('@')
                || normalized.startsWith("@") || normalized.endsWith("@")) {
            throw new IllegalArgumentException("email must contain exactly one @ between non-empty parts");
        }
        return new Email(normalized);
    }

    @Override
    public String toString() {
        return value;
    }
}
