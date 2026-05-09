package com.fiap.gateway.adapter.in.rest.dto;

import com.fiap.gateway.domain.model.Asset;
import java.time.Instant;
import java.util.UUID;

public record AssetResponse(
        UUID id, String filename, String contentType, long sizeBytes,
        String s3Key, String checksumSha256, Instant uploadedAt) {
    public static AssetResponse of(Asset a) {
        return new AssetResponse(a.id().value(), a.filename(), a.contentType().value, a.sizeBytes(),
                a.s3Key(), a.checksumSha256(), a.uploadedAt());
    }
}
