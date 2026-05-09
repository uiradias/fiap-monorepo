package com.fiap.orchestrator.adapter.out.persistence;

import com.fiap.orchestrator.domain.model.*;
import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "session_events")
public class SessionEventEntity {

    @Id
    private UUID id;

    @Column(name = "session_id", nullable = false)
    private UUID sessionId;

    @Enumerated(EnumType.STRING)
    @Column(name = "from_state")
    private SessionState fromState;

    @Enumerated(EnumType.STRING)
    @Column(name = "to_state", nullable = false)
    private SessionState toState;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "payload", nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> payload;

    @Column(name = "occurred_at", nullable = false)
    private Instant occurredAt;

    @Column(name = "published_at")
    private Instant publishedAt;

    public SessionEventEntity() {}

    public static SessionEventEntity from(SessionEvent e) {
        SessionEventEntity x = new SessionEventEntity();
        x.id = e.id().value();
        x.sessionId = e.sessionId().value();
        x.fromState = e.fromState();
        x.toState = e.toState();
        x.payload = Map.copyOf(e.payload());
        x.occurredAt = e.occurredAt();
        return x;
    }

    public SessionEvent toDomain() {
        if (fromState == null) {
            return SessionEvent.initial(
                    new EventId(id), new SessionId(sessionId), toState, payload, occurredAt);
        }
        return SessionEvent.transition(
                new EventId(id), new SessionId(sessionId), fromState, toState, payload, occurredAt);
    }
}
