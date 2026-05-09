package com.fiap.gateway.adapter.in.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.application.service.InMemoryFakes;
import com.fiap.gateway.domain.model.*;
import org.junit.jupiter.api.Test;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class SessionEventsWsHandlerTest {

    private final InMemoryFakes.FakeEventLog log = new InMemoryFakes.FakeEventLog();
    private final InMemoryFakes.FakeProjections proj = new InMemoryFakes.FakeProjections();
    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    void on_open_sends_snapshot_then_subscribes() throws Exception {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        proj.upsert(SessionProjection.initial(sid, uid, SessionState.QUEUED_FOR_ANALYSIS, Instant.now()));
        log.insertIfAbsent(new SessionEventLogEntry(
                new EventId(UUID.randomUUID()), sid, uid, null, SessionState.ASSETS_UPLOADED,
                Map.of(), Instant.now(), Instant.now()));

        InProcessSessionEventBroadcaster bcast = new InProcessSessionEventBroadcaster(mapper);
        SessionEventsWsHandler handler = new SessionEventsWsHandler(bcast, log, proj, mapper, 50);

        WebSocketSession ws = mock(WebSocketSession.class);
        when(ws.isOpen()).thenReturn(true);
        Map<String, Object> attrs = new HashMap<>();
        attrs.put(JwtHandshakeInterceptor.ATTR_SESSION_ID, sid);
        attrs.put(JwtHandshakeInterceptor.ATTR_USER_ID, uid);
        when(ws.getAttributes()).thenReturn(attrs);

        handler.afterConnectionEstablished(ws);

        verify(ws, atLeastOnce()).sendMessage(any(TextMessage.class));
        assertThat(bcast.subscribersFor(sid)).contains(ws);
    }

    @Test
    void broadcasts_event_to_subscribed_sockets() throws Exception {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        InProcessSessionEventBroadcaster bcast = new InProcessSessionEventBroadcaster(mapper);

        WebSocketSession ws = mock(WebSocketSession.class);
        when(ws.isOpen()).thenReturn(true);
        bcast.subscribe(sid, ws);

        bcast.broadcast(new SessionEventLogEntry(
                new EventId(UUID.randomUUID()), sid, uid,
                SessionState.ASSETS_UPLOADED, SessionState.QUEUED_FOR_ANALYSIS,
                Map.of(), Instant.now(), Instant.now()));

        verify(ws, times(1)).sendMessage(any(TextMessage.class));
    }
}
