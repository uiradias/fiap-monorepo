package com.fiap.orchestrator.application.service;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.in.CancelSessionUseCase;
import com.fiap.orchestrator.domain.port.out.OutboxPort;
import com.fiap.orchestrator.domain.port.out.SessionRepositoryPort;
import com.fiap.orchestrator.domain.statemachine.SessionStateMachine;
import com.fiap.orchestrator.domain.statemachine.Transition;

@Service
public class CancelSessionService implements CancelSessionUseCase {

    private final SessionRepositoryPort sessions;
    private final OutboxPort outbox;
    private final Clock clock;
    private final SessionStateMachine sm = new SessionStateMachine();

    public CancelSessionService(SessionRepositoryPort sessions, OutboxPort outbox, Clock clock) {
        this.sessions = sessions;
        this.outbox = outbox;
        this.clock = clock;
    }

    @Override
    @Transactional
    public void cancel(SessionId sessionId) {
        Instant now = clock.now();
        Session s =
                sessions.findById(sessionId)
                        .orElseThrow(
                                () -> new IllegalStateException("unknown session: " + sessionId));
        Transition t = sm.next(s.state(), SessionStateMachine.Trigger.CANCEL);
        Session moved = s.withFailure(SessionState.CANCELED, "CANCELED_BY_REQUEST", now);
        sessions.save(moved);
        SessionEvent ev =
                SessionEvent.transition(
                        new EventId(UUID.randomUUID()),
                        sessionId,
                        t.from(),
                        t.to(),
                        Map.of("trigger", "CANCEL"),
                        now);
        sessions.appendEvent(ev);
        outbox.append(
                sessionId,
                OutboxPort.Destination.SNS_SESSION_EVENTS,
                "SessionStateChanged",
                CreateSessionService.sessionEventPayload(ev, moved.userId()),
                now);
    }
}
