package com.fiap.orchestrator.adapter.out.persistence;

import com.fiap.orchestrator.domain.model.Session;
import com.fiap.orchestrator.domain.model.SessionId;
import com.fiap.orchestrator.domain.model.SessionState;
import com.fiap.orchestrator.domain.model.UserId;
import jakarta.persistence.*;

import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "sessions")
public class SessionEntity {

    @Id
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SessionState state;

    @Column(name = "asset_count", nullable = false)
    private int assetCount;

    @Column(name = "failure_reason")
    private String failureReason;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @Version
    @Column(nullable = false)
    private long version;

    public SessionEntity() {}

    public static SessionEntity from(Session s) {
        SessionEntity e = new SessionEntity();
        e.id = s.id().value();
        e.userId = s.userId().value();
        e.state = s.state();
        e.assetCount = s.assetCount();
        e.failureReason = s.failureReason();
        e.createdAt = s.createdAt();
        e.updatedAt = s.updatedAt();
        e.version = s.version();
        return e;
    }

    public Session toDomain() {
        return new Session(
                new SessionId(id), new UserId(userId), state, assetCount,
                failureReason, createdAt, updatedAt, version);
    }

    public UUID getId() { return id; }
    public long getVersion() { return version; }
    public SessionState getState() { return state; }
    void setState(SessionState s) { this.state = s; }
    void setUpdatedAt(Instant t) { this.updatedAt = t; }
    void setFailureReason(String r) { this.failureReason = r; }
}
