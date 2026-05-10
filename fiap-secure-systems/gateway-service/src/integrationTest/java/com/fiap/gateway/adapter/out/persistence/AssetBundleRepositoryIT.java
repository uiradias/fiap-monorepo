package com.fiap.gateway.adapter.out.persistence;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Instant;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import com.fiap.gateway.PostgresTestcontainersBase;
import com.fiap.gateway.domain.model.*;

class AssetBundleRepositoryIT extends PostgresTestcontainersBase {

    @Autowired AssetBundleRepositoryAdapter bundles;
    @Autowired AssetRepositoryAdapter assets;
    @Autowired UserRepositoryAdapter users;

    @Test
    void insert_save_findById_round_trip_with_assets() {
        UserId uid = insertUser();
        BundleId bid = new BundleId(UUID.randomUUID());
        Instant now = Instant.parse("2026-05-09T12:00:00Z");

        AssetBundle b = AssetBundle.newBundle(bid, uid, now);
        bundles.insert(b);
        b = b.registerAsset(1024, now.plusSeconds(1));
        bundles.save(b);

        Asset a =
                new Asset(
                        new AssetId(UUID.randomUUID()),
                        bid,
                        "sessions/" + bid + "/x.png",
                        "x.png",
                        ContentType.IMAGE_PNG,
                        1024L,
                        "deadbeef".repeat(8),
                        now.plusSeconds(1));
        assets.insert(a);

        assertThat(bundles.findById(bid))
                .hasValueSatisfying(
                        found -> {
                            assertThat(found.assetCount()).isEqualTo(1);
                            assertThat(found.status()).isEqualTo(BundleStatus.UPLOADING);
                        });
        assertThat(assets.findByBundleId(bid)).hasSize(1);
    }

    private UserId insertUser() {
        UserId uid = new UserId(UUID.randomUUID());
        users.insertOrThrow(
                User.newUser(
                        uid,
                        Email.of("u-" + UUID.randomUUID() + "@x.com"),
                        new PasswordHash("$2a$12$x"),
                        null,
                        Instant.now()));
        return uid;
    }
}
