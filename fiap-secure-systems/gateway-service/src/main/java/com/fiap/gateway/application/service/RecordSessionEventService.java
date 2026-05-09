package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.RecordSessionEventUseCase;
import com.fiap.gateway.domain.port.out.SessionEventBroadcastPort;
import com.fiap.gateway.domain.port.out.SessionEventLogRepositoryPort;
import com.fiap.gateway.domain.port.out.SessionProjectionRepositoryPort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Map;

@Service
public class RecordSessionEventService implements RecordSessionEventUseCase {

    private final SessionEventLogRepositoryPort log;
    private final SessionProjectionRepositoryPort projections;
    private final SessionEventBroadcastPort broadcaster;

    public RecordSessionEventService(SessionEventLogRepositoryPort log,
                                     SessionProjectionRepositoryPort projections,
                                     SessionEventBroadcastPort broadcaster) {
        this.log = log;
        this.projections = projections;
        this.broadcaster = broadcaster;
    }

    @Override
    @Transactional
    public boolean record(EventId eventId, SessionId sessionId, UserId userId,
                          SessionState fromState, SessionState toState,
                          Map<String, Object> payload,
                          Instant occurredAt, Instant receivedAt) {
        SessionEventLogEntry entry = new SessionEventLogEntry(
                eventId, sessionId, userId, fromState, toState, payload, occurredAt, receivedAt);
        boolean inserted = log.insertIfAbsent(entry);
        if (!inserted) return false;

        SessionProjection p = projections.findById(sessionId)
                .orElseGet(() -> SessionProjection.initial(sessionId, userId, toState, occurredAt));
        projections.upsert(p.applyEvent(entry));

        broadcaster.broadcast(entry);
        return true;
    }
}
