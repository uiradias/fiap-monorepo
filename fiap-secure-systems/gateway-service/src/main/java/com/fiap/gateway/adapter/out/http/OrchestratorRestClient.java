package com.fiap.gateway.adapter.out.http;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.application.service.Clock;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.out.OrchestratorClientPort;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.LongSupplier;

public class OrchestratorRestClient implements OrchestratorClientPort {

    private final RestClient client;
    private final InternalHmacRequestSigner signer;
    private final LongSupplier clockSeconds;
    private final ObjectMapper mapper = new ObjectMapper().findAndRegisterModules();

    @SuppressWarnings("unused")
    public OrchestratorRestClient(RestClient client, InternalHmacRequestSigner signer,
                                  Clock clock, String hmacSecret) {
        this(client, signer, () -> clock.now().getEpochSecond());
    }

    public OrchestratorRestClient(RestClient client, InternalHmacRequestSigner signer,
                                  LongSupplier clockSeconds, String hmacSecret) {
        this(client, signer, clockSeconds);
    }

    public OrchestratorRestClient(RestClient client, InternalHmacRequestSigner signer,
                                  LongSupplier clockSeconds) {
        this.client = client;
        this.signer = signer;
        this.clockSeconds = clockSeconds;
    }

    @Retry(name = "orchestrator")
    @CircuitBreaker(name = "orchestrator")
    @Override
    public void createSession(SessionId sessionId, UserId userId, int assetCount, List<String> assetKeys) {
        Map<String, Object> body = Map.of(
                "sessionId", sessionId.value().toString(),
                "userId", userId.value().toString(),
                "assetCount", assetCount,
                "assetKeys", assetKeys);
        sendJson("POST", "/internal/sessions", body, Void.class);
    }

    @Retry(name = "orchestrator")
    @CircuitBreaker(name = "orchestrator")
    @Override
    public SessionProjection getSession(SessionId sessionId) {
        String path = "/internal/sessions/" + sessionId;
        @SuppressWarnings("unchecked")
        Map<String, Object> body = (Map<String, Object>) sendJson("GET", path, null, Map.class);
        return new SessionProjection(
                new SessionId(UUID.fromString((String) body.get("id"))),
                new UserId(UUID.fromString((String) body.get("userId"))),
                SessionState.valueOf((String) body.get("state")),
                java.time.Instant.parse((String) body.get("lastEventAt")),
                (String) body.get("failureReason"),
                body.get("reportId") == null ? null : new ReportId(UUID.fromString((String) body.get("reportId"))));
    }

    @Retry(name = "orchestrator")
    @CircuitBreaker(name = "orchestrator")
    @Override
    public AnalysisReport getReport(SessionId sessionId) {
        String path = "/internal/sessions/" + sessionId + "/report";
        @SuppressWarnings("unchecked")
        Map<String, Object> body = (Map<String, Object>) sendJson("GET", path, null, Map.class);
        @SuppressWarnings("unchecked")
        Map<String, Object> payload = (Map<String, Object>) body.get("payload");
        @SuppressWarnings("unchecked")
        Map<String, Object> md = (Map<String, Object>) body.get("modelMetadata");
        return new AnalysisReport(
                new ReportId(UUID.fromString((String) body.get("id"))),
                new SessionId(UUID.fromString((String) body.get("sessionId"))),
                (String) body.get("summary"),
                (String) body.get("confidence"),
                payload, md,
                java.time.Instant.parse((String) body.get("createdAt")));
    }

    @Retry(name = "orchestrator")
    @CircuitBreaker(name = "orchestrator")
    @Override
    public void cancelSession(SessionId sessionId) {
        sendJson("POST", "/internal/sessions/" + sessionId + "/cancel", Map.of(), Void.class);
    }

    private <T> T sendJson(String method, String path, Object body, Class<T> responseType) {
        byte[] bodyBytes;
        try {
            bodyBytes = body == null ? new byte[0] : mapper.writeValueAsBytes(body);
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }
        long ts = clockSeconds.getAsLong();
        String sig = signer.signature(ts, method, path, bodyBytes);

        var spec = switch (method) {
            case "GET"  -> client.get().uri(path).headers(h -> commonHeaders(h, ts, sig));
            case "POST" -> client.post().uri(path).headers(h -> commonHeaders(h, ts, sig))
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(bodyBytes);
            default -> throw new IllegalArgumentException("unsupported method: " + method);
        };

        if (responseType == Void.class) {
            spec.retrieve().toBodilessEntity();
            return null;
        }
        return spec.retrieve().body(responseType);
    }

    private static void commonHeaders(HttpHeaders h, long ts, String sig) {
        h.add("X-Internal-Timestamp", Long.toString(ts));
        h.add("X-Internal-Signature", sig);
    }
}
