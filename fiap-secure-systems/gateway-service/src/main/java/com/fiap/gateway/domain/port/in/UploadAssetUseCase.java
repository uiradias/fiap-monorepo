package com.fiap.gateway.domain.port.in;

import com.fiap.gateway.domain.model.*;

import java.io.InputStream;

public interface UploadAssetUseCase {
    Asset upload(BundleId bundleId, UserId requester,
                 String filename, ContentType contentType,
                 long sizeBytes, InputStream body);
}
