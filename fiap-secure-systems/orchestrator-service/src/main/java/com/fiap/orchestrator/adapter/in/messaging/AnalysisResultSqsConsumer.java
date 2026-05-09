package com.fiap.orchestrator.adapter.in.messaging;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.orchestrator.application.service.Clock;
import com.fiap.orchestrator.domain.exception.UnknownSessionException;
import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisCompletedUseCase;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisFailedUseCase;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisStartedUseCase;
import com.fiap.orchestrator.infrastructure.schema.ContractValidator;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.DeleteMessageRequest;
import software.amazon.awssdk.services.sqs.model.Message;
import software.amazon.awssdk.services.sqs.model.ReceiveMessageRequest;
import software.amazon.awssdk.services.sqs.model.SendMessageRequest;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;

public class AnalysisResultSqsConsumer {

    private static final Logger log = LoggerFactory.getLogger(AnalysisResultSqsConsumer.class);
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {};

    private final SqsClient sqs;
    private final String queueUrl;
    private final String dlqUrl;
    private final int waitSeconds;
    private final ObjectMapper mapper;
    private final ContractValidator validator;
    private final HandleAnalysisStartedUseCase started;
    private final HandleAnalysisCompletedUseCase completed;
    private final HandleAnalysisFailedUseCase failed;
    private final Clock clock;

    private final AtomicBoolean running = new AtomicBoolean(false);
    private Thread worker;

    public AnalysisResultSqsConsumer(
            SqsClient sqs, String queueUrl, String dlqUrl, int waitSeconds,
            ObjectMapper mapper, ContractValidator validator,
            HandleAnalysisStartedUseCase started,
            HandleAnalysisCompletedUseCase completed,
            HandleAnalysisFailedUseCase failed,
            Clock clock) {
        this.sqs = sqs;
        this.queueUrl = queueUrl;
        this.dlqUrl = dlqUrl;
        this.waitSeconds = waitSeconds;
        this.mapper = mapper;
        this.validator = validator;
        this.started = started;
        this.completed = completed;
        this.failed = failed;
        this.clock = clock;
    }

    @PostConstruct
    public synchronized void start() {
        if (running.compareAndSet(false, true)) {
            worker = new Thread(this::loop, "analysis-results-consumer");
            worker.setDaemon(true);
            worker.start();
            log.info("analysis-results consumer started (queue={})", queueUrl);
        }
    }

    @PreDestroy
    public synchronized void stop() {
        running.set(false);
        if (worker != null) {
            worker.interrupt();
            worker = null;
        }
    }

    private void loop() {
        while (running.get()) {
            try {
                var resp = sqs.receiveMessage(ReceiveMessageRequest.builder()
                        .queueUrl(queueUrl)
                        .waitTimeSeconds(waitSeconds)
                        .maxNumberOfMessages(10)
                        .build());
                for (Message m : resp.messages()) {
                    handleOne(m);
                }
            } catch (Exception e) {
                if (!running.get()) return;
                log.warn("analysis-results loop iteration failed", e);
                try { Thread.sleep(1_000); } catch (InterruptedException ignored) { return; }
            }
        }
    }

    void handleOne(Message m) {
        Map<String, Object> body;
        try {
            body = mapper.readValue(m.body(), MAP_TYPE);
            validator.validateAnalysisResult(body);
        } catch (Exception parseError) {
            log.warn("dropping unparseable/invalid analysis-results message: {}", parseError.getMessage());
            deleteSafely(m);
            return;
        }
        try {
            dispatch(body);
            deleteSafely(m);
        } catch (UnknownSessionException poisonPill) {
            // Permanent error: session referenced by the message does not exist (and won't, ever).
            // Re-queueing wastes 300 s of visibility timeout per attempt; forward to DLQ explicitly
            // so ops keeps an audit trail and the message is gone from the main queue immediately.
            log.warn("poison pill on analysis-results jobId={} status={}: {}",
                    body.get("jobId"), body.get("status"), poisonPill.getMessage());
            forwardToDlq(m);
            deleteSafely(m);
        } catch (Exception useCaseError) {
            log.error("use case failed for analysis-results jobId={} status={}; leaving for redelivery",
                    body.get("jobId"), body.get("status"), useCaseError);
        }
    }

    private void forwardToDlq(Message m) {
        try {
            sqs.sendMessage(SendMessageRequest.builder()
                    .queueUrl(dlqUrl)
                    .messageBody(m.body())
                    .build());
        } catch (Exception e) {
            log.warn("failed to forward poison-pill message {} to DLQ {}: {}",
                    m.messageId(), dlqUrl, e.getMessage());
        }
    }

    private void dispatch(Map<String, Object> body) {
        JobId jobId = new JobId(UUID.fromString(String.valueOf(body.get("jobId"))));
        SessionId sessionId = new SessionId(UUID.fromString(String.valueOf(body.get("sessionId"))));
        String status = String.valueOf(body.get("status"));
        Instant completedAt = Instant.parse(String.valueOf(body.get("completedAt")));

        switch (status) {
            case "STARTED" -> started.onStarted(jobId, sessionId);
            case "SUCCEEDED" -> {
                @SuppressWarnings("unchecked")
                Map<String, Object> result = (Map<String, Object>) body.get("result");
                @SuppressWarnings("unchecked")
                Map<String, Object> md = (Map<String, Object>) body.get("modelMetadata");
                completed.onSucceeded(new AnalysisOutcome(
                        jobId, sessionId, AnalysisStatus.SUCCEEDED,
                        result, md, null, completedAt));
            }
            case "FAILED" -> {
                @SuppressWarnings("unchecked")
                Map<String, Object> err = (Map<String, Object>) body.get("error");
                AnalysisFailure failure = new AnalysisFailure(
                        String.valueOf(err.get("code")),
                        String.valueOf(err.get("message")));
                failed.onFailed(new AnalysisOutcome(
                        jobId, sessionId, AnalysisStatus.FAILED,
                        null, null, failure, completedAt));
            }
            default -> throw new IllegalStateException("unknown status: " + status);
        }
    }

    private void deleteSafely(Message m) {
        try {
            sqs.deleteMessage(DeleteMessageRequest.builder()
                    .queueUrl(queueUrl)
                    .receiptHandle(m.receiptHandle())
                    .build());
        } catch (Exception e) {
            log.warn("failed to delete analysis-results message {}: {}", m.messageId(), e.getMessage());
        }
    }
}
