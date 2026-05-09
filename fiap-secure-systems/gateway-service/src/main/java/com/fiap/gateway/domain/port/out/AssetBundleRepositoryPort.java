package com.fiap.gateway.domain.port.out;

import com.fiap.gateway.domain.model.*;

import java.util.Optional;

public interface AssetBundleRepositoryPort {
    AssetBundle insert(AssetBundle bundle);
    AssetBundle save(AssetBundle bundle);                   // upsert on id
    Optional<AssetBundle> findById(BundleId id);
}
