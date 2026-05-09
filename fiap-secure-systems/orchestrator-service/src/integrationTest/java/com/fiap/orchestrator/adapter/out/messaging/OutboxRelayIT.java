package com.fiap.orchestrator.adapter.out.messaging;

import com.fiap.orchestrator.LocalStackTestcontainersBase;
import com.fiap.orchestrator.adapter.out.persistence.OutboxAdapter;
import com.fiap.orchestrator.adapter.out.persistence.SessionRepositoryAdapter;
import com.fiap.orchestrator.application.service.Clock;
import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.out.OutboxPort;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static java.time.Duration.ofSeconds;
import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;

class OutboxRelayIT extends LocalStackTestcontainersBase {

    @Autowired OutboxRelay relay;
    @Autowired OutboxAdapter outbox;
    @Autowired SessionRepositoryAdapter sessions;
    @Autowired Clock clock;

    @Test
    void drains_a_session_event_outbox_row_and_marks_published() {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        sessions.insertIfAbsent(Session.newSession(sid, uid, 1, clock.now()));

        Map<String, Object> body = Map.of(
                "schemaVersion", 1,
                "eventId", UUID.randomUUID().toString(),
                "sessionId", sid.toString(),
                "userId", uid.toString(),
                "fromState", null,
                "toState", "ASSETS_UPLOADED",
                "payload", Map.of(),
                "occurredAt", Instant.now().toString()
        );
        outbox.append(sid, OutboxPort.Destination.SNS_SESSION_EVENTS,
                "SessionStateChanged", body, clock.now());

        relay.drainOnce();

        await().atMost(ofSeconds(5)).untilAsserted(() -> {
            List<OutboxPort.OutboxEntry> remaining = outbox.fetchUnpublished(50);
            assertThat(remaining).noneMatch(e -> e.aggregateId().equals(sid));
        });
    }

    @Test
    void after_analysis_job_publish_advances_session_to_QUEUED_FOR_ANALYSIS() {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        sessions.insertIfAbsent(Session.newSession(sid, uid, 1, clock.now()));

        Map<String, Object> jobBody = Map.of(
                "schemaVersion", 1,
                "jobId", UUID.randomUUID().toString(),
                "sessionId", sid.toString(),
                "userId", uid.toString(),
                "assets", List.of(Map.of(
                        "assetId", UUID.randomUUID().toString(),
                        "s3Key", "sessions/" + sid + "/file.png",
                        "contentType", "image/png",
                        "filename", "file.png",
                        "sizeBytes", 70)),
                "promptVersion", "v1",
                "submittedAt", Instant.now().toString()
        );
        outbox.append(sid, OutboxPort.Destination.SQS_ANALYSIS_JOBS,
                "AnalysisJobRequested", jobBody, clock.now());

        relay.drainOnce();

        await().atMost(ofSeconds(5)).untilAsserted(() -> {
            Session s = sessions.findById(sid).orElseThrow();
            assertThat(s.state()).isEqualTo(SessionState.QUEUED_FOR_ANALYSIS);
        });

        relay.drainOnce();
        await().atMost(ofSeconds(5)).untilAsserted(() ->
                assertThat(outbox.fetchUnpublished(50))
                        .noneMatch(e -> e.aggregateId().equals(sid)));
    }
}
