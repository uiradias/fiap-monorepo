package com.fiap.orchestrator.application.service;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.orchestrator.domain.exception.UnknownSessionException;
import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisCompletedUseCase;
import com.fiap.orchestrator.domain.port.out.OutboxPort;
import com.fiap.orchestrator.domain.port.out.ProcessedResultsPort;
import com.fiap.orchestrator.domain.port.out.ReportRepositoryPort;
import com.fiap.orchestrator.domain.port.out.SessionRepositoryPort;
import com.fiap.orchestrator.domain.statemachine.SessionStateMachine;
import com.fiap.orchestrator.domain.statemachine.Transition;
import com.fiap.orchestrator.infrastructure.observability.SessionMetrics;

import java.time.Duration;

@Service
public class HandleAnalysisCompletedService implements HandleAnalysisCompletedUseCase {

    private final SessionRepositoryPort sessions;
    private final ReportRepositoryPort reports;
    private final OutboxPort outbox;
    private final ProcessedResultsPort dedup;
    private final Clock clock;
    private final SessionMetrics metrics;
    private final SessionStateMachine sm = new SessionStateMachine();

    public HandleAnalysisCompletedService(
            SessionRepositoryPort sessions,
            ReportRepositoryPort reports,
            OutboxPort outbox,
            ProcessedResultsPort dedup,
            Clock clock,
            SessionMetrics metrics) {
        this.sessions = sessions;
        this.reports = reports;
        this.outbox = outbox;
        this.dedup = dedup;
        this.clock = clock;
        this.metrics = metrics;
    }

    @Override
    @Transactional
    public void onSucceeded(AnalysisOutcome outcome) {
        Instant now = clock.now();
        if (!dedup.recordIfAbsent(outcome.jobId(), AnalysisStatus.SUCCEEDED, now)) return;

        Session s =
                sessions.findById(outcome.sessionId())
                        .orElseThrow(() -> new UnknownSessionException(outcome.sessionId()));

        // Step A: ANALYZING → ANALYSIS_COMPLETED
        Transition tA = sm.next(s.state(), SessionStateMachine.Trigger.RECEIVE_RESULT_SUCCEEDED);
        Session sA = s.withState(tA.to(), now);
        sessions.save(sA);
        metrics.recordTransition(sA.state(), null);
        SessionEvent evA =
                SessionEvent.transition(
                        new EventId(UUID.randomUUID()),
                        outcome.sessionId(),
                        tA.from(),
                        tA.to(),
                        Map.of(
                                "trigger",
                                "RECEIVE_RESULT_SUCCEEDED",
                                "jobId",
                                outcome.jobId().toString()),
                        now);
        sessions.appendEvent(evA);
        outbox.append(
                outcome.sessionId(),
                OutboxPort.Destination.SNS_SESSION_EVENTS,
                "SessionStateChanged",
                CreateSessionService.sessionEventPayload(evA, sA.userId()),
                now);

        Map<String, Object> result = outcome.resultOpt().orElseThrow();
        Map<String, Object> md = outcome.modelMetadataOpt().orElseThrow();
        AnalysisReport report =
                new AnalysisReport(
                        new ReportId(UUID.randomUUID()),
                        outcome.sessionId(),
                        (String) result.get("summary"),
                        (String) result.get("confidence"),
                        result,
                        md,
                        now);
        reports.save(report);

        // Step B: ANALYSIS_COMPLETED → REPORT_READY
        Transition tB = sm.next(sA.state(), SessionStateMachine.Trigger.REPORT_PERSISTED);
        Session sB = sA.withState(tB.to(), now);
        sessions.save(sB);
        metrics.recordTransition(sB.state(), null);
        metrics.recordSessionDuration(Duration.between(s.createdAt(), now));
        SessionEvent evB =
                SessionEvent.transition(
                        new EventId(UUID.randomUUID()),
                        outcome.sessionId(),
                        tB.from(),
                        tB.to(),
                        Map.of("trigger", "REPORT_PERSISTED", "reportId", report.id().toString()),
                        now);
        sessions.appendEvent(evB);
        outbox.append(
                outcome.sessionId(),
                OutboxPort.Destination.SNS_SESSION_EVENTS,
                "SessionStateChanged",
                CreateSessionService.sessionEventPayload(evB, sB.userId()),
                now);
    }
}
