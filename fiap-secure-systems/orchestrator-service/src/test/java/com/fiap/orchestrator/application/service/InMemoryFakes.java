package com.fiap.orchestrator.application.service;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.out.*;

public class InMemoryFakes {

    public static class SessionRepoFake implements SessionRepositoryPort {
        public final Map<UUID, Session> store = new ConcurrentHashMap<>();
        public final List<SessionEvent> events = Collections.synchronizedList(new ArrayList<>());

        @Override
        public Optional<Session> findById(SessionId id) {
            return Optional.ofNullable(store.get(id.value()));
        }

        @Override
        public Session insertIfAbsent(Session session) {
            return store.computeIfAbsent(session.id().value(), k -> session);
        }

        @Override
        public Session save(Session session) {
            Session existing = store.get(session.id().value());
            if (existing == null) throw new IllegalStateException("not found");
            if (existing.version() != session.version() - 1) {
                throw new org.springframework.dao.OptimisticLockingFailureException(
                        "version mismatch (expected %d, got %d)"
                                .formatted(existing.version(), session.version() - 1));
            }
            store.put(session.id().value(), session);
            return session;
        }

        @Override
        public void appendEvent(SessionEvent event) {
            events.add(event);
        }
    }

    public static class ReportRepoFake implements ReportRepositoryPort {
        public final Map<UUID, AnalysisReport> store = new ConcurrentHashMap<>();

        @Override
        public Optional<AnalysisReport> findBySessionId(SessionId sessionId) {
            return Optional.ofNullable(store.get(sessionId.value()));
        }

        @Override
        public AnalysisReport save(AnalysisReport r) {
            store.put(r.sessionId().value(), r);
            return r;
        }
    }

    public static class OutboxFake implements OutboxPort {
        public final List<OutboxEntry> rows = Collections.synchronizedList(new ArrayList<>());

        @Override
        public void append(
                SessionId aggregateId,
                Destination destination,
                String eventType,
                Map<String, Object> payload,
                Instant now) {
            rows.add(
                    new OutboxEntry(
                            UUID.randomUUID(),
                            aggregateId,
                            destination,
                            eventType,
                            Map.copyOf(payload),
                            now,
                            0,
                            null));
        }

        @Override
        public List<OutboxEntry> fetchUnpublished(int limit) {
            return List.copyOf(rows);
        }

        @Override
        public void markPublished(UUID id, Instant now) {}

        @Override
        public void recordFailure(UUID id, String errorMessage) {}

        @Override
        public long countUnpublished() {
            return rows.size();
        }
    }

    public static class ProcessedResultsFake implements ProcessedResultsPort {
        public final Set<String> seen = ConcurrentHashMap.newKeySet();

        @Override
        public boolean recordIfAbsent(JobId jobId, AnalysisStatus status, Instant at) {
            return seen.add(jobId.value() + ":" + status);
        }
    }

    public static class TestClock implements Clock {
        public Instant now = Instant.parse("2026-01-01T00:00:00Z");

        @Override
        public Instant now() {
            return now;
        }

        public void advance(java.time.Duration d) {
            now = now.plus(d);
        }
    }
}
