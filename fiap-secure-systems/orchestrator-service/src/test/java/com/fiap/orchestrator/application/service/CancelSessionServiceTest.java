package com.fiap.orchestrator.application.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.statemachine.IllegalSessionTransitionException;

class CancelSessionServiceTest {

    InMemoryFakes.SessionRepoFake repo = new InMemoryFakes.SessionRepoFake();
    InMemoryFakes.OutboxFake outbox = new InMemoryFakes.OutboxFake();
    InMemoryFakes.TestClock clock = new InMemoryFakes.TestClock();
    CancelSessionService svc;

    @BeforeEach
    void setup() {
        svc = new CancelSessionService(repo, outbox, clock);
    }

    @Test
    void cancel_from_non_terminal_succeeds() {
        SessionId sid = new SessionId(UUID.randomUUID());
        Session s = Session.newSession(sid, new UserId(UUID.randomUUID()), 1, clock.now());
        repo.store.put(sid.value(), s);
        svc.cancel(sid);
        assertThat(repo.store.get(sid.value()).state()).isEqualTo(SessionState.CANCELED);
    }

    @Test
    void cancel_from_terminal_throws() {
        SessionId sid = new SessionId(UUID.randomUUID());
        Session s =
                Session.newSession(sid, new UserId(UUID.randomUUID()), 1, clock.now())
                        .withState(SessionState.QUEUED_FOR_ANALYSIS, clock.now())
                        .withState(SessionState.ANALYZING, clock.now())
                        .withState(SessionState.ANALYSIS_COMPLETED, clock.now())
                        .withState(SessionState.REPORT_READY, clock.now());
        repo.store.put(sid.value(), s);
        assertThatThrownBy(() -> svc.cancel(sid))
                .isInstanceOf(IllegalSessionTransitionException.class);
    }
}
