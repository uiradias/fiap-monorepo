package com.fiap.gateway.adapter.in.rest.dto;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import com.fiap.gateway.domain.model.AssetBundle;

public record BundleResponse(
        UUID bundleId,
        String status,
        int assetCount,
        long totalBytes,
        Instant createdAt,
        Instant updatedAt,
        List<AssetResponse> assets) {
    public static BundleResponse of(AssetBundle b, List<AssetResponse> assets) {
        return new BundleResponse(
                b.id().value(),
                b.status().name(),
                b.assetCount(),
                b.totalBytes(),
                b.createdAt(),
                b.updatedAt(),
                assets);
    }
}
