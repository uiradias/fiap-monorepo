package com.fiap.gateway.adapter.in.websocket;

import com.fiap.gateway.domain.exception.InvalidTokenException;
import com.fiap.gateway.domain.model.SessionId;
import com.fiap.gateway.domain.model.UserId;
import com.fiap.gateway.domain.port.out.SessionProjectionRepositoryPort;
import com.fiap.gateway.domain.port.out.TokenIssuerPort;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.server.HandshakeInterceptor;

import java.net.URI;
import java.util.Map;
import java.util.UUID;

public class JwtHandshakeInterceptor implements HandshakeInterceptor {

    public static final String ATTR_USER_ID = "userId";
    public static final String ATTR_SESSION_ID = "sessionId";

    private final TokenIssuerPort tokens;
    private final SessionProjectionRepositoryPort projections;

    public JwtHandshakeInterceptor(TokenIssuerPort tokens, SessionProjectionRepositoryPort projections) {
        this.tokens = tokens;
        this.projections = projections;
    }

    @Override
    public boolean beforeHandshake(ServerHttpRequest request, ServerHttpResponse response,
                                   WebSocketHandler wsHandler, Map<String, Object> attributes) {
        URI uri = request.getURI();
        String token = queryParam(uri, "token");
        if (token == null) {
            return reject(response, HttpStatus.UNAUTHORIZED);
        }
        UserId uid;
        try { uid = tokens.verifyAccessToken(token); }
        catch (InvalidTokenException ite) { return reject(response, HttpStatus.UNAUTHORIZED); }

        String path = request.getURI().getPath();      // /ws/sessions/{id}
        SessionId sid;
        try { sid = new SessionId(UUID.fromString(path.substring(path.lastIndexOf('/') + 1))); }
        catch (IllegalArgumentException iae) { return reject(response, HttpStatus.BAD_REQUEST); }

        var p = projections.findById(sid);
        if (p.isEmpty()) return reject(response, HttpStatus.NOT_FOUND);
        if (!p.get().userId().equals(uid)) return reject(response, HttpStatus.FORBIDDEN);

        attributes.put(ATTR_USER_ID, uid);
        attributes.put(ATTR_SESSION_ID, sid);
        return true;
    }

    @Override
    public void afterHandshake(ServerHttpRequest req, ServerHttpResponse res,
                               WebSocketHandler h, Exception ex) {}

    private static boolean reject(ServerHttpResponse response, HttpStatus status) {
        response.setStatusCode(status);
        return false;
    }

    private static String queryParam(URI uri, String name) {
        String q = uri.getQuery();
        if (q == null) return null;
        for (String part : q.split("&")) {
            int eq = part.indexOf('=');
            if (eq > 0 && part.substring(0, eq).equals(name)) {
                return java.net.URLDecoder.decode(part.substring(eq + 1), java.nio.charset.StandardCharsets.UTF_8);
            }
        }
        return null;
    }
}
