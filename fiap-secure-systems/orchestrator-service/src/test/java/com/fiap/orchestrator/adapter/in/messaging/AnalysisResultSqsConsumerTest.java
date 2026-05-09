package com.fiap.orchestrator.adapter.in.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.orchestrator.application.service.Clock;
import com.fiap.orchestrator.domain.exception.UnknownSessionException;
import com.fiap.orchestrator.domain.model.JobId;
import com.fiap.orchestrator.domain.model.SessionId;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisCompletedUseCase;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisFailedUseCase;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisStartedUseCase;
import com.fiap.orchestrator.infrastructure.schema.ContractValidator;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.DeleteMessageRequest;
import software.amazon.awssdk.services.sqs.model.Message;
import software.amazon.awssdk.services.sqs.model.SendMessageRequest;

import java.io.File;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

class AnalysisResultSqsConsumerTest {

    private static final String MAIN_URL = "http://localhost:4566/000000000000/analysis-results";
    private static final String DLQ_URL = "http://localhost:4566/000000000000/analysis-results-dlq";

    private SqsClient sqs;
    private HandleAnalysisStartedUseCase started;
    private HandleAnalysisCompletedUseCase completed;
    private HandleAnalysisFailedUseCase failed;
    private AnalysisResultSqsConsumer consumer;
    private ObjectMapper mapper;

    @BeforeEach
    void setUp() {
        sqs = mock(SqsClient.class);
        started = mock(HandleAnalysisStartedUseCase.class);
        completed = mock(HandleAnalysisCompletedUseCase.class);
        failed = mock(HandleAnalysisFailedUseCase.class);
        mapper = new ObjectMapper().findAndRegisterModules();

        ContractValidator validator = new ContractValidator(
                new File(System.getProperty("user.dir") + "/../infrastructure/contracts").getAbsoluteFile());
        Clock clock = Instant::now;

        consumer = new AnalysisResultSqsConsumer(
                sqs, MAIN_URL, DLQ_URL, 1, mapper, validator,
                started, completed, failed, clock);
    }

    @Test
    void unknown_session_on_started_routes_message_to_dlq_and_deletes_from_main() throws Exception {
        UUID jobId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        String body = mapper.writeValueAsString(Map.of(
                "schemaVersion", 1,
                "jobId", jobId.toString(),
                "sessionId", sessionId.toString(),
                "status", "STARTED",
                "completedAt", Instant.now().toString()
        ));
        Message m = Message.builder().body(body).receiptHandle("rh-1").messageId("mid-1").build();

        doThrow(new UnknownSessionException(new SessionId(sessionId)))
                .when(started).onStarted(any(JobId.class), any(SessionId.class));

        consumer.handleOne(m);

        verify(sqs, times(1)).sendMessage(argThat((SendMessageRequest req) ->
                DLQ_URL.equals(req.queueUrl()) && body.equals(req.messageBody())));
        verify(sqs, times(1)).deleteMessage(argThat((DeleteMessageRequest req) ->
                MAIN_URL.equals(req.queueUrl()) && "rh-1".equals(req.receiptHandle())));
    }

    @Test
    void transient_failure_on_started_leaves_message_for_redelivery() throws Exception {
        UUID jobId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        String body = mapper.writeValueAsString(Map.of(
                "schemaVersion", 1,
                "jobId", jobId.toString(),
                "sessionId", sessionId.toString(),
                "status", "STARTED",
                "completedAt", Instant.now().toString()
        ));
        Message m = Message.builder().body(body).receiptHandle("rh-2").messageId("mid-2").build();

        doThrow(new RuntimeException("db hiccup"))
                .when(started).onStarted(any(JobId.class), any(SessionId.class));

        consumer.handleOne(m);

        // Transient failures: do NOT delete from main, do NOT push to DLQ — let visibility timeout requeue.
        verify(sqs, never()).deleteMessage(any(DeleteMessageRequest.class));
        verify(sqs, never()).sendMessage(any(SendMessageRequest.class));
    }

    @Test
    void unparseable_message_is_dropped_without_dlq_forwarding() {
        Message m = Message.builder().body("not-json").receiptHandle("rh-3").messageId("mid-3").build();

        consumer.handleOne(m);

        // Garbage in: drop quietly. SQS-redrive will catch repeats; we don't double-forward to DLQ.
        verify(sqs, times(1)).deleteMessage(argThat((DeleteMessageRequest req) ->
                "rh-3".equals(req.receiptHandle())));
        verify(sqs, never()).sendMessage(any(SendMessageRequest.class));
    }

    @Test
    void successful_dispatch_deletes_from_main_without_dlq_forwarding() throws Exception {
        UUID jobId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        String body = mapper.writeValueAsString(Map.of(
                "schemaVersion", 1,
                "jobId", jobId.toString(),
                "sessionId", sessionId.toString(),
                "status", "SUCCEEDED",
                "result", Map.of(
                        "summary", "ok",
                        "components", List.of(),
                        "risks", List.of(),
                        "improvements", List.of(),
                        "strengths", List.of(),
                        "confidence", "high",
                        "model_metadata", Map.of("model", "claude-sonnet-4-6")),
                "modelMetadata", Map.of("model", "claude-sonnet-4-6"),
                "completedAt", Instant.now().toString()
        ));
        Message m = Message.builder().body(body).receiptHandle("rh-4").messageId("mid-4").build();

        consumer.handleOne(m);

        verify(sqs, times(1)).deleteMessage(argThat((DeleteMessageRequest req) ->
                MAIN_URL.equals(req.queueUrl()) && "rh-4".equals(req.receiptHandle())));
        verify(sqs, never()).sendMessage(any(SendMessageRequest.class));
    }
}
