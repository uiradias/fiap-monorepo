package com.fiap.gateway.domain.port.in;

import java.io.InputStream;

import com.fiap.gateway.domain.model.*;

public interface UploadAssetUseCase {
    Asset upload(
            BundleId bundleId,
            UserId requester,
            String filename,
            ContentType contentType,
            long sizeBytes,
            InputStream body);
}
