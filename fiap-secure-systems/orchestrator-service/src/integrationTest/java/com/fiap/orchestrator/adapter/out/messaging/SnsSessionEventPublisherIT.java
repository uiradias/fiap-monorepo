package com.fiap.orchestrator.adapter.out.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.orchestrator.LocalStackTestcontainersBase;
import com.fiap.orchestrator.infrastructure.schema.ContractValidator;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sns.model.CreateTopicRequest;
import software.amazon.awssdk.services.sns.model.SubscribeRequest;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.CreateQueueRequest;
import software.amazon.awssdk.services.sqs.model.GetQueueAttributesRequest;
import software.amazon.awssdk.services.sqs.model.QueueAttributeName;
import software.amazon.awssdk.services.sqs.model.ReceiveMessageRequest;

import java.io.File;
import java.net.URI;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class SnsSessionEventPublisherIT extends LocalStackTestcontainersBase {

    private static SnsClient sns;
    private static SqsClient sqs;
    private static String topicArn;
    private static String queueUrl;

    @BeforeAll
    static void wire() {
        sns = SnsClient.builder()
                .endpointOverride(URI.create(LOCALSTACK.getEndpoint().toString()))
                .region(Region.of(LOCALSTACK.getRegion()))
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(LOCALSTACK.getAccessKey(), LOCALSTACK.getSecretKey())))
                .build();
        sqs = SqsClient.builder()
                .endpointOverride(URI.create(LOCALSTACK.getEndpoint().toString()))
                .region(Region.of(LOCALSTACK.getRegion()))
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(LOCALSTACK.getAccessKey(), LOCALSTACK.getSecretKey())))
                .build();
        topicArn = sns.createTopic(CreateTopicRequest.builder()
                .name("session-events-it").build()).topicArn();
        queueUrl = sqs.createQueue(CreateQueueRequest.builder()
                .queueName("session-events-it-q").build()).queueUrl();
        String queueArn = sqs.getQueueAttributes(GetQueueAttributesRequest.builder()
                .queueUrl(queueUrl)
                .attributeNames(QueueAttributeName.QUEUE_ARN).build())
                .attributes().get(QueueAttributeName.QUEUE_ARN);
        sns.subscribe(SubscribeRequest.builder()
                .topicArn(topicArn)
                .protocol("sqs")
                .endpoint(queueArn)
                .attributes(Map.of("RawMessageDelivery", "true"))
                .returnSubscriptionArn(true)
                .build());
    }

    @Test
    void publishes_a_well_formed_session_event_with_attributes() throws Exception {
        ContractValidator validator = new ContractValidator(
                new File("../infrastructure/contracts").getAbsoluteFile());
        SnsSessionEventPublisher publisher = new SnsSessionEventPublisher(
                sns, topicArn, validator, new ObjectMapper());

        Map<String, Object> body = Map.of(
                "schemaVersion", 1,
                "eventId", UUID.randomUUID().toString(),
                "sessionId", UUID.randomUUID().toString(),
                "userId", UUID.randomUUID().toString(),
                "fromState", "ASSETS_UPLOADED",
                "toState", "QUEUED_FOR_ANALYSIS",
                "payload", Map.of(),
                "occurredAt", "2026-01-01T00:00:00Z"
        );

        publisher.publishPreSerialized(body);

        var resp = sqs.receiveMessage(ReceiveMessageRequest.builder()
                .queueUrl(queueUrl).waitTimeSeconds(3).build());
        assertThat(resp.messages()).hasSize(1);
        Map<?, ?> received = new ObjectMapper().readValue(resp.messages().get(0).body(), Map.class);
        assertThat(received.get("toState")).isEqualTo("QUEUED_FOR_ANALYSIS");
    }
}
