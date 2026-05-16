package com.fiap.gateway.adapter.in.websocket;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.domain.port.out.SessionEventLogRepositoryPort;
import com.fiap.gateway.domain.port.out.SessionProjectionRepositoryPort;
import com.fiap.gateway.domain.port.out.TokenIssuerPort;

import io.micrometer.core.instrument.MeterRegistry;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final TokenIssuerPort tokens;
    private final SessionProjectionRepositoryPort projections;
    private final SessionEventLogRepositoryPort eventLog;
    private final ObjectMapper mapper;
    private final MeterRegistry meterRegistry;
    private final int snapshotEvents;

    public WebSocketConfig(
            TokenIssuerPort tokens,
            SessionProjectionRepositoryPort projections,
            SessionEventLogRepositoryPort eventLog,
            ObjectMapper mapper,
            MeterRegistry meterRegistry,
            @Value("${gateway.websocket.snapshot-events:50}") int snapshotEvents) {
        this.tokens = tokens;
        this.projections = projections;
        this.eventLog = eventLog;
        this.mapper = mapper;
        this.meterRegistry = meterRegistry;
        this.snapshotEvents = snapshotEvents;
    }

    @Bean
    public InProcessSessionEventBroadcaster sessionEventBroadcaster() {
        return new InProcessSessionEventBroadcaster(mapper, meterRegistry);
    }

    @Bean
    public SessionEventsWsHandler sessionEventsWsHandler(
            InProcessSessionEventBroadcaster broadcaster) {
        return new SessionEventsWsHandler(
                broadcaster, eventLog, projections, mapper, snapshotEvents);
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(
                        sessionEventsWsHandler(sessionEventBroadcaster()),
                        "/ws/sessions/{sessionId}")
                .addInterceptors(new JwtHandshakeInterceptor(tokens, projections))
                .setAllowedOrigins("*");
    }
}
