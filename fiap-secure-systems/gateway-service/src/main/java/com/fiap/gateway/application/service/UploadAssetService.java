package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.exception.BundleNotFoundException;
import com.fiap.gateway.domain.exception.ForbiddenException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.UploadAssetUseCase;
import com.fiap.gateway.domain.port.out.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.InputStream;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.UUID;

@Service
public class UploadAssetService implements UploadAssetUseCase {

    private final AssetBundleRepositoryPort bundles;
    private final AssetRepositoryPort assets;
    private final AssetStoragePort storage;
    private final Clock clock;

    public UploadAssetService(AssetBundleRepositoryPort bundles, AssetRepositoryPort assets,
                              AssetStoragePort storage, Clock clock) {
        this.bundles = bundles;
        this.assets = assets;
        this.storage = storage;
        this.clock = clock;
    }

    @Override
    @Transactional
    public Asset upload(BundleId bundleId, UserId requester, String filename,
                        ContentType contentType, long sizeBytes, InputStream body) {
        AssetBundle bundle = bundles.findById(bundleId).orElseThrow(() -> new BundleNotFoundException(bundleId));
        if (!bundle.userId().equals(requester)) throw new ForbiddenException("bundle " + bundleId);
        if (!bundle.status().canAcceptAssets()) {
            throw new IllegalStateException("bundle " + bundleId + " is " + bundle.status() + "; cannot upload");
        }
        if (sizeBytes <= 0 || sizeBytes > 25L * 1024L * 1024L) {
            throw new IllegalArgumentException("file must be 1B–25MB; got " + sizeBytes);
        }

        AssetId assetId = new AssetId(UUID.randomUUID());

        // Hash and stream simultaneously so we don't buffer the whole file.
        DigestingStream ds = new DigestingStream(body);
        String s3Key = storage.put(bundleId, assetId, filename, contentType, sizeBytes, ds);
        String checksum = ds.hexDigest();

        Asset a = new Asset(assetId, bundleId, s3Key, filename, contentType, sizeBytes,
                checksum, clock.now());
        assets.insert(a);

        bundles.save(bundle.registerAsset(sizeBytes, clock.now()));
        return a;
    }

    /** Tee-stream that updates a SHA-256 digest as bytes flow through. */
    private static final class DigestingStream extends InputStream {
        private final InputStream src;
        private final MessageDigest md;
        DigestingStream(InputStream src) {
            this.src = src;
            try { this.md = MessageDigest.getInstance("SHA-256"); }
            catch (Exception e) { throw new IllegalStateException(e); }
        }
        @Override public int read() throws java.io.IOException {
            int b = src.read();
            if (b >= 0) md.update((byte) b);
            return b;
        }
        @Override public int read(byte[] buf, int off, int len) throws java.io.IOException {
            int n = src.read(buf, off, len);
            if (n > 0) md.update(buf, off, n);
            return n;
        }
        String hexDigest() { return HexFormat.of().formatHex(md.digest()); }
    }
}
