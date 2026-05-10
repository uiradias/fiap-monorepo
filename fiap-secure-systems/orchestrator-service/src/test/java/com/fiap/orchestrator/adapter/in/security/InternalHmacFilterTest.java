package com.fiap.orchestrator.adapter.in.security;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import com.fiap.orchestrator.application.service.Clock;

class InternalHmacFilterTest {

    private static final String SECRET = "test-secret-32-bytes-min-for-real-deployments";
    private static final HexFormat HEX = HexFormat.of();

    Clock clock;
    InternalHmacFilter filter;

    @BeforeEach
    void setup() {
        clock = () -> Instant.parse("2026-01-01T00:00:00Z");
        filter = new InternalHmacFilter(SECRET, 300, clock);
    }

    @Test
    void valid_signature_passes() throws Exception {
        MockHttpServletRequest req = jsonRequest("POST", "/internal/sessions", "{\"k\":\"v\"}");
        long ts = clock.now().getEpochSecond();
        sign(req, ts);
        MockHttpServletResponse resp = new MockHttpServletResponse();
        filter.doFilter(req, resp, new MockFilterChain());
        assertThat(resp.getStatus()).isEqualTo(200);
    }

    @Test
    void missing_signature_returns_401() throws Exception {
        MockHttpServletRequest req = jsonRequest("POST", "/internal/sessions", "{}");
        MockHttpServletResponse resp = new MockHttpServletResponse();
        filter.doFilter(req, resp, new MockFilterChain());
        assertThat(resp.getStatus()).isEqualTo(401);
        assertThat(resp.getContentType()).startsWith("application/problem+json");
    }

    @Test
    void wrong_secret_returns_401() throws Exception {
        MockHttpServletRequest req = jsonRequest("POST", "/internal/sessions", "{}");
        long ts = clock.now().getEpochSecond();
        req.addHeader("X-Internal-Timestamp", String.valueOf(ts));
        req.addHeader(
                "X-Internal-Signature",
                hmac(
                        "wrong-secret-min-16chars",
                        canonical(ts, "POST", "/internal/sessions", "{}")));
        MockHttpServletResponse resp = new MockHttpServletResponse();
        filter.doFilter(req, resp, new MockFilterChain());
        assertThat(resp.getStatus()).isEqualTo(401);
    }

    @Test
    void replay_outside_window_returns_401() throws Exception {
        MockHttpServletRequest req = jsonRequest("POST", "/internal/sessions", "{}");
        long ts = clock.now().minusSeconds(600).getEpochSecond();
        req.addHeader("X-Internal-Timestamp", String.valueOf(ts));
        req.addHeader(
                "X-Internal-Signature",
                hmac(SECRET, canonical(ts, "POST", "/internal/sessions", "{}")));
        MockHttpServletResponse resp = new MockHttpServletResponse();
        filter.doFilter(req, resp, new MockFilterChain());
        assertThat(resp.getStatus()).isEqualTo(401);
    }

    @Test
    void actuator_health_skips_hmac() throws Exception {
        MockHttpServletRequest req = new MockHttpServletRequest("GET", "/actuator/health");
        MockHttpServletResponse resp = new MockHttpServletResponse();
        filter.doFilter(req, resp, new MockFilterChain());
        assertThat(resp.getStatus()).isEqualTo(200);
    }

    private MockHttpServletRequest jsonRequest(String method, String path, String body) {
        MockHttpServletRequest r = new MockHttpServletRequest(method, path);
        r.setContentType("application/json");
        r.setContent(body.getBytes(StandardCharsets.UTF_8));
        return r;
    }

    private void sign(MockHttpServletRequest r, long ts) throws IOException {
        String body = new String(r.getContentAsByteArray(), StandardCharsets.UTF_8);
        String can = canonical(ts, r.getMethod(), r.getRequestURI(), body);
        r.addHeader("X-Internal-Timestamp", String.valueOf(ts));
        r.addHeader("X-Internal-Signature", hmac(SECRET, can));
    }

    private static String canonical(long ts, String method, String path, String body) {
        return ts + "\n" + method + "\n" + path + "\n" + sha256Hex(body);
    }

    private static String sha256Hex(String s) {
        try {
            return HEX.formatHex(
                    MessageDigest.getInstance("SHA-256")
                            .digest(s.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private static String hmac(String secret, String message) {
        try {
            Mac m = Mac.getInstance("HmacSHA256");
            m.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            return HEX.formatHex(m.doFinal(message.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
