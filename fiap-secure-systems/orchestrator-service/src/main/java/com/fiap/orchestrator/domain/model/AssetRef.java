package com.fiap.orchestrator.domain.model;

import java.util.Objects;
import java.util.UUID;

public record AssetRef(
        UUID assetId,
        String s3Key,
        String contentType,
        String filename,
        long sizeBytes
) {
    public AssetRef {
        Objects.requireNonNull(assetId, "assetId");
        Objects.requireNonNull(s3Key, "s3Key");
        Objects.requireNonNull(contentType, "contentType");
        Objects.requireNonNull(filename, "filename");
        if (sizeBytes <= 0) throw new IllegalArgumentException("sizeBytes must be > 0");
    }
}
