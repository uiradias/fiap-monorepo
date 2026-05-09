package com.fiap.orchestrator.adapter.out.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.orchestrator.LocalStackTestcontainersBase;
import com.fiap.orchestrator.infrastructure.schema.ContractValidator;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.CreateQueueRequest;
import software.amazon.awssdk.services.sqs.model.ReceiveMessageRequest;

import java.io.File;
import java.net.URI;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class SqsAnalysisJobPublisherIT extends LocalStackTestcontainersBase {

    private static SqsClient sqs;
    private static String queueUrl;

    @BeforeAll
    static void createQueue() {
        sqs = SqsClient.builder()
                .endpointOverride(URI.create(LOCALSTACK.getEndpoint().toString()))
                .region(Region.of(LOCALSTACK.getRegion()))
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(LOCALSTACK.getAccessKey(), LOCALSTACK.getSecretKey())))
                .build();
        queueUrl = sqs.createQueue(CreateQueueRequest.builder()
                .queueName("analysis-jobs-it").build()).queueUrl();
    }

    @Test
    void publishes_a_well_formed_job() throws Exception {
        ContractValidator validator = new ContractValidator(
                new File("../infrastructure/contracts").getAbsoluteFile());
        SqsAnalysisJobPublisher publisher = new SqsAnalysisJobPublisher(
                sqs, queueUrl, validator, new ObjectMapper());

        UUID jobId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        Map<String, Object> payload = Map.of(
                "schemaVersion", 1,
                "jobId", jobId.toString(),
                "sessionId", sessionId.toString(),
                "userId", "00000000-0000-4000-8000-000000000001",
                "assets", List.of(Map.of(
                        "assetId", "00000000-0000-4000-8000-000000000002",
                        "s3Key", "sessions/" + sessionId + "/file.png",
                        "contentType", "image/png",
                        "filename", "file.png",
                        "sizeBytes", 70)),
                "promptVersion", "v1",
                "submittedAt", Instant.now().toString());

        publisher.publishPreSerialized(payload, sessionId.toString());

        var resp = sqs.receiveMessage(ReceiveMessageRequest.builder()
                .queueUrl(queueUrl).waitTimeSeconds(2).build());
        assertThat(resp.messages()).hasSize(1);
        Map<?, ?> body = new ObjectMapper().readValue(resp.messages().get(0).body(), Map.class);
        assertThat(body.get("jobId")).isEqualTo(jobId.toString());
    }
}
