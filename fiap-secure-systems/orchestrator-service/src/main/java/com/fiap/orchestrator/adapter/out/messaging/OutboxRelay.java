package com.fiap.orchestrator.adapter.out.messaging;

import com.fiap.orchestrator.application.service.Clock;
import com.fiap.orchestrator.application.service.CreateSessionService;
import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.out.OutboxPort;
import com.fiap.orchestrator.domain.port.out.SessionRepositoryPort;
import com.fiap.orchestrator.domain.statemachine.SessionStateMachine;
import com.fiap.orchestrator.domain.statemachine.Transition;
import com.fiap.orchestrator.infrastructure.config.OutboxRelayProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@Component
public class OutboxRelay {

    private static final Logger log = LoggerFactory.getLogger(OutboxRelay.class);

    private final OutboxPort outbox;
    private final SqsAnalysisJobPublisher jobsPublisher;
    private final SnsSessionEventPublisher eventsPublisher;
    private final SessionRepositoryPort sessions;
    private final Clock clock;
    private final OutboxRelayProperties props;
    private final SessionStateMachine sm = new SessionStateMachine();

    public OutboxRelay(
            OutboxPort outbox,
            SqsAnalysisJobPublisher jobsPublisher,
            SnsSessionEventPublisher eventsPublisher,
            SessionRepositoryPort sessions,
            Clock clock,
            OutboxRelayProperties props) {
        this.outbox = outbox;
        this.jobsPublisher = jobsPublisher;
        this.eventsPublisher = eventsPublisher;
        this.sessions = sessions;
        this.clock = clock;
        this.props = props;
    }

    @Scheduled(fixedDelayString = "${orchestrator.outbox.relay-interval-ms:500}")
    public void drainOnce() {
        var batch = outbox.fetchUnpublished(props.batchSize());
        for (var entry : batch) {
            try {
                publish(entry);
                outbox.markPublished(entry.id(), clock.now());
                if (entry.destination() == OutboxPort.Destination.SQS_ANALYSIS_JOBS
                        && "AnalysisJobRequested".equals(entry.eventType())) {
                    advanceAfterJobPublished(entry.aggregateId());
                }
            } catch (Exception e) {
                String msg = e.getClass().getSimpleName() + ": " + e.getMessage();
                outbox.recordFailure(entry.id(), msg);
                int attempts = entry.attempts() + 1;
                if (attempts >= props.maxPublishAttemptsBeforeAlert()) {
                    log.warn("outbox row {} has failed {}× last={}", entry.id(), attempts, msg);
                } else {
                    log.info("outbox publish failed (attempt {}/{}): {}",
                            attempts, props.maxPublishAttemptsBeforeAlert(), msg);
                }
            }
        }
    }

    private void publish(OutboxPort.OutboxEntry entry) {
        switch (entry.destination()) {
            case SQS_ANALYSIS_JOBS ->
                    jobsPublisher.publishPreSerialized(entry.payload(), entry.aggregateId().toString());
            case SNS_SESSION_EVENTS ->
                    eventsPublisher.publishPreSerialized(entry.payload());
        }
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void advanceAfterJobPublished(SessionId sessionId) {
        Session s = sessions.findById(sessionId)
                .orElseThrow(() -> new IllegalStateException("unknown session: " + sessionId));
        if (s.state() != SessionState.ASSETS_UPLOADED) {
            return;
        }
        Instant now = clock.now();
        Transition t = sm.next(s.state(), SessionStateMachine.Trigger.OUTBOX_JOB_PUBLISHED);
        Session moved = s.withState(t.to(), now);
        sessions.save(moved);
        SessionEvent ev = SessionEvent.transition(
                new EventId(UUID.randomUUID()), sessionId, t.from(), t.to(),
                Map.of("trigger", "OUTBOX_JOB_PUBLISHED"), now);
        sessions.appendEvent(ev);
        outbox.append(sessionId, OutboxPort.Destination.SNS_SESSION_EVENTS, "SessionStateChanged",
                CreateSessionService.sessionEventPayload(ev, moved.userId()), now);
    }
}
