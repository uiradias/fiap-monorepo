package com.fiap.gateway.domain.port.out;

import com.fiap.gateway.domain.model.*;

import java.util.List;

public interface AssetRepositoryPort {
    Asset insert(Asset asset);                              // unique on (bundle_id, s3_key)
    List<Asset> findByBundleId(BundleId bundleId);
}
