package com.fiap.gateway.domain.model;

import java.util.Set;

public enum ContentType {
    APPLICATION_PDF("application/pdf"),
    IMAGE_PNG("image/png"),
    IMAGE_JPEG("image/jpeg"),
    IMAGE_WEBP("image/webp");

    private static final Set<String> ALLOWED = Set.of(
            APPLICATION_PDF.value, IMAGE_PNG.value, IMAGE_JPEG.value, IMAGE_WEBP.value);

    public final String value;

    ContentType(String value) {
        this.value = value;
    }

    public static ContentType ofLenient(String raw) {
        if (raw == null) throw new IllegalArgumentException("content-type required");
        String trimmed = raw.split(";", 2)[0].trim().toLowerCase();
        if (!ALLOWED.contains(trimmed)) {
            throw new IllegalArgumentException("unsupported content-type: " + raw);
        }
        for (ContentType c : values()) if (c.value.equals(trimmed)) return c;
        throw new IllegalStateException("unreachable");
    }
}
