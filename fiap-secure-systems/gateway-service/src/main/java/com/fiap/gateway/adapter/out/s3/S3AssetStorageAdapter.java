package com.fiap.gateway.adapter.out.s3;

import java.io.InputStream;
import java.net.URI;
import java.time.Duration;

import com.fiap.gateway.domain.model.AssetId;
import com.fiap.gateway.domain.model.BundleId;
import com.fiap.gateway.domain.model.ContentType;
import com.fiap.gateway.domain.port.out.AssetStoragePort;

import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;

public class S3AssetStorageAdapter implements AssetStoragePort {

    private final S3Client s3;
    private final S3Presigner presigner;
    private final String bucket;

    public S3AssetStorageAdapter(S3Client s3, S3Presigner presigner, String bucket) {
        this.s3 = s3;
        this.presigner = presigner;
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

    @Override
    public URI presignedGetUrl(String s3Key, Duration ttl) {
        GetObjectRequest get = GetObjectRequest.builder().bucket(bucket).key(s3Key).build();
        return URI.create(
                presigner
                        .presignGetObject(r -> r.signatureDuration(ttl).getObjectRequest(get))
                        .url()
                        .toString());
    }
}
