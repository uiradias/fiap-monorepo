package com.fiap.gateway.adapter.out.persistence;

import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.out.AssetBundleRepositoryPort;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Repository
public class AssetBundleRepositoryAdapter implements AssetBundleRepositoryPort {

    private final AssetBundleJpaRepository repo;

    public AssetBundleRepositoryAdapter(AssetBundleJpaRepository repo) { this.repo = repo; }

    @Override
    @Transactional
    public AssetBundle insert(AssetBundle bundle) {
        repo.save(toEntity(bundle));
        return bundle;
    }

    @Override
    @Transactional
    public AssetBundle save(AssetBundle bundle) {
        repo.save(toEntity(bundle));
        return bundle;
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<AssetBundle> findById(BundleId id) {
        return repo.findById(id.value()).map(this::toDomain);
    }

    private AssetBundleEntity toEntity(AssetBundle b) {
        AssetBundleEntity e = new AssetBundleEntity();
        e.id = b.id().value();
        e.userId = b.userId().value();
        e.status = b.status().name();
        e.assetCount = b.assetCount();
        e.totalBytes = b.totalBytes();
        e.createdAt = b.createdAt();
        e.updatedAt = b.updatedAt();
        return e;
    }

    private AssetBundle toDomain(AssetBundleEntity e) {
        return new AssetBundle(
                new BundleId(e.id),
                new UserId(e.userId),
                BundleStatus.valueOf(e.status),
                e.assetCount,
                e.totalBytes,
                e.createdAt,
                e.updatedAt);
    }
}
