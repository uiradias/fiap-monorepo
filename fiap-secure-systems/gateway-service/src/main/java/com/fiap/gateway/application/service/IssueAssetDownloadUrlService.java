package com.fiap.gateway.application.service;

import java.time.Duration;
import java.util.List;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import com.fiap.gateway.domain.exception.AssetNotFoundException;
import com.fiap.gateway.domain.exception.BundleNotFoundException;
import com.fiap.gateway.domain.exception.ForbiddenException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.IssueAssetDownloadUrlUseCase;
import com.fiap.gateway.domain.port.out.AssetBundleRepositoryPort;
import com.fiap.gateway.domain.port.out.AssetRepositoryPort;
import com.fiap.gateway.domain.port.out.AssetStoragePort;

@Service
public class IssueAssetDownloadUrlService implements IssueAssetDownloadUrlUseCase {

    private final AssetBundleRepositoryPort bundles;
    private final AssetRepositoryPort assets;
    private final AssetStoragePort storage;
    private final Duration presignTtl;

    public IssueAssetDownloadUrlService(
            AssetBundleRepositoryPort bundles,
            AssetRepositoryPort assets,
            AssetStoragePort storage,
            @Value("${gateway.s3.presign-ttl-seconds:900}") long presignTtlSeconds) {
        this.bundles = bundles;
        this.assets = assets;
        this.storage = storage;
        if (presignTtlSeconds <= 0 || presignTtlSeconds > 86400) {
            throw new IllegalArgumentException(
                    "gateway.s3.presign-ttl-seconds must be between 1 and 86400");
        }
        this.presignTtl = Duration.ofSeconds(presignTtlSeconds);
    }

    @Override
    public DownloadUrl issue(BundleId bundleId, AssetId assetId, UserId requester) {
        AssetBundle bundle =
                bundles.findById(bundleId).orElseThrow(() -> new BundleNotFoundException(bundleId));
        if (!bundle.userId().equals(requester)) throw new ForbiddenException("bundle " + bundleId);

        List<Asset> inBundle = assets.findByBundleId(bundleId);
        Asset asset =
                inBundle.stream()
                        .filter(a -> a.id().equals(assetId))
                        .findFirst()
                        .orElseThrow(() -> new AssetNotFoundException(bundleId, assetId));

        return new DownloadUrl(
                storage.presignedGetUrl(asset.s3Key(), presignTtl), presignTtl.toSeconds());
    }
}
