package com.fiap.gateway;

import java.net.URI;
import java.util.Map;

import org.testcontainers.containers.localstack.LocalStackContainer;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.CreateBucketRequest;
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sns.model.CreateTopicRequest;
import software.amazon.awssdk.services.sns.model.SubscribeRequest;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.CreateQueueRequest;
import software.amazon.awssdk.services.sqs.model.GetQueueAttributesRequest;
import software.amazon.awssdk.services.sqs.model.QueueAttributeName;

public final class Provisioning {

    static volatile boolean done = false;
    public static String bucket;
    public static String sessionEventsUrl;
    public static String sessionEventsTopicArn;

    static synchronized void ensure(LocalStackContainer ls) {
        if (done) return;
        URI endpoint = ls.getEndpoint();
        var creds =
                StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(ls.getAccessKey(), ls.getSecretKey()));
        Region region = Region.of(ls.getRegion());

        try (S3Client s3 =
                        S3Client.builder()
                                .endpointOverride(endpoint)
                                .region(region)
                                .credentialsProvider(creds)
                                .build();
                SqsClient sqs =
                        SqsClient.builder()
                                .endpointOverride(endpoint)
                                .region(region)
                                .credentialsProvider(creds)
                                .build();
                SnsClient sns =
                        SnsClient.builder()
                                .endpointOverride(endpoint)
                                .region(region)
                                .credentialsProvider(creds)
                                .build()) {

            bucket = "fiap-test-" + System.nanoTime();
            s3.createBucket(CreateBucketRequest.builder().bucket(bucket).build());

            sessionEventsTopicArn =
                    sns.createTopic(CreateTopicRequest.builder().name("session-events").build())
                            .topicArn();
            sessionEventsUrl =
                    sqs.createQueue(
                                    CreateQueueRequest.builder()
                                            .queueName("session-events-gateway")
                                            .build())
                            .queueUrl();

            String queueArn =
                    sqs.getQueueAttributes(
                                    GetQueueAttributesRequest.builder()
                                            .queueUrl(sessionEventsUrl)
                                            .attributeNames(QueueAttributeName.QUEUE_ARN)
                                            .build())
                            .attributes()
                            .get(QueueAttributeName.QUEUE_ARN);
            sns.subscribe(
                    SubscribeRequest.builder()
                            .topicArn(sessionEventsTopicArn)
                            .protocol("sqs")
                            .endpoint(queueArn)
                            .attributes(Map.of("RawMessageDelivery", "true"))
                            .build());
        }
        done = true;
    }
}
