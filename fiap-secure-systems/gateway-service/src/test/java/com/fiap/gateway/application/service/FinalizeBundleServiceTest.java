package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.exception.ForbiddenException;
import com.fiap.gateway.domain.model.*;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class FinalizeBundleServiceTest {

    private final Clock CLOCK = () -> Instant.parse("2026-05-09T12:00:00Z");
    private final InMemoryFakes.FakeBundles bundles = new InMemoryFakes.FakeBundles();
    private final InMemoryFakes.FakeAssets assets = new InMemoryFakes.FakeAssets();
    private final InMemoryFakes.FakeOrchestrator orch = new InMemoryFakes.FakeOrchestrator();
    private final InMemoryFakes.FakeProjections proj = new InMemoryFakes.FakeProjections();

    private final FinalizeBundleService svc = new FinalizeBundleService(bundles, assets, orch, proj, CLOCK);

    @Test
    void finalizes_with_orchestrator_call_and_seeds_projection() {
        UserId uid = new UserId(UUID.randomUUID());
        BundleId bid = new BundleId(UUID.randomUUID());
        AssetBundle b = AssetBundle.newBundle(bid, uid, CLOCK.now()).registerAsset(10, CLOCK.now());
        bundles.insert(b);
        assets.insert(new Asset(new AssetId(UUID.randomUUID()), bid,
                "sessions/" + bid + "/x.png", "x.png", ContentType.IMAGE_PNG, 10,
                "deadbeef".repeat(8), CLOCK.now()));

        var result = svc.finalize(bid, uid);

        assertThat(result.sessionId().value().toString()).isEqualTo(bid.value().toString());
        assertThat(orch.creates).hasSize(1);
        assertThat(orch.creates.get(0).count()).isEqualTo(1);
        assertThat(proj.byId).containsKey(result.sessionId());
        assertThat(bundles.byId.get(bid).status()).isEqualTo(BundleStatus.UPLOADED);
    }

    @Test
    void rejects_other_users_bundle() {
        UserId owner = new UserId(UUID.randomUUID());
        UserId attacker = new UserId(UUID.randomUUID());
        BundleId bid = new BundleId(UUID.randomUUID());
        bundles.insert(AssetBundle.newBundle(bid, owner, CLOCK.now())
                .registerAsset(1, CLOCK.now()));
        assertThatThrownBy(() -> svc.finalize(bid, attacker))
                .isInstanceOf(ForbiddenException.class);
    }
}
