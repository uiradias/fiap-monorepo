package com.fiap.gateway.domain.model;

import java.util.Objects;
import java.util.UUID;

public record AssetId(UUID value) {
    public AssetId {
        Objects.requireNonNull(value, "value");
    }

    public static AssetId of(String s) {
        return new AssetId(UUID.fromString(s));
    }

    @Override
    public String toString() {
        return value.toString();
    }
}
