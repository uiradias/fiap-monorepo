package com.fiap.gateway.domain.port.in;

import java.net.URI;

import com.fiap.gateway.domain.model.*;

public interface IssueAssetDownloadUrlUseCase {

    record DownloadUrl(URI url, long expiresInSeconds) {}

    DownloadUrl issue(BundleId bundleId, AssetId assetId, UserId requester);
}
