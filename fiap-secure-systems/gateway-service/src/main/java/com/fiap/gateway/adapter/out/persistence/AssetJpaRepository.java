package com.fiap.gateway.adapter.out.persistence;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AssetJpaRepository extends JpaRepository<AssetEntity, UUID> {
    List<AssetEntity> findByBundleIdOrderByUploadedAtAsc(UUID bundleId);
}
