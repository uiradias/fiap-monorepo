package com.fiap.orchestrator.adapter.out.persistence;

import com.fiap.orchestrator.domain.model.Session;
import com.fiap.orchestrator.domain.model.SessionEvent;
import com.fiap.orchestrator.domain.model.SessionId;
import com.fiap.orchestrator.domain.port.out.SessionRepositoryPort;
import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public class SessionRepositoryAdapter implements SessionRepositoryPort {

    private final SessionJpaRepository sessions;
    private final SessionEventJpaRepository events;

    public SessionRepositoryAdapter(SessionJpaRepository sessions, SessionEventJpaRepository events) {
        this.sessions = sessions;
        this.events = events;
    }

    @Override
    public Optional<Session> findById(SessionId id) {
        return sessions.findById(id.value()).map(SessionEntity::toDomain);
    }

    @Override
    public Session insertIfAbsent(Session session) {
        Optional<SessionEntity> existing = sessions.findById(session.id().value());
        if (existing.isPresent()) {
            return existing.get().toDomain();
        }
        return sessions.save(SessionEntity.from(session)).toDomain();
    }

    @Override
    public Session save(Session session) {
        // The domain Session's version is the post-save version (Session.withState bumps it).
        // We re-load the managed entity (whose .version is the CURRENT DB version), then verify
        // it equals session.version()-1 — i.e., the caller's read is still fresh.
        // Hibernate's @Version alone doesn't fire here because findById re-reads inside this
        // transaction, so we'd otherwise lose the stale-read signal. The explicit check below
        // restores it.
        SessionEntity managed = sessions.findById(session.id().value())
                .orElseThrow(() -> new IllegalStateException("session not found: " + session.id()));
        long expectedDbVersion = session.version() - 1;
        if (managed.getVersion() != expectedDbVersion) {
            throw new OptimisticLockingFailureException(
                    "version mismatch for session %s: expected DB version %d, got %d"
                            .formatted(session.id(), expectedDbVersion, managed.getVersion()));
        }
        managed.setState(session.state());
        managed.setUpdatedAt(session.updatedAt());
        managed.setFailureReason(session.failureReason());
        return sessions.saveAndFlush(managed).toDomain();
    }

    @Override
    public void appendEvent(SessionEvent event) {
        events.save(SessionEventEntity.from(event));
    }
}
