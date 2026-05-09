package com.fiap.gateway.adapter.out.http;

import com.fiap.gateway.domain.model.*;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class OrchestratorRestClientTest {

    private MockWebServer server;
    private OrchestratorRestClient client;

    @BeforeEach
    void up() throws Exception {
        server = new MockWebServer();
        server.start();
        client = new OrchestratorRestClient(
                RestClient.builder()
                        .baseUrl(server.url("/").toString().replaceAll("/$", ""))
                        .build(),
                new InternalHmacRequestSigner("secret"),
                () -> 1714003200L,                        // fixed clock (epoch-seconds)
                "secret");
    }

    @AfterEach
    void down() throws Exception { server.shutdown(); }

    @Test
    void posts_create_session_with_hmac_headers() throws Exception {
        server.enqueue(new MockResponse().setResponseCode(201).setBody("{}"));

        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        client.createSession(sid, uid, 1, List.of("sessions/" + sid + "/x.png"));

        RecordedRequest rec = server.takeRequest();
        assertThat(rec.getMethod()).isEqualTo("POST");
        assertThat(rec.getPath()).isEqualTo("/internal/sessions");
        assertThat(rec.getHeader("X-Internal-Timestamp")).isEqualTo("1714003200");
        assertThat(rec.getHeader("X-Internal-Signature")).isNotNull().hasSize(64);
        assertThat(rec.getBody().readUtf8()).contains(sid.value().toString());
    }

    @Test
    void getReport_returns_parsed_payload() throws Exception {
        SessionId sid = new SessionId(UUID.randomUUID());
        ReportId rid = new ReportId(UUID.randomUUID());
        server.enqueue(new MockResponse()
                .setHeader("Content-Type", "application/json")
                .setBody("""
                        {
                          "id":"%s",
                          "sessionId":"%s",
                          "summary":"ok",
                          "confidence":"high",
                          "payload":{"summary":"ok"},
                          "modelMetadata":{"model":"x"},
                          "createdAt":"2026-05-09T12:00:00Z"
                        }""".formatted(rid.value(), sid.value())));

        AnalysisReport r = client.getReport(sid);
        assertThat(r.id()).isEqualTo(rid);
        assertThat(r.summary()).isEqualTo("ok");
    }
}
