package com.fiap.gateway.domain.port.out;

import java.util.List;

import com.fiap.gateway.domain.model.*;

public interface AssetRepositoryPort {
    Asset insert(Asset asset); // unique on (bundle_id, s3_key)

    List<Asset> findByBundleId(BundleId bundleId);
}
