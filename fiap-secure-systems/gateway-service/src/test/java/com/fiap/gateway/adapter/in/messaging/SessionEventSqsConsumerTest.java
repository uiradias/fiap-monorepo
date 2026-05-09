package com.fiap.gateway.adapter.in.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.application.service.Clock;
import com.fiap.gateway.domain.model.SessionState;
import com.fiap.gateway.domain.port.in.RecordSessionEventUseCase;
import com.fiap.gateway.infrastructure.schema.ContractValidator;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.DeleteMessageRequest;
import software.amazon.awssdk.services.sqs.model.Message;

import java.io.File;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

class SessionEventSqsConsumerTest {

    private static final String QUEUE = "http://localhost:4566/000000000000/session-events-gateway";
    private static final Clock CLOCK = () -> Instant.parse("2026-05-09T12:00:00Z");

    private SqsClient sqs;
    private RecordSessionEventUseCase recorder;
    private SessionEventSqsConsumer consumer;
    private ObjectMapper mapper;

    @BeforeEach
    void up() {
        sqs = mock(SqsClient.class);
        recorder = mock(RecordSessionEventUseCase.class);
        mapper = new ObjectMapper().findAndRegisterModules();
        ContractValidator validator = new ContractValidator(
                new File(System.getProperty("user.dir") + "/../infrastructure/contracts").getAbsoluteFile());
        consumer = new SessionEventSqsConsumer(sqs, QUEUE, 1, mapper, validator, recorder, CLOCK);
    }

    @Test
    void valid_event_records_and_deletes() throws Exception {
        UUID eid = UUID.randomUUID();
        UUID sid = UUID.randomUUID();
        UUID uid = UUID.randomUUID();
        String body = mapper.writeValueAsString(Map.of(
                "schemaVersion", 1,
                "eventId", eid.toString(),
                "sessionId", sid.toString(),
                "userId", uid.toString(),
                "fromState", "ASSETS_UPLOADED",
                "toState", "QUEUED_FOR_ANALYSIS",
                "payload", Map.of(),
                "occurredAt", Instant.now().toString()));

        Message m = Message.builder().body(body).receiptHandle("rh-1").messageId("mid-1").build();
        when(recorder.record(any(), any(), any(), any(), eq(SessionState.QUEUED_FOR_ANALYSIS),
                any(), any(), any())).thenReturn(true);

        consumer.handleOne(m);

        verify(recorder, times(1)).record(any(), any(), any(),
                eq(SessionState.ASSETS_UPLOADED), eq(SessionState.QUEUED_FOR_ANALYSIS),
                any(), any(), any());
        verify(sqs, times(1)).deleteMessage(any(DeleteMessageRequest.class));
    }

    @Test
    void unparseable_body_is_dropped() {
        Message m = Message.builder().body("not-json").receiptHandle("rh-2").messageId("mid-2").build();
        consumer.handleOne(m);
        verify(sqs, times(1)).deleteMessage(any(DeleteMessageRequest.class));
        verifyNoInteractions(recorder);
    }

    @Test
    void recorder_failure_leaves_message_for_redelivery() {
        UUID eid = UUID.randomUUID();
        UUID sid = UUID.randomUUID();
        UUID uid = UUID.randomUUID();
        String body;
        try {
            body = mapper.writeValueAsString(Map.of(
                    "schemaVersion", 1,
                    "eventId", eid.toString(),
                    "sessionId", sid.toString(),
                    "userId", uid.toString(),
                    "toState", "ASSETS_UPLOADED",
                    "payload", Map.of(),
                    "occurredAt", Instant.now().toString()));
        } catch (Exception e) { throw new RuntimeException(e); }

        Message m = Message.builder().body(body).receiptHandle("rh-3").messageId("mid-3").build();
        when(recorder.record(any(), any(), any(), any(), any(), any(), any(), any()))
                .thenThrow(new RuntimeException("db hiccup"));

        consumer.handleOne(m);

        verify(sqs, never()).deleteMessage(any(DeleteMessageRequest.class));
    }
}
