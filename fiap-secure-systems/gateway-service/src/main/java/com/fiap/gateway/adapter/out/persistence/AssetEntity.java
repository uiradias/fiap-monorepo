package com.fiap.gateway.adapter.out.persistence;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "assets")
public class AssetEntity {
    @Id public UUID id;
    @Column(name = "bundle_id", nullable = false) public UUID bundleId;
    @Column(name = "s3_key", nullable = false) public String s3Key;
    @Column(nullable = false) public String filename;
    @Column(name = "content_type", nullable = false) public String contentType;
    @Column(name = "size_bytes", nullable = false) public long sizeBytes;
    @Column(name = "checksum_sha256", nullable = false) public String checksumSha256;
    @Column(name = "uploaded_at", nullable = false) public Instant uploadedAt;
}
