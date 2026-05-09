package com.fiap.gateway.adapter.in.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.LocalStackTestcontainersBase;
import com.fiap.gateway.Provisioning;
import com.fiap.gateway.adapter.out.persistence.SessionProjectionRepositoryAdapter;
import com.fiap.gateway.domain.model.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sns.model.PublishRequest;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import static java.time.Duration.ofSeconds;
import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;

class SessionEventSqsConsumerIT extends LocalStackTestcontainersBase {

    @Autowired SnsClient sns;
    @Autowired ObjectMapper mapper;
    @Autowired SessionProjectionRepositoryAdapter projections;

    @Test
    void session_event_propagates_to_projection() throws Exception {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());

        Map<String, Object> evt = Map.of(
                "schemaVersion", 1,
                "eventId", UUID.randomUUID().toString(),
                "sessionId", sid.toString(),
                "userId", uid.toString(),
                "toState", "REPORT_READY",
                "payload", Map.of("reportId", UUID.randomUUID().toString()),
                "occurredAt", Instant.now().toString());

        sns.publish(PublishRequest.builder()
                .topicArn(Provisioning.sessionEventsTopicArn)
                .message(mapper.writeValueAsString(evt))
                .build());

        await().atMost(ofSeconds(15)).untilAsserted(() ->
                assertThat(projections.findById(sid))
                        .hasValueSatisfying(p ->
                                assertThat(p.state()).isEqualTo(SessionState.REPORT_READY)));
    }
}
