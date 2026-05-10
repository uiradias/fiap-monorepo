package com.fiap.gateway.application.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.io.ByteArrayInputStream;
import java.time.Instant;
import java.util.UUID;

import org.junit.jupiter.api.Test;

import com.fiap.gateway.domain.exception.BundleNotFoundException;
import com.fiap.gateway.domain.exception.ForbiddenException;
import com.fiap.gateway.domain.model.*;

class UploadAssetServiceTest {

    private final Clock CLOCK = () -> Instant.parse("2026-05-09T12:00:00Z");
    private final InMemoryFakes.FakeBundles bundles = new InMemoryFakes.FakeBundles();
    private final InMemoryFakes.FakeAssets assets = new InMemoryFakes.FakeAssets();
    private final InMemoryFakes.FakeS3 s3 = new InMemoryFakes.FakeS3();
    private final UploadAssetService svc = new UploadAssetService(bundles, assets, s3, CLOCK);

    private final UserId UID = new UserId(UUID.randomUUID());
    private final BundleId BID = new BundleId(UUID.randomUUID());

    @Test
    void uploads_an_asset_into_INITIATED_bundle_and_advances_state() {
        bundles.insert(AssetBundle.newBundle(BID, UID, CLOCK.now()));
        byte[] body = "hello".getBytes();

        Asset a =
                svc.upload(
                        BID,
                        UID,
                        "hello.png",
                        ContentType.IMAGE_PNG,
                        body.length,
                        new ByteArrayInputStream(body));

        assertThat(a.bundleId()).isEqualTo(BID);
        assertThat(a.s3Key()).isEqualTo("sessions/" + BID + "/hello.png");
        assertThat(a.checksumSha256()).hasSize(64); // sha256 hex
        assertThat(s3.writes).containsKey("sessions/" + BID + "/hello.png");
        assertThat(bundles.byId.get(BID).status()).isEqualTo(BundleStatus.UPLOADING);
        assertThat(bundles.byId.get(BID).assetCount()).isEqualTo(1);
    }

    @Test
    void rejects_other_users_bundle() {
        bundles.insert(AssetBundle.newBundle(BID, UID, CLOCK.now()));
        UserId attacker = new UserId(UUID.randomUUID());
        assertThatThrownBy(
                        () ->
                                svc.upload(
                                        BID,
                                        attacker,
                                        "x.png",
                                        ContentType.IMAGE_PNG,
                                        1,
                                        new ByteArrayInputStream(new byte[] {0})))
                .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void rejects_unknown_bundle() {
        assertThatThrownBy(
                        () ->
                                svc.upload(
                                        BID,
                                        UID,
                                        "x.png",
                                        ContentType.IMAGE_PNG,
                                        1,
                                        new ByteArrayInputStream(new byte[] {0})))
                .isInstanceOf(BundleNotFoundException.class);
    }

    @Test
    void rejects_size_zero() {
        bundles.insert(AssetBundle.newBundle(BID, UID, CLOCK.now()));
        assertThatThrownBy(
                        () ->
                                svc.upload(
                                        BID,
                                        UID,
                                        "x.png",
                                        ContentType.IMAGE_PNG,
                                        0,
                                        new ByteArrayInputStream(new byte[0])))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void rejects_size_above_25_MiB() {
        bundles.insert(AssetBundle.newBundle(BID, UID, CLOCK.now()));
        long tooBig = 25L * 1024L * 1024L + 1;
        assertThatThrownBy(
                        () ->
                                svc.upload(
                                        BID,
                                        UID,
                                        "x.png",
                                        ContentType.IMAGE_PNG,
                                        tooBig,
                                        new ByteArrayInputStream(new byte[1])))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
