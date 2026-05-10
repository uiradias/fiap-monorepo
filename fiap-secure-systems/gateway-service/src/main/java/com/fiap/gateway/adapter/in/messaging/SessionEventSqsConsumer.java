package com.fiap.gateway.adapter.in.messaging;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.application.service.Clock;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.RecordSessionEventUseCase;
import com.fiap.gateway.infrastructure.schema.ContractValidator;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.DeleteMessageRequest;
import software.amazon.awssdk.services.sqs.model.Message;
import software.amazon.awssdk.services.sqs.model.ReceiveMessageRequest;

public class SessionEventSqsConsumer {

    private static final Logger log = LoggerFactory.getLogger(SessionEventSqsConsumer.class);
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {};

    private final SqsClient sqs;
    private final String queueUrl;
    private final int waitSeconds;
    private final ObjectMapper mapper;
    private final ContractValidator validator;
    private final RecordSessionEventUseCase recorder;
    private final Clock clock;

    private final AtomicBoolean running = new AtomicBoolean(false);
    private Thread worker;

    public SessionEventSqsConsumer(
            SqsClient sqs,
            String queueUrl,
            int waitSeconds,
            ObjectMapper mapper,
            ContractValidator validator,
            RecordSessionEventUseCase recorder,
            Clock clock) {
        this.sqs = sqs;
        this.queueUrl = queueUrl;
        this.waitSeconds = waitSeconds;
        this.mapper = mapper;
        this.validator = validator;
        this.recorder = recorder;
        this.clock = clock;
    }

    @PostConstruct
    public synchronized void start() {
        if (running.compareAndSet(false, true)) {
            worker = new Thread(this::loop, "session-events-consumer");
            worker.setDaemon(true);
            worker.start();
            log.info("session-events consumer started (queue={})", queueUrl);
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
                var resp =
                        sqs.receiveMessage(
                                ReceiveMessageRequest.builder()
                                        .queueUrl(queueUrl)
                                        .waitTimeSeconds(waitSeconds)
                                        .maxNumberOfMessages(10)
                                        .build());
                for (Message m : resp.messages()) {
                    handleOne(m);
                }
            } catch (Exception e) {
                if (!running.get()) return;
                log.warn("session-events loop iteration failed", e);
                try {
                    Thread.sleep(1_000);
                } catch (InterruptedException ignored) {
                    return;
                }
            }
        }
    }

    void handleOne(Message m) {
        Map<String, Object> body;
        try {
            body = mapper.readValue(m.body(), MAP_TYPE);
            validator.validateSessionEvent(body);
        } catch (Exception parseError) {
            log.warn(
                    "dropping unparseable/invalid session-event message: {}",
                    parseError.getMessage());
            deleteSafely(m);
            return;
        }
        try {
            EventId eid = new EventId(UUID.fromString((String) body.get("eventId")));
            SessionId sid = new SessionId(UUID.fromString((String) body.get("sessionId")));
            UserId uid = new UserId(UUID.fromString((String) body.get("userId")));
            SessionState toState = SessionState.valueOf((String) body.get("toState"));
            String fromStr = (String) body.get("fromState");
            SessionState fromState = (fromStr == null) ? null : SessionState.valueOf(fromStr);
            @SuppressWarnings("unchecked")
            Map<String, Object> payload =
                    (Map<String, Object>) body.getOrDefault("payload", Map.of());
            Instant occurredAt = Instant.parse((String) body.get("occurredAt"));

            recorder.record(eid, sid, uid, fromState, toState, payload, occurredAt, clock.now());
            deleteSafely(m);
        } catch (Exception useCaseError) {
            log.error(
                    "recordSessionEvent failed for eventId={} sessionId={}; leaving for redelivery",
                    body.get("eventId"),
                    body.get("sessionId"),
                    useCaseError);
        }
    }

    private void deleteSafely(Message m) {
        try {
            sqs.deleteMessage(
                    DeleteMessageRequest.builder()
                            .queueUrl(queueUrl)
                            .receiptHandle(m.receiptHandle())
                            .build());
        } catch (Exception e) {
            log.warn(
                    "failed to delete session-events message {}: {}",
                    m.messageId(),
                    e.getMessage());
        }
    }
}
