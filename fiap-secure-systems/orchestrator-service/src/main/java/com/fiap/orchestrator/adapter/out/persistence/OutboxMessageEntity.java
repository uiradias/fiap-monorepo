package com.fiap.orchestrator.adapter.out.persistence;

import com.fiap.orchestrator.domain.port.out.OutboxPort;
import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "outbox_messages")
public class OutboxMessageEntity {

    @Id
    private UUID id;

    @Column(name = "aggregate_id", nullable = false)
    private UUID aggregateId;

    @Enumerated(EnumType.STRING)
    @Column(name = "destination", nullable = false)
    private OutboxPort.Destination destination;

    @Column(name = "event_type", nullable = false)
    private String eventType;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "payload", nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> payload;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "published_at")
    private Instant publishedAt;

    @Column(nullable = false)
    private int attempts;

    @Column(name = "last_error")
    private String lastError;

    public OutboxMessageEntity() {}

    public static OutboxMessageEntity create(
            UUID id, UUID aggregateId, OutboxPort.Destination destination,
            String eventType, Map<String, Object> payload, Instant createdAt) {
        OutboxMessageEntity e = new OutboxMessageEntity();
        e.id = id;
        e.aggregateId = aggregateId;
        e.destination = destination;
        e.eventType = eventType;
        e.payload = Map.copyOf(payload);
        e.createdAt = createdAt;
        e.attempts = 0;
        return e;
    }

    public UUID getId() { return id; }
    public UUID getAggregateId() { return aggregateId; }
    public OutboxPort.Destination getDestination() { return destination; }
    public String getEventType() { return eventType; }
    public Map<String, Object> getPayload() { return payload; }
    public Instant getCreatedAt() { return createdAt; }
    public Instant getPublishedAt() { return publishedAt; }
    public int getAttempts() { return attempts; }
    public String getLastError() { return lastError; }

    void markPublished(Instant now) { this.publishedAt = now; }
    void recordFailure(String err) { this.attempts += 1; this.lastError = err; }
}
