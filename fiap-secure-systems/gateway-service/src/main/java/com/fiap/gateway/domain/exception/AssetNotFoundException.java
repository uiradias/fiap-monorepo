package com.fiap.gateway.domain.exception;

import com.fiap.gateway.domain.model.AssetId;
import com.fiap.gateway.domain.model.BundleId;

public class AssetNotFoundException extends RuntimeException {
    public AssetNotFoundException(BundleId bundleId, AssetId assetId) {
        super("asset not found in bundle " + bundleId + ": " + assetId);
    }
}
