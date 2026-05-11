package com.fiap.orchestrator;

import java.net.URI;

import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.localstack.LocalStackContainer;
import org.testcontainers.utility.DockerImageName;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sns.model.CreateTopicRequest;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.CreateQueueRequest;

// Singleton container — see PostgresTestcontainersBase for rationale on @Testcontainers absence.
// Provisions the SQS queues and SNS topic the production beans wire against, then overrides the
// corresponding URLs/ARN so OutboxRelay and AnalysisResultSqsConsumer talk to LocalStack rather
// than the stub `http://test/...` URLs from application-test.yml.
public abstract class LocalStackTestcontainersBase extends PostgresTestcontainersBase {

    public static final LocalStackContainer LOCALSTACK;
    static final String analysisJobsUrl;
    static final String analysisResultsUrl;
    static final String sessionEventsTopicArn;

    static {
        LOCALSTACK =
                new LocalStackContainer(DockerImageName.parse("localstack/localstack:3.5"))
                        .withServices(
                                LocalStackContainer.Service.SQS, LocalStackContainer.Service.SNS);
        LOCALSTACK.start();
        AwsBasicCredentials creds =
                AwsBasicCredentials.create(LOCALSTACK.getAccessKey(), LOCALSTACK.getSecretKey());
        URI endpoint = URI.create(LOCALSTACK.getEndpoint().toString());
        Region region = Region.of(LOCALSTACK.getRegion());
        try (SqsClient sqs =
                        SqsClient.builder()
                                .endpointOverride(endpoint)
                                .region(region)
                                .credentialsProvider(StaticCredentialsProvider.create(creds))
                                .build();
                SnsClient sns =
                        SnsClient.builder()
                                .endpointOverride(endpoint)
                                .region(region)
                                .credentialsProvider(StaticCredentialsProvider.create(creds))
                                .build()) {
            analysisJobsUrl =
                    sqs.createQueue(CreateQueueRequest.builder().queueName("analysis-jobs").build())
                            .queueUrl();
            analysisResultsUrl =
                    sqs.createQueue(
                                    CreateQueueRequest.builder()
                                            .queueName("analysis-results")
                                            .build())
                            .queueUrl();
            sessionEventsTopicArn =
                    sns.createTopic(CreateTopicRequest.builder().name("session-events").build())
                            .topicArn();
        }
    }

    @DynamicPropertySource
    static void registerLocalStackProperties(DynamicPropertyRegistry registry) {
        registry.add("orchestrator.aws.endpoint-url", () -> LOCALSTACK.getEndpoint().toString());
        registry.add("orchestrator.aws.region", LOCALSTACK::getRegion);
        registry.add("orchestrator.aws.access-key", LOCALSTACK::getAccessKey);
        registry.add("orchestrator.aws.secret-key", LOCALSTACK::getSecretKey);
        registry.add("orchestrator.sqs.analysis-jobs-url", () -> analysisJobsUrl);
        registry.add("orchestrator.sqs.analysis-results-url", () -> analysisResultsUrl);
        registry.add("orchestrator.sns.session-events-topic-arn", () -> sessionEventsTopicArn);
    }
}
