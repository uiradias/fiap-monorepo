package com.fiap.gateway.domain.model;
import java.util.Objects; import java.util.UUID;
public record UserId(UUID value) {
    public UserId { Objects.requireNonNull(value, "value"); }
    public static UserId of(String s) { return new UserId(UUID.fromString(s)); }
    @Override public String toString() { return value.toString(); }
}
