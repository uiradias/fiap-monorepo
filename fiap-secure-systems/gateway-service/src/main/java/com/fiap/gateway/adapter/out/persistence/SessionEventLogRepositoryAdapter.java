package com.fiap.gateway.adapter.out.persistence;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.out.SessionEventLogRepositoryPort;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@Repository
public class SessionEventLogRepositoryAdapter implements SessionEventLogRepositoryPort {

    private final SessionEventLogJpaRepository repo;
    private final ObjectMapper mapper;

    public SessionEventLogRepositoryAdapter(SessionEventLogJpaRepository repo, ObjectMapper mapper) {
        this.repo = repo;
        this.mapper = mapper;
    }

    @Override
    @Transactional
    public boolean insertIfAbsent(SessionEventLogEntry entry) {
        String payloadJson;
        try { payloadJson = mapper.writeValueAsString(entry.payload()); }
        catch (JsonProcessingException e) { throw new IllegalStateException(e); }
        int rows = repo.insertIfAbsent(
                entry.eventId().value(),
                entry.sessionId().value(),
                entry.userId().value(),
                entry.fromStateOpt().map(Enum::name).orElse(null),
                entry.toState().name(),
                payloadJson,
                entry.occurredAt(),
                entry.receivedAt());
        return rows > 0;
    }

    @Override
    @Transactional(readOnly = true)
    @SuppressWarnings("unchecked")
    public List<SessionEventLogEntry> tailForSession(SessionId sessionId, int limit) {
        return repo.tailForSession(sessionId.value(), limit).stream().map(e -> {
            Map<String, Object> p;
            try { p = mapper.readValue(e.payload, Map.class); } catch (IOException ex) { p = Map.of(); }
            return new SessionEventLogEntry(
                    new EventId(e.eventId),
                    new SessionId(e.sessionId),
                    new UserId(e.userId),
                    e.fromState == null ? null : SessionState.valueOf(e.fromState),
                    SessionState.valueOf(e.toState),
                    p,
                    e.occurredAt,
                    e.receivedAt);
        }).toList();
    }
}
