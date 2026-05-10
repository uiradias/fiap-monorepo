package com.fiap.gateway.adapter.out.s3;

import java.io.InputStream;

import com.fiap.gateway.domain.model.AssetId;
import com.fiap.gateway.domain.model.BundleId;
import com.fiap.gateway.domain.model.ContentType;
import com.fiap.gateway.domain.port.out.AssetStoragePort;

import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;

public class S3AssetStorageAdapter implements AssetStoragePort {

    private final S3Client s3;
    private final String bucket;

    public S3AssetStorageAdapter(S3Client s3, String bucket) {
        this.s3 = s3;
        this.bucket = bucket;
    }

    @Override
    public String put(
            BundleId bundleId,
            AssetId assetId,
            String filename,
            ContentType contentType,
            long sizeBytes,
            InputStream body) {
        String key = "sessions/" + bundleId + "/" + filename;
        s3.putObject(
                PutObjectRequest.builder()
                        .bucket(bucket)
                        .key(key)
                        .contentType(contentType.value)
                        .contentLength(sizeBytes)
                        .build(),
                RequestBody.fromInputStream(body, sizeBytes));
        return key;
    }
}
