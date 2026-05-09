package com.fiap.gateway.adapter.out.persistence;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "asset_bundles")
public class AssetBundleEntity {
    @Id public UUID id;
    @Column(name = "user_id", nullable = false) public UUID userId;
    @Column(nullable = false) public String status;
    @Column(name = "asset_count", nullable = false) public int assetCount;
    @Column(name = "total_bytes", nullable = false) public long totalBytes;
    @Column(name = "created_at", nullable = false) public Instant createdAt;
    @Column(name = "updated_at", nullable = false) public Instant updatedAt;
}
