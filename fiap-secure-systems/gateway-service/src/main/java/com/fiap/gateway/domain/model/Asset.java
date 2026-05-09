package com.fiap.gateway.domain.model;

import java.time.Instant;
import java.util.Objects;

public record Asset(
        AssetId id,
        BundleId bundleId,
        String s3Key,
        String filename,
        ContentType contentType,
        long sizeBytes,
        String checksumSha256,
        Instant uploadedAt) {

    public Asset {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(bundleId, "bundleId");
        Objects.requireNonNull(s3Key, "s3Key");
        Objects.requireNonNull(filename, "filename");
        Objects.requireNonNull(contentType, "contentType");
        Objects.requireNonNull(checksumSha256, "checksumSha256");
        Objects.requireNonNull(uploadedAt, "uploadedAt");
        if (sizeBytes <= 0) throw new IllegalArgumentException("sizeBytes must be positive");
        if (sizeBytes > 25L * 1024L * 1024L)
            throw new IllegalArgumentException("sizeBytes exceeds 25 MiB cap");
    }
}
