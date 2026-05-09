package com.fiap.gateway.adapter.in.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.domain.model.SessionEventLogEntry;
import com.fiap.gateway.domain.model.SessionId;
import com.fiap.gateway.domain.port.out.SessionEventBroadcastPort;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

public class InProcessSessionEventBroadcaster implements SessionEventBroadcastPort {

    private static final Logger log = LoggerFactory.getLogger(InProcessSessionEventBroadcaster.class);

    private final Map<SessionId, CopyOnWriteArrayList<WebSocketSession>> subscribers = new ConcurrentHashMap<>();
    private final ObjectMapper mapper;

    public InProcessSessionEventBroadcaster(ObjectMapper mapper) {
        this.mapper = mapper;
    }

    public void subscribe(SessionId sid, WebSocketSession ws) {
        subscribers.computeIfAbsent(sid, s -> new CopyOnWriteArrayList<>()).add(ws);
    }

    public void unsubscribe(SessionId sid, WebSocketSession ws) {
        var list = subscribers.get(sid);
        if (list != null) list.remove(ws);
    }

    public List<WebSocketSession> subscribersFor(SessionId sid) {
        return subscribers.getOrDefault(sid, new CopyOnWriteArrayList<>());
    }

    @Override
    public void broadcast(SessionEventLogEntry e) {
        List<WebSocketSession> list = subscribers.get(e.sessionId());
        if (list == null || list.isEmpty()) return;
        String frame;
        try {
            Map<String, Object> data = new HashMap<>();
            data.put("type", "session.event");
            data.put("eventId", e.eventId().value().toString());
            data.put("sessionId", e.sessionId().value().toString());
            data.put("fromState", e.fromStateOpt().map(Enum::name).orElse(null));
            data.put("toState", e.toState().name());
            data.put("payload", e.payload());
            data.put("occurredAt", e.occurredAt().toString());
            frame = mapper.writeValueAsString(data);
        } catch (Exception ex) {
            log.warn("failed to serialize WS event for session {}", e.sessionId(), ex);
            return;
        }
        for (WebSocketSession s : list) {
            try {
                if (s.isOpen()) s.sendMessage(new TextMessage(frame));
            } catch (Exception sendErr) {
                log.warn("WS send failed for session {}; closing socket", e.sessionId(), sendErr);
                try { s.close(); } catch (Exception ignored) {}
            }
        }
    }
}
