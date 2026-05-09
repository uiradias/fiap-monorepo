package com.fiap.orchestrator.application.service;

import com.fiap.orchestrator.domain.exception.UnknownSessionException;
import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisStartedUseCase;
import com.fiap.orchestrator.domain.port.out.OutboxPort;
import com.fiap.orchestrator.domain.port.out.ProcessedResultsPort;
import com.fiap.orchestrator.domain.port.out.SessionRepositoryPort;
import com.fiap.orchestrator.domain.statemachine.SessionStateMachine;
import com.fiap.orchestrator.domain.statemachine.Transition;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Service
public class HandleAnalysisStartedService implements HandleAnalysisStartedUseCase {

    private final SessionRepositoryPort sessions;
    private final OutboxPort outbox;
    private final ProcessedResultsPort dedup;
    private final Clock clock;
    private final SessionStateMachine sm = new SessionStateMachine();

    public HandleAnalysisStartedService(
            SessionRepositoryPort sessions, OutboxPort outbox,
            ProcessedResultsPort dedup, Clock clock) {
        this.sessions = sessions;
        this.outbox = outbox;
        this.dedup = dedup;
        this.clock = clock;
    }

    @Override
    @Transactional
    public void onStarted(JobId jobId, SessionId sessionId) {
        Instant now = clock.now();
        if (!dedup.recordIfAbsent(jobId, AnalysisStatus.STARTED, now)) {
            return;
        }
        Session s = sessions.findById(sessionId)
                .orElseThrow(() -> new UnknownSessionException(sessionId));
        Transition t = sm.next(s.state(), SessionStateMachine.Trigger.RECEIVE_RESULT_STARTED);
        Session moved = s.withState(t.to(), now);
        sessions.save(moved);
        SessionEvent ev = SessionEvent.transition(
                new EventId(UUID.randomUUID()), sessionId, t.from(), t.to(),
                Map.of("trigger", "RECEIVE_RESULT_STARTED", "jobId", jobId.toString()), now);
        sessions.appendEvent(ev);
        outbox.append(sessionId, OutboxPort.Destination.SNS_SESSION_EVENTS, "SessionStateChanged",
                CreateSessionService.sessionEventPayload(ev, moved.userId()), now);
    }
}
