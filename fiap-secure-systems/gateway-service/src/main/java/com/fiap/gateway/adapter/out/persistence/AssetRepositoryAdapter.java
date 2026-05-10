package com.fiap.gateway.adapter.out.persistence;

import java.util.List;

import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.out.AssetRepositoryPort;

@Repository
public class AssetRepositoryAdapter implements AssetRepositoryPort {

    private final AssetJpaRepository repo;

    public AssetRepositoryAdapter(AssetJpaRepository repo) {
        this.repo = repo;
    }

    @Override
    @Transactional
    public Asset insert(Asset asset) {
        AssetEntity e = new AssetEntity();
        e.id = asset.id().value();
        e.bundleId = asset.bundleId().value();
        e.s3Key = asset.s3Key();
        e.filename = asset.filename();
        e.contentType = asset.contentType().value;
        e.sizeBytes = asset.sizeBytes();
        e.checksumSha256 = asset.checksumSha256();
        e.uploadedAt = asset.uploadedAt();
        repo.save(e);
        return asset;
    }

    @Override
    @Transactional(readOnly = true)
    public List<Asset> findByBundleId(BundleId bundleId) {
        return repo.findByBundleIdOrderByUploadedAtAsc(bundleId.value()).stream()
                .map(this::toDomain)
                .toList();
    }

    private Asset toDomain(AssetEntity e) {
        return new Asset(
                new AssetId(e.id),
                new BundleId(e.bundleId),
                e.s3Key,
                e.filename,
                ContentType.ofLenient(e.contentType),
                e.sizeBytes,
                e.checksumSha256,
                e.uploadedAt);
    }
}
