package com.fiap.orchestrator.domain.port.out;

import com.fiap.orchestrator.domain.model.Session;
import com.fiap.orchestrator.domain.model.SessionEvent;
import com.fiap.orchestrator.domain.model.SessionId;

import java.util.Optional;

public interface SessionRepositoryPort {
    Optional<Session> findById(SessionId id);
    Session insertIfAbsent(Session session);
    Session save(Session session);
    void appendEvent(SessionEvent event);
}
