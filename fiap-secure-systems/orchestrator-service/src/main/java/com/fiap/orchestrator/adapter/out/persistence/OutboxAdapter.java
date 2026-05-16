package com.fiap.orchestrator.adapter.out.persistence;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Repository;

import com.fiap.orchestrator.domain.model.SessionId;
import com.fiap.orchestrator.domain.port.out.OutboxPort;

@Repository
public class OutboxAdapter implements OutboxPort {

    private final OutboxJpaRepository outbox;

    public OutboxAdapter(OutboxJpaRepository outbox) {
        this.outbox = outbox;
    }

    @Override
    public void append(
            SessionId aggregateId,
            Destination destination,
            String eventType,
            Map<String, Object> payload,
            Instant now) {
        outbox.save(
                OutboxMessageEntity.create(
                        UUID.randomUUID(),
                        aggregateId.value(),
                        destination,
                        eventType,
                        payload,
                        now));
    }

    @Override
    public List<OutboxEntry> fetchUnpublished(int limit) {
        return outbox.findUnpublished(PageRequest.of(0, limit)).stream()
                .map(
                        e ->
                                new OutboxEntry(
                                        e.getId(),
                                        new SessionId(e.getAggregateId()),
                                        e.getDestination(),
                                        e.getEventType(),
                                        e.getPayload(),
                                        e.getCreatedAt(),
                                        e.getAttempts(),
                                        e.getLastError()))
                .toList();
    }

    @Override
    public void markPublished(UUID id, Instant now) {
        OutboxMessageEntity e =
                outbox.findById(id)
                        .orElseThrow(() -> new IllegalStateException("outbox row gone: " + id));
        e.markPublished(now);
        outbox.save(e);
    }

    @Override
    public void recordFailure(UUID id, String errorMessage) {
        OutboxMessageEntity e =
                outbox.findById(id)
                        .orElseThrow(() -> new IllegalStateException("outbox row gone: " + id));
        e.recordFailure(errorMessage);
        outbox.save(e);
    }

    @Override
    public long countUnpublished() {
        return outbox.countByPublishedAtIsNull();
    }
}
