package com.fiap.gateway.adapter.out.persistence;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;

public interface AssetBundleJpaRepository extends JpaRepository<AssetBundleEntity, UUID> {}
