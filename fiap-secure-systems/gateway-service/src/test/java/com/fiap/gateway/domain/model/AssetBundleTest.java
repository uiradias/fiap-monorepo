package com.fiap.gateway.domain.model;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;
import java.util.UUID;

import org.junit.jupiter.api.Test;

class AssetBundleTest {

    private final BundleId BID = new BundleId(UUID.randomUUID());
    private final UserId UID = new UserId(UUID.randomUUID());
    private final Instant NOW = Instant.parse("2026-05-09T12:00:00Z");

    @Test
    void newBundle_starts_in_INITIATED_with_zero_assets() {
        AssetBundle b = AssetBundle.newBundle(BID, UID, NOW);
        assertThat(b.status()).isEqualTo(BundleStatus.INITIATED);
        assertThat(b.assetCount()).isZero();
        assertThat(b.totalBytes()).isZero();
    }

    @Test
    void registerAsset_moves_to_UPLOADING_and_increments_counts() {
        AssetBundle b =
                AssetBundle.newBundle(BID, UID, NOW).registerAsset(1024, NOW.plusSeconds(1));
        assertThat(b.status()).isEqualTo(BundleStatus.UPLOADING);
        assertThat(b.assetCount()).isEqualTo(1);
        assertThat(b.totalBytes()).isEqualTo(1024);
        assertThat(b.updatedAt()).isEqualTo(NOW.plusSeconds(1));
    }

    @Test
    void registerAsset_rejects_after_20() {
        AssetBundle b = AssetBundle.newBundle(BID, UID, NOW);
        for (int i = 0; i < 20; i++) b = b.registerAsset(1, NOW);
        AssetBundle finalB = b;
        assertThatThrownBy(() -> finalB.registerAsset(1, NOW))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("20");
    }

    @Test
    void finalize_rejected_on_INITIATED() {
        AssetBundle empty = AssetBundle.newBundle(BID, UID, NOW);
        assertThatThrownBy(() -> empty.finalize(NOW)).isInstanceOf(IllegalStateException.class);
    }

    @Test
    void finalize_moves_to_UPLOADED() {
        AssetBundle b =
                AssetBundle.newBundle(BID, UID, NOW)
                        .registerAsset(1, NOW)
                        .finalize(NOW.plusSeconds(2));
        assertThat(b.status()).isEqualTo(BundleStatus.UPLOADED);
        assertThat(b.updatedAt()).isEqualTo(NOW.plusSeconds(2));
    }

    @Test
    void finalize_is_idempotent_on_already_UPLOADED() {
        AssetBundle uploaded =
                AssetBundle.newBundle(BID, UID, NOW)
                        .registerAsset(1, NOW)
                        .finalize(NOW.plusSeconds(2));
        AssetBundle again = uploaded.finalize(NOW.plusSeconds(3));
        assertThat(again).isSameAs(uploaded);
    }

    @Test
    void markFailed_is_a_noop_on_terminal_bundles() {
        AssetBundle uploaded =
                AssetBundle.newBundle(BID, UID, NOW)
                        .registerAsset(1, NOW)
                        .finalize(NOW.plusSeconds(2));
        assertThat(uploaded.markFailed(NOW.plusSeconds(3))).isSameAs(uploaded);

        AssetBundle alreadyFailed =
                AssetBundle.newBundle(BID, UID, NOW).markFailed(NOW.plusSeconds(1));
        assertThat(alreadyFailed.markFailed(NOW.plusSeconds(2))).isSameAs(alreadyFailed);
    }
}
