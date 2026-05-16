package com.fiap.orchestrator.application.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.infrastructure.observability.SessionMetrics;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;

class HandleAnalysisFailedServiceTest {

    InMemoryFakes.SessionRepoFake repo = new InMemoryFakes.SessionRepoFake();
    InMemoryFakes.OutboxFake outbox = new InMemoryFakes.OutboxFake();
    InMemoryFakes.ProcessedResultsFake dedup = new InMemoryFakes.ProcessedResultsFake();
    InMemoryFakes.TestClock clock = new InMemoryFakes.TestClock();
    SessionMetrics metrics = new SessionMetrics(new SimpleMeterRegistry());
    HandleAnalysisFailedService svc;

    @BeforeEach
    void setup() {
        svc = new HandleAnalysisFailedService(repo, outbox, dedup, clock, metrics);
    }

    @Test
    void failed_drives_to_FAILED_and_records_reason() {
        SessionId sid = new SessionId(UUID.randomUUID());
        Session s = Session.newSession(sid, new UserId(UUID.randomUUID()), 1, clock.now());
        s = s.withState(SessionState.QUEUED_FOR_ANALYSIS, clock.now());
        s = s.withState(SessionState.ANALYZING, clock.now());
        repo.store.put(sid.value(), s);

        AnalysisOutcome out =
                new AnalysisOutcome(
                        new JobId(UUID.randomUUID()),
                        sid,
                        AnalysisStatus.FAILED,
                        null,
                        null,
                        new AnalysisFailure("MODEL_RATE_LIMITED", "exhausted"),
                        clock.now());

        svc.onFailed(out);

        Session after = repo.store.get(sid.value());
        assertThat(after.state()).isEqualTo(SessionState.FAILED);
        assertThat(after.failureReason()).isEqualTo("MODEL_RATE_LIMITED");
    }
}
