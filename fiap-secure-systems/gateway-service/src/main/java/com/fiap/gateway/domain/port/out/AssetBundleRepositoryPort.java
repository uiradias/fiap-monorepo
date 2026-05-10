package com.fiap.gateway.domain.port.out;

import java.util.Optional;

import com.fiap.gateway.domain.model.*;

public interface AssetBundleRepositoryPort {
    AssetBundle insert(AssetBundle bundle);

    AssetBundle save(AssetBundle bundle); // upsert on id

    Optional<AssetBundle> findById(BundleId id);
}
