package com.fiap.gateway.adapter.out.http;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.web.client.RestClient;

import com.fiap.gateway.domain.model.Asset;
import com.fiap.gateway.domain.model.AssetId;
import com.fiap.gateway.domain.model.BundleId;
import com.fiap.gateway.domain.model.ContentType;
import com.fiap.gateway.domain.model.SessionId;
import com.fiap.gateway.domain.model.UserId;

@EnabledIfEnvironmentVariable(named = "GATEWAY_IT_ORCHESTRATOR_BASE_URL", matches = "https?://.+")
class OrchestratorRestClientIT {

    @Test
    void createSession_against_running_orchestrator() {
        String baseUrl = System.getenv("GATEWAY_IT_ORCHESTRATOR_BASE_URL");
        String secret =
                System.getenv()
                        .getOrDefault(
                                "INTERNAL_HMAC_SECRET",
                                "change-me-32-bytes-min-for-real-deployments");

        OrchestratorRestClient client =
                new OrchestratorRestClient(
                        RestClient.builder().baseUrl(baseUrl).build(),
                        new InternalHmacRequestSigner(secret),
                        () -> Instant.now().getEpochSecond());

        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        BundleId bid = new BundleId(sid.value());
        Asset asset =
                new Asset(
                        new AssetId(UUID.randomUUID()),
                        bid,
                        "sessions/" + sid + "/test.png",
                        "test.png",
                        ContentType.IMAGE_PNG,
                        100L,
                        "deadbeef".repeat(8),
                        Instant.now());
        client.createSession(sid, uid, 1, List.of(asset));

        // Read it back
        var session = client.getSession(sid);
        org.assertj.core.api.Assertions.assertThat(session.id()).isEqualTo(sid);
    }
}
