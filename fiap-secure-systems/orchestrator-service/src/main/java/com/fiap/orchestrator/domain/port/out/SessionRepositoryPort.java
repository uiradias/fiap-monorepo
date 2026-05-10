package com.fiap.orchestrator.domain.port.out;

import java.util.Optional;

import com.fiap.orchestrator.domain.model.Session;
import com.fiap.orchestrator.domain.model.SessionEvent;
import com.fiap.orchestrator.domain.model.SessionId;

public interface SessionRepositoryPort {
    Optional<Session> findById(SessionId id);

    Session insertIfAbsent(Session session);

    Session save(Session session);

    void appendEvent(SessionEvent event);
}
