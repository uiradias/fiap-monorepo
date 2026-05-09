package com.fiap.gateway.adapter.out.http;

import com.fiap.gateway.domain.model.SessionId;
import com.fiap.gateway.domain.model.UserId;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.web.client.RestClient;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@EnabledIfEnvironmentVariable(named = "GATEWAY_IT_ORCHESTRATOR_BASE_URL", matches = "https?://.+")
class OrchestratorRestClientIT {

    @Test
    void createSession_against_running_orchestrator() {
        String baseUrl = System.getenv("GATEWAY_IT_ORCHESTRATOR_BASE_URL");
        String secret = System.getenv().getOrDefault("INTERNAL_HMAC_SECRET",
                "change-me-32-bytes-min-for-real-deployments");

        OrchestratorRestClient client = new OrchestratorRestClient(
                RestClient.builder().baseUrl(baseUrl).build(),
                new InternalHmacRequestSigner(secret),
                () -> Instant.now().getEpochSecond());

        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        client.createSession(sid, uid, 1, List.of("sessions/" + sid + "/test.png"));

        // Read it back
        var session = client.getSession(sid);
        org.assertj.core.api.Assertions.assertThat(session.id()).isEqualTo(sid);
    }
}
