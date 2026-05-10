package com.fiap.orchestrator.application.service;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.orchestrator.domain.exception.UnknownSessionException;
import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisFailedUseCase;
import com.fiap.orchestrator.domain.port.out.OutboxPort;
import com.fiap.orchestrator.domain.port.out.ProcessedResultsPort;
import com.fiap.orchestrator.domain.port.out.SessionRepositoryPort;

@Service
public class HandleAnalysisFailedService implements HandleAnalysisFailedUseCase {

    private final SessionRepositoryPort sessions;
    private final OutboxPort outbox;
    private final ProcessedResultsPort dedup;
    private final Clock clock;

    public HandleAnalysisFailedService(
            SessionRepositoryPort sessions,
            OutboxPort outbox,
            ProcessedResultsPort dedup,
            Clock clock) {
        this.sessions = sessions;
        this.outbox = outbox;
        this.dedup = dedup;
        this.clock = clock;
    }

    @Override
    @Transactional
    public void onFailed(AnalysisOutcome outcome) {
        Instant now = clock.now();
        if (!dedup.recordIfAbsent(outcome.jobId(), AnalysisStatus.FAILED, now)) return;

        Session s =
                sessions.findById(outcome.sessionId())
                        .orElseThrow(() -> new UnknownSessionException(outcome.sessionId()));
        if (s.state().isTerminal()) return;

        AnalysisFailure failure = outcome.failureOpt().orElseThrow();
        Session moved = s.withFailure(SessionState.FAILED, failure.code(), now);
        sessions.save(moved);
        SessionEvent ev =
                SessionEvent.transition(
                        new EventId(UUID.randomUUID()),
                        outcome.sessionId(),
                        s.state(),
                        SessionState.FAILED,
                        Map.of(
                                "trigger",
                                "RECEIVE_RESULT_FAILED",
                                "errorCode",
                                failure.code(),
                                "errorMessage",
                                failure.message()),
                        now);
        sessions.appendEvent(ev);
        outbox.append(
                outcome.sessionId(),
                OutboxPort.Destination.SNS_SESSION_EVENTS,
                "SessionStateChanged",
                CreateSessionService.sessionEventPayload(ev, moved.userId()),
                now);
    }
}
