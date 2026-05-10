package com.fiap.gateway.adapter.in.websocket;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.domain.model.SessionId;
import com.fiap.gateway.domain.port.out.SessionEventLogRepositoryPort;
import com.fiap.gateway.domain.port.out.SessionProjectionRepositoryPort;

public class SessionEventsWsHandler extends TextWebSocketHandler {

    private static final Logger log = LoggerFactory.getLogger(SessionEventsWsHandler.class);

    private final InProcessSessionEventBroadcaster broadcaster;
    private final SessionEventLogRepositoryPort eventLog;
    private final SessionProjectionRepositoryPort projections;
    private final ObjectMapper mapper;
    private final int snapshotEvents;

    public SessionEventsWsHandler(
            InProcessSessionEventBroadcaster broadcaster,
            SessionEventLogRepositoryPort eventLog,
            SessionProjectionRepositoryPort projections,
            ObjectMapper mapper,
            int snapshotEvents) {
        this.broadcaster = broadcaster;
        this.eventLog = eventLog;
        this.projections = projections;
        this.mapper = mapper;
        this.snapshotEvents = snapshotEvents;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession ws) throws Exception {
        SessionId sid = (SessionId) ws.getAttributes().get(JwtHandshakeInterceptor.ATTR_SESSION_ID);
        broadcaster.subscribe(sid, ws);
        sendSnapshot(ws, sid);

        // If the session is already terminal, send the snapshot and close cleanly.
        var p = projections.findById(sid).orElse(null);
        if (p != null && p.state().isTerminal()) {
            try {
                ws.close(CloseStatus.NORMAL);
            } catch (Exception ignored) {
            }
        }
    }

    private void sendSnapshot(WebSocketSession ws, SessionId sid) {
        List<Map<String, Object>> tail =
                eventLog.tailForSession(sid, snapshotEvents).stream()
                        .map(
                                e -> {
                                    Map<String, Object> m = new HashMap<>();
                                    m.put("eventId", e.eventId().value().toString());
                                    m.put("sessionId", e.sessionId().value().toString());
                                    m.put(
                                            "fromState",
                                            e.fromStateOpt().map(Enum::name).orElse(null));
                                    m.put("toState", e.toState().name());
                                    m.put("payload", e.payload());
                                    m.put("occurredAt", e.occurredAt().toString());
                                    return m;
                                })
                        .collect(Collectors.toList());
        try {
            String frame =
                    mapper.writeValueAsString(
                            Map.of(
                                    "type",
                                    "session.snapshot",
                                    "sessionId",
                                    sid.value().toString(),
                                    "events",
                                    tail));
            ws.sendMessage(new TextMessage(frame));
        } catch (Exception ex) {
            log.warn("failed to send snapshot for session {}", sid, ex);
        }
    }

    @Override
    protected void handleTextMessage(WebSocketSession ws, TextMessage message) {
        // Client → server: ignore everything except optional "pong" frames.
        // Cancellation goes through REST.
    }

    @Override
    public void afterConnectionClosed(WebSocketSession ws, CloseStatus status) {
        SessionId sid = (SessionId) ws.getAttributes().get(JwtHandshakeInterceptor.ATTR_SESSION_ID);
        if (sid != null) broadcaster.unsubscribe(sid, ws);
    }
}
