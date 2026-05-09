package com.fiap.orchestrator.adapter.in.security;

import com.fiap.orchestrator.application.service.Clock;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ReadListener;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletInputStream;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletRequestWrapper;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.filter.OncePerRequestFilter;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.io.BufferedReader;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;

public class InternalHmacFilter extends OncePerRequestFilter {

    private static final List<String> WHITELIST = List.of(
            "/actuator/health", "/actuator/info");
    private static final HexFormat HEX = HexFormat.of();

    private final byte[] secret;
    private final int replayWindowSeconds;
    private final Clock clock;

    public InternalHmacFilter(String secret, int replayWindowSeconds, Clock clock) {
        if (secret == null || secret.length() < 16) {
            throw new IllegalArgumentException("INTERNAL_HMAC_SECRET too short (min 16 chars)");
        }
        this.secret = secret.getBytes(StandardCharsets.UTF_8);
        this.replayWindowSeconds = replayWindowSeconds;
        this.clock = clock;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {

        String path = request.getRequestURI();
        if (WHITELIST.stream().anyMatch(path::startsWith)) {
            chain.doFilter(request, response);
            return;
        }

        String tsHeader = request.getHeader("X-Internal-Timestamp");
        String sigHeader = request.getHeader("X-Internal-Signature");
        if (tsHeader == null || sigHeader == null) {
            problem(response, "missing X-Internal-Timestamp or X-Internal-Signature");
            return;
        }
        long ts;
        try {
            ts = Long.parseLong(tsHeader);
        } catch (NumberFormatException nfe) {
            problem(response, "invalid X-Internal-Timestamp");
            return;
        }
        long now = clock.now().getEpochSecond();
        if (Math.abs(now - ts) > replayWindowSeconds) {
            problem(response, "X-Internal-Timestamp outside replay window");
            return;
        }

        byte[] bodyBytes = request.getInputStream().readAllBytes();
        String body = new String(bodyBytes, StandardCharsets.UTF_8);
        String canonical = ts + "\n" + request.getMethod() + "\n" + path + "\n" + sha256Hex(body);
        String expected = hmacHex(canonical);

        if (!constantTimeEquals(expected, sigHeader)) {
            problem(response, "invalid X-Internal-Signature");
            return;
        }
        chain.doFilter(new CachedBodyRequest(request, bodyBytes), response);
    }

    private static final class CachedBodyRequest extends HttpServletRequestWrapper {
        private final byte[] cachedBody;

        CachedBodyRequest(HttpServletRequest delegate, byte[] cachedBody) {
            super(delegate);
            this.cachedBody = cachedBody;
        }

        @Override public ServletInputStream getInputStream() {
            ByteArrayInputStream inner = new ByteArrayInputStream(cachedBody);
            return new ServletInputStream() {
                @Override public boolean isFinished() { return inner.available() == 0; }
                @Override public boolean isReady() { return true; }
                @Override public void setReadListener(ReadListener readListener) {}
                @Override public int read() { return inner.read(); }
            };
        }

        @Override public BufferedReader getReader() {
            return new BufferedReader(new InputStreamReader(getInputStream(), StandardCharsets.UTF_8));
        }
    }

    private static boolean constantTimeEquals(String a, String b) {
        if (a == null || b == null) return false;
        return MessageDigest.isEqual(
                a.getBytes(StandardCharsets.UTF_8), b.getBytes(StandardCharsets.UTF_8));
    }

    private static String sha256Hex(String s) {
        try {
            return HEX.formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(s.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    private String hmacHex(String message) {
        try {
            Mac m = Mac.getInstance("HmacSHA256");
            m.init(new SecretKeySpec(secret, "HmacSHA256"));
            return HEX.formatHex(m.doFinal(message.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    private static void problem(HttpServletResponse response, String detail) throws IOException {
        response.setStatus(401);
        response.setContentType("application/problem+json");
        String body = """
                {"type":"about:blank","title":"Unauthorized","status":401,"detail":"%s","code":"INTERNAL_HMAC_REJECTED"}
                """.formatted(detail.replace("\"", "\\\""));
        response.getWriter().write(body);
    }
}
