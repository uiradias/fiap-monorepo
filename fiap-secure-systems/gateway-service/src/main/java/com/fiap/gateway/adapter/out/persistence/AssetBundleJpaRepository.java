package com.fiap.gateway.adapter.out.persistence;

import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AssetBundleJpaRepository extends JpaRepository<AssetBundleEntity, UUID> {}
