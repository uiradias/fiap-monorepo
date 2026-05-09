package com.fiap.gateway.domain.model;
import java.util.Objects; import java.util.UUID;
public record RefreshTokenId(UUID value) {
    public RefreshTokenId { Objects.requireNonNull(value, "value"); }
    public static RefreshTokenId of(String s) { return new RefreshTokenId(UUID.fromString(s)); }
    @Override public String toString() { return value.toString(); }
}
