package com.fiap.gateway.adapter.out.http;

import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.function.LongSupplier;

import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.MediaType;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.application.service.Clock;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.out.OrchestratorClientPort;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;

public class OrchestratorRestClient implements OrchestratorClientPort {

    private final RestClient client;
    private final InternalHmacRequestSigner signer;
    private final LongSupplier clockSeconds;
    private final ObjectMapper mapper = new ObjectMapper().findAndRegisterModules();

    @SuppressWarnings("unused")
    public OrchestratorRestClient(
            RestClient client, InternalHmacRequestSigner signer, Clock clock, String hmacSecret) {
        this(client, signer, () -> clock.now().getEpochSecond());
    }

    public OrchestratorRestClient(
            RestClient client,
            InternalHmacRequestSigner signer,
            LongSupplier clockSeconds,
            String hmacSecret) {
        this(client, signer, clockSeconds);
    }

    public OrchestratorRestClient(
            RestClient client, InternalHmacRequestSigner signer, LongSupplier clockSeconds) {
        this.client = client;
        this.signer = signer;
        this.clockSeconds = clockSeconds;
    }

    @Retry(name = "orchestrator")
    @CircuitBreaker(name = "orchestrator")
    @Override
    public void createSession(
            SessionId sessionId, UserId userId, int assetCount, List<Asset> assets) {
        List<Map<String, Object>> assetReqs =
                assets.stream()
                        .map(
                                a ->
                                        Map.<String, Object>of(
                                                "assetId", a.id().value().toString(),
                                                "s3Key", a.s3Key(),
                                                "contentType", a.contentType().value,
                                                "filename", a.filename(),
                                                "sizeBytes", a.sizeBytes()))
                        .toList();
        Map<String, Object> body =
                Map.of(
                        "sessionId",
                        sessionId.value().toString(),
                        "userId",
                        userId.value().toString(),
                        "assetCount",
                        assetCount,
                        "assets",
                        assetReqs);
        sendJson("POST", "/internal/sessions", body, Void.class);
    }

    @Retry(name = "orchestrator")
    @CircuitBreaker(name = "orchestrator")
    @Override
    public SessionProjection getSession(SessionId sessionId) {
        String path = "/internal/sessions/" + sessionId;
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> body = (Map<String, Object>) sendJson("GET", path, null, Map.class);
            return sessionProjectionFromOrchestratorBody(body);
        } catch (RestClientResponseException e) {
            if (e.getStatusCode().isSameCodeAs(HttpStatusCode.valueOf(404))) {
                return null;
            }
            throw e;
        }
    }

    @Retry(name = "orchestrator")
    @CircuitBreaker(name = "orchestrator")
    @Override
    public List<SessionSummary> listSessions(UserId userId, int limit) {
        String signingPath = "/internal/sessions";
        String uri = signingPath + "?userId=" + userId.value() + "&limit=" + limit;
        byte[] bodyBytes = new byte[0];
        long ts = clockSeconds.getAsLong();
        String sig = signer.signature(ts, "GET", signingPath, bodyBytes);
        List<Map<String, Object>> rows =
                client.get()
                        .uri(uri)
                        .headers(h -> commonHeaders(h, ts, sig))
                        .retrieve()
                        .body(new ParameterizedTypeReference<List<Map<String, Object>>>() {});
        if (rows == null) {
            return List.of();
        }
        List<SessionSummary> out = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            out.add(sessionSummaryFromOrchestratorBody(row));
        }
        return out;
    }

    private static SessionProjection sessionProjectionFromOrchestratorBody(
            Map<String, Object> body) {
        ReportId reportId = parseReportId(body.get("reportId"));
        return new SessionProjection(
                new SessionId(UUID.fromString((String) body.get("sessionId"))),
                new UserId(UUID.fromString((String) body.get("userId"))),
                SessionState.valueOf((String) body.get("state")),
                Instant.parse((String) body.get("updatedAt")),
                (String) body.get("failureReason"),
                reportId);
    }

    private static SessionSummary sessionSummaryFromOrchestratorBody(Map<String, Object> body) {
        int assetCount = body.get("assetCount") instanceof Number n ? n.intValue() : 0;
        return new SessionSummary(
                new SessionId(UUID.fromString((String) body.get("sessionId"))),
                new UserId(UUID.fromString((String) body.get("userId"))),
                SessionState.valueOf((String) body.get("state")),
                assetCount,
                (String) body.get("failureReason"),
                Instant.parse((String) body.get("createdAt")),
                Instant.parse((String) body.get("updatedAt")),
                Optional.ofNullable(parseReportId(body.get("reportId"))));
    }

    private static ReportId parseReportId(Object raw) {
        if (raw == null) {
            return null;
        }
        return new ReportId(UUID.fromString(raw.toString()));
    }

    @Retry(name = "orchestrator")
    @CircuitBreaker(name = "orchestrator")
    @Override
    public AnalysisReport getReport(SessionId sessionId) {
        // Orchestrator's ReportResponse: reportId, sessionId, summary, confidence, payload,
        // modelMetadata, createdAt
        String path = "/internal/sessions/" + sessionId + "/report";
        @SuppressWarnings("unchecked")
        Map<String, Object> body = (Map<String, Object>) sendJson("GET", path, null, Map.class);
        @SuppressWarnings("unchecked")
        Map<String, Object> payload = (Map<String, Object>) body.get("payload");
        @SuppressWarnings("unchecked")
        Map<String, Object> md = (Map<String, Object>) body.get("modelMetadata");
        return new AnalysisReport(
                new ReportId(UUID.fromString((String) body.get("reportId"))),
                new SessionId(UUID.fromString((String) body.get("sessionId"))),
                (String) body.get("summary"),
                (String) body.get("confidence"),
                payload,
                md,
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

        var spec =
                switch (method) {
                    case "GET" -> client.get().uri(path).headers(h -> commonHeaders(h, ts, sig));
                    case "POST" ->
                            client.post()
                                    .uri(path)
                                    .headers(h -> commonHeaders(h, ts, sig))
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
