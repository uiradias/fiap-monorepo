package com.fiap.gateway.domain.model;

import java.time.Instant;
import java.util.Objects;

public record AssetBundle(
        BundleId id,
        UserId userId,
        BundleStatus status,
        int assetCount,
        long totalBytes,
        Instant createdAt,
        Instant updatedAt) {

    private static final int MAX_ASSETS = 20;

    public AssetBundle {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(userId, "userId");
        Objects.requireNonNull(status, "status");
        Objects.requireNonNull(createdAt, "createdAt");
        Objects.requireNonNull(updatedAt, "updatedAt");
        if (assetCount < 0) throw new IllegalArgumentException("assetCount must be >= 0");
        if (totalBytes < 0) throw new IllegalArgumentException("totalBytes must be >= 0");
    }

    public static AssetBundle newBundle(BundleId id, UserId userId, Instant now) {
        return new AssetBundle(id, userId, BundleStatus.INITIATED, 0, 0L, now, now);
    }

    public AssetBundle registerAsset(long sizeBytes, Instant now) {
        if (!status.canAcceptAssets()) {
            throw new IllegalStateException(
                    "bundle " + id + " is " + status + "; cannot accept assets");
        }
        if (assetCount >= MAX_ASSETS) {
            throw new IllegalStateException(
                    "bundle " + id + " already at the " + MAX_ASSETS + " asset cap");
        }
        return new AssetBundle(
                id,
                userId,
                BundleStatus.UPLOADING,
                assetCount + 1,
                totalBytes + sizeBytes,
                createdAt,
                now);
    }

    public AssetBundle finalize(Instant now) {
        if (status == BundleStatus.UPLOADED) return this;
        if (!status.canBeFinalized()) {
            throw new IllegalStateException("bundle " + id + " is " + status + "; cannot finalize");
        }
        return new AssetBundle(
                id, userId, BundleStatus.UPLOADED, assetCount, totalBytes, createdAt, now);
    }

    public AssetBundle markFailed(Instant now) {
        if (status == BundleStatus.UPLOADED || status == BundleStatus.FAILED) {
            return this;
        }
        return new AssetBundle(
                id, userId, BundleStatus.FAILED, assetCount, totalBytes, createdAt, now);
    }
}
