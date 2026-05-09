package com.fiap.orchestrator.adapter.out.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.orchestrator.domain.model.SessionEvent;
import com.fiap.orchestrator.domain.model.UserId;
import com.fiap.orchestrator.domain.port.out.SessionEventPublisherPort;
import com.fiap.orchestrator.infrastructure.schema.ContractValidator;
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sns.model.MessageAttributeValue;
import software.amazon.awssdk.services.sns.model.PublishRequest;

import java.util.LinkedHashMap;
import java.util.Map;

public class SnsSessionEventPublisher implements SessionEventPublisherPort {

    private final SnsClient sns;
    private final String topicArn;
    private final ContractValidator validator;
    private final ObjectMapper mapper;

    public SnsSessionEventPublisher(
            SnsClient sns, String topicArn, ContractValidator validator, ObjectMapper mapper) {
        this.sns = sns;
        this.topicArn = topicArn;
        this.validator = validator;
        this.mapper = mapper;
    }

    @Override
    public void publish(SessionEvent event, UserId userId) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("schemaVersion", 1);
        body.put("eventId", event.id().toString());
        body.put("sessionId", event.sessionId().toString());
        body.put("userId", userId.toString());
        body.put("fromState", event.fromState() == null ? null : event.fromState().name());
        body.put("toState", event.toState().name());
        body.put("payload", event.payload());
        body.put("occurredAt", event.occurredAt().toString());
        publishPreSerialized(body);
    }

    public void publishPreSerialized(Map<String, Object> body) {
        validator.validateSessionEvent(body);
        try {
            String json = mapper.writeValueAsString(body);
            Map<String, MessageAttributeValue> attrs = Map.of(
                    "sessionId", attr(String.valueOf(body.get("sessionId"))),
                    "userId",    attr(String.valueOf(body.get("userId"))),
                    "toState",   attr(String.valueOf(body.get("toState"))));
            sns.publish(PublishRequest.builder()
                    .topicArn(topicArn)
                    .message(json)
                    .messageAttributes(attrs)
                    .build());
        } catch (Exception e) {
            throw new RuntimeException("failed to publish session-event", e);
        }
    }

    private static MessageAttributeValue attr(String s) {
        return MessageAttributeValue.builder().dataType("String").stringValue(s).build();
    }
}
