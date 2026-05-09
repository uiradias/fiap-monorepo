package com.fiap.gateway.adapter.in.ratelimit;

import com.fiap.gateway.infrastructure.config.RateLimitProperties;
import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class RateLimitFilter extends OncePerRequestFilter {

    private final ConcurrentHashMap<String, Bucket> buckets = new ConcurrentHashMap<>();
    private final int authedPerMinute;
    private final int anonPerMinute;

    public RateLimitFilter(RateLimitProperties props) {
        this.authedPerMinute = props.authedPerMinute();
        this.anonPerMinute = props.anonPerMinute();
    }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        if (!shouldRateLimit(req)) {
            chain.doFilter(req, res);
            return;
        }
        String key = clientKey(req);
        Bucket bucket = buckets.computeIfAbsent(key, k -> newBucket(req));
        if (bucket.tryConsume(1)) {
            chain.doFilter(req, res);
        } else {
            res.setStatus(HttpStatus.TOO_MANY_REQUESTS.value());
            res.setHeader("Retry-After", "60");
        }
    }

    private boolean shouldRateLimit(HttpServletRequest req) {
        String path = req.getRequestURI();
        String method = req.getMethod();
        if ("POST".equals(method) && path.equals("/api/v1/auth/login")) return true;
        if ("POST".equals(method) && path.startsWith("/api/v1/asset-bundles/") && path.endsWith("/assets")) return true;
        return false;
    }

    private Bucket newBucket(HttpServletRequest req) {
        boolean authed = req.getHeader("Authorization") != null;
        int rate = authed ? authedPerMinute : anonPerMinute;
        return Bucket.builder()
                .addLimit(Bandwidth.builder().capacity(rate).refillIntervally(rate, Duration.ofMinutes(1)).build())
                .build();
    }

    private String clientKey(HttpServletRequest req) {
        String auth = req.getHeader("Authorization");
        if (auth != null) return "u:" + auth;          // already namespaced by token
        String fwd = req.getHeader("X-Forwarded-For");
        return "ip:" + (fwd != null ? fwd.split(",")[0].trim() : req.getRemoteAddr());
    }
}
