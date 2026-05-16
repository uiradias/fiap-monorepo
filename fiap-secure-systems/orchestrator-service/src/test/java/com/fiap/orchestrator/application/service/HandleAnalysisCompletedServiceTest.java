package com.fiap.orchestrator.application.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.infrastructure.observability.SessionMetrics;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;

class HandleAnalysisCompletedServiceTest {

    InMemoryFakes.SessionRepoFake repo = new InMemoryFakes.SessionRepoFake();
    InMemoryFakes.ReportRepoFake reports = new InMemoryFakes.ReportRepoFake();
    InMemoryFakes.OutboxFake outbox = new InMemoryFakes.OutboxFake();
    InMemoryFakes.ProcessedResultsFake dedup = new InMemoryFakes.ProcessedResultsFake();
    InMemoryFakes.TestClock clock = new InMemoryFakes.TestClock();
    SessionMetrics metrics = new SessionMetrics(new SimpleMeterRegistry());
    HandleAnalysisCompletedService svc;

    @BeforeEach
    void setup() {
        svc = new HandleAnalysisCompletedService(repo, reports, outbox, dedup, clock, metrics);
    }

    private static Map<String, Object> reportPayload(String summary) {
        return Map.of(
                "summary", summary,
                "components", List.of(),
                "risks", List.of(),
                "improvements", List.of(),
                "strengths", List.of(),
                "confidence", "high",
                "model_metadata", Map.of("model", "claude-sonnet-4-6"));
    }

    @Test
    void succeeded_persists_report_and_walks_to_REPORT_READY() {
        SessionId sid = new SessionId(UUID.randomUUID());
        Session s = Session.newSession(sid, new UserId(UUID.randomUUID()), 1, clock.now());
        s = s.withState(SessionState.QUEUED_FOR_ANALYSIS, clock.now());
        s = s.withState(SessionState.ANALYZING, clock.now());
        repo.store.put(sid.value(), s);

        AnalysisOutcome out =
                new AnalysisOutcome(
                        new JobId(UUID.randomUUID()),
                        sid,
                        AnalysisStatus.SUCCEEDED,
                        reportPayload("hello"),
                        Map.of(
                                "model",
                                "claude-sonnet-4-6",
                                "tokensIn",
                                10,
                                "tokensOut",
                                20,
                                "durationMs",
                                100),
                        null,
                        clock.now());

        svc.onSucceeded(out);

        assertThat(repo.store.get(sid.value()).state()).isEqualTo(SessionState.REPORT_READY);
        assertThat(reports.store).containsKey(sid.value());
        assertThat(repo.events)
                .extracting("toState")
                .containsExactly(SessionState.ANALYSIS_COMPLETED, SessionState.REPORT_READY);
        assertThat(outbox.rows).hasSize(2);
    }
}
