package com.fiap.orchestrator.adapter.in.security;

import com.fiap.orchestrator.application.service.Clock;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.util.ContentCachingRequestWrapper;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.io.IOException;
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

        ContentCachingRequestWrapper cached = new ContentCachingRequestWrapper(request);

        String tsHeader = cached.getHeader("X-Internal-Timestamp");
        String sigHeader = cached.getHeader("X-Internal-Signature");
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

        // Force the cache by reading the underlying stream first.
        cached.getInputStream().readAllBytes();
        String body = new String(cached.getContentAsByteArray(), StandardCharsets.UTF_8);
        String canonical = ts + "\n" + cached.getMethod() + "\n" + path + "\n" + sha256Hex(body);
        String expected = hmacHex(canonical);

        if (!constantTimeEquals(expected, sigHeader)) {
            problem(response, "invalid X-Internal-Signature");
            return;
        }
        chain.doFilter(cached, response);
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
