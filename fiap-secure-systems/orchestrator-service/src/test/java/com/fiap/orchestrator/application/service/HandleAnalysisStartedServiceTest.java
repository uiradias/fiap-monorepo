package com.fiap.orchestrator.application.service;

import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.out.OutboxPort;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class HandleAnalysisStartedServiceTest {

    InMemoryFakes.SessionRepoFake repo = new InMemoryFakes.SessionRepoFake();
    InMemoryFakes.OutboxFake outbox = new InMemoryFakes.OutboxFake();
    InMemoryFakes.ProcessedResultsFake dedup = new InMemoryFakes.ProcessedResultsFake();
    InMemoryFakes.TestClock clock = new InMemoryFakes.TestClock();
    HandleAnalysisStartedService svc;

    @BeforeEach
    void setup() {
        svc = new HandleAnalysisStartedService(repo, outbox, dedup, clock);
    }

    private SessionId seed(SessionState start) {
        SessionId sid = new SessionId(UUID.randomUUID());
        Session s = Session.newSession(sid, new UserId(UUID.randomUUID()), 1, clock.now());
        if (start == SessionState.QUEUED_FOR_ANALYSIS) {
            s = s.withState(SessionState.QUEUED_FOR_ANALYSIS, clock.now());
        }
        repo.store.put(sid.value(), s);
        return sid;
    }

    @Test
    void started_advances_QUEUED_to_ANALYZING_and_emits_event() {
        SessionId sid = seed(SessionState.QUEUED_FOR_ANALYSIS);
        JobId job = new JobId(UUID.randomUUID());
        svc.onStarted(job, sid);
        assertThat(repo.store.get(sid.value()).state()).isEqualTo(SessionState.ANALYZING);
        assertThat(repo.events).singleElement()
                .satisfies(ev -> assertThat(ev.toState()).isEqualTo(SessionState.ANALYZING));
        assertThat(outbox.rows).hasSize(1);
        assertThat(outbox.rows.get(0).destination()).isEqualTo(OutboxPort.Destination.SNS_SESSION_EVENTS);
    }

    @Test
    void duplicate_started_is_silently_ignored() {
        SessionId sid = seed(SessionState.QUEUED_FOR_ANALYSIS);
        JobId job = new JobId(UUID.randomUUID());
        svc.onStarted(job, sid);
        svc.onStarted(job, sid);
        assertThat(repo.events).hasSize(1);
        assertThat(outbox.rows).hasSize(1);
    }
}
