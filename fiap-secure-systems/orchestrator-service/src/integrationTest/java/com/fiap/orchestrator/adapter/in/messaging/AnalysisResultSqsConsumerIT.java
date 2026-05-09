package com.fiap.orchestrator.adapter.in.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.orchestrator.LocalStackTestcontainersBase;
import com.fiap.orchestrator.adapter.out.persistence.SessionRepositoryAdapter;
import com.fiap.orchestrator.application.service.Clock;
import com.fiap.orchestrator.domain.model.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.SendMessageRequest;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static java.time.Duration.ofSeconds;
import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;

class AnalysisResultSqsConsumerIT extends LocalStackTestcontainersBase {

    @Autowired AnalysisResultSqsConsumer consumer;
    @Autowired SessionRepositoryAdapter sessions;
    @Autowired SqsClient sqs;
    @Autowired Clock clock;
    @Autowired ObjectMapper mapper;
    @Autowired
    @Qualifier("analysisResultsQueueUrl")
    String resultsQueueUrl;

    @Test
    void started_then_succeeded_walks_session_to_REPORT_READY() throws Exception {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        Session s = sessions.insertIfAbsent(Session.newSession(sid, uid, 1, clock.now()));
        s = sessions.save(s.withState(SessionState.QUEUED_FOR_ANALYSIS, clock.now()));

        UUID jobId = UUID.randomUUID();
        send(Map.of(
                "schemaVersion", 1,
                "jobId", jobId.toString(),
                "sessionId", sid.toString(),
                "status", "STARTED",
                "completedAt", Instant.now().toString()
        ));

        await().atMost(ofSeconds(15)).untilAsserted(() ->
                assertThat(sessions.findById(sid).orElseThrow().state())
                        .isEqualTo(SessionState.ANALYZING));

        Map<String, Object> payload = Map.of(
                "summary", "happy",
                "components", List.of(),
                "risks", List.of(),
                "improvements", List.of(),
                "strengths", List.of(),
                "confidence", "high",
                "model_metadata", Map.of("model", "claude-sonnet-4-6")
        );
        send(Map.of(
                "schemaVersion", 1,
                "jobId", jobId.toString(),
                "sessionId", sid.toString(),
                "status", "SUCCEEDED",
                "result", payload,
                "modelMetadata", Map.of("model", "claude-sonnet-4-6"),
                "completedAt", Instant.now().toString()
        ));

        await().atMost(ofSeconds(15)).untilAsserted(() ->
                assertThat(sessions.findById(sid).orElseThrow().state())
                        .isEqualTo(SessionState.REPORT_READY));
    }

    private void send(Map<String, Object> body) throws Exception {
        sqs.sendMessage(SendMessageRequest.builder()
                .queueUrl(resultsQueueUrl)
                .messageBody(mapper.writeValueAsString(body))
                .build());
    }
}
