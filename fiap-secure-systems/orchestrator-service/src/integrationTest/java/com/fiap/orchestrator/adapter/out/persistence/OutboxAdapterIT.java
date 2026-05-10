package com.fiap.orchestrator.adapter.out.persistence;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import com.fiap.orchestrator.PostgresTestcontainersBase;
import com.fiap.orchestrator.domain.model.SessionId;
import com.fiap.orchestrator.domain.port.out.OutboxPort;

class OutboxAdapterIT extends PostgresTestcontainersBase {

    @Autowired OutboxAdapter outbox;

    @Test
    void append_then_fetchUnpublished_returns_in_createdAt_order() {
        SessionId sid = new SessionId(UUID.randomUUID());
        Instant t0 = Instant.now();
        outbox.append(
                sid,
                OutboxPort.Destination.SQS_ANALYSIS_JOBS,
                "AnalysisJobRequested",
                Map.of("k", "1"),
                t0);
        outbox.append(
                sid,
                OutboxPort.Destination.SNS_SESSION_EVENTS,
                "SessionStateChanged",
                Map.of("k", "2"),
                t0.plusMillis(1));

        List<OutboxPort.OutboxEntry> entries = outbox.fetchUnpublished(10);
        assertThat(entries).hasSizeGreaterThanOrEqualTo(2);
        OutboxPort.OutboxEntry first =
                entries.stream().filter(e -> e.aggregateId().equals(sid)).findFirst().orElseThrow();
        assertThat(first.eventType()).isEqualTo("AnalysisJobRequested");
    }

    @Test
    void markPublished_excludes_from_unpublished() {
        SessionId sid = new SessionId(UUID.randomUUID());
        outbox.append(
                sid,
                OutboxPort.Destination.SQS_ANALYSIS_JOBS,
                "AnalysisJobRequested",
                Map.of("k", "v"),
                Instant.now());

        OutboxPort.OutboxEntry e =
                outbox.fetchUnpublished(50).stream()
                        .filter(x -> x.aggregateId().equals(sid))
                        .findFirst()
                        .orElseThrow();
        outbox.markPublished(e.id(), Instant.now());

        boolean stillUnpublished =
                outbox.fetchUnpublished(50).stream().anyMatch(x -> x.id().equals(e.id()));
        assertThat(stillUnpublished).isFalse();
    }

    @Test
    void recordFailure_bumps_attempts() {
        SessionId sid = new SessionId(UUID.randomUUID());
        outbox.append(
                sid,
                OutboxPort.Destination.SQS_ANALYSIS_JOBS,
                "AnalysisJobRequested",
                Map.of("k", "v"),
                Instant.now());
        OutboxPort.OutboxEntry e =
                outbox.fetchUnpublished(50).stream()
                        .filter(x -> x.aggregateId().equals(sid))
                        .findFirst()
                        .orElseThrow();
        outbox.recordFailure(e.id(), "boom");
        outbox.recordFailure(e.id(), "boom2");
        OutboxPort.OutboxEntry refreshed =
                outbox.fetchUnpublished(50).stream()
                        .filter(x -> x.id().equals(e.id()))
                        .findFirst()
                        .orElseThrow();
        assertThat(refreshed.attempts()).isEqualTo(2);
        assertThat(refreshed.lastError()).isEqualTo("boom2");
    }
}
