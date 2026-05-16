package com.fiap.gateway.domain.port.out;

import java.io.InputStream;
import java.net.URI;
import java.time.Duration;

import com.fiap.gateway.domain.model.*;

public interface AssetStoragePort {
    /** Returns the s3 key written. SSE is the bucket default. */
    String put(
            BundleId bundleId,
            AssetId assetId,
            String filename,
            ContentType contentType,
            long sizeBytes,
            InputStream body);

    /** HTTPS GET URL valid for {@code ttl}; caller authorizes bundle/asset ownership. */
    URI presignedGetUrl(String s3Key, Duration ttl);
}
