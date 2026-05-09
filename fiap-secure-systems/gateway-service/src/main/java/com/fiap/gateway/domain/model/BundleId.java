package com.fiap.gateway.domain.model;
import java.util.Objects; import java.util.UUID;
public record BundleId(UUID value) {
    public BundleId { Objects.requireNonNull(value, "value"); }
    public static BundleId of(String s) { return new BundleId(UUID.fromString(s)); }
    @Override public String toString() { return value.toString(); }
}
