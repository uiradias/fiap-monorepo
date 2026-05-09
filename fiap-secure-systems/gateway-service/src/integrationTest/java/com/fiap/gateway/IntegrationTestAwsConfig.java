package com.fiap.gateway;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.adapter.in.messaging.SessionEventSqsConsumer;
import com.fiap.gateway.adapter.out.s3.S3AssetStorageAdapter;
import com.fiap.gateway.application.service.Clock;
import com.fiap.gateway.domain.port.in.RecordSessionEventUseCase;
import com.fiap.gateway.infrastructure.schema.ContractValidator;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sqs.SqsClient;

import java.io.File;
import java.net.URI;
import java.time.Instant;

@Configuration
public class IntegrationTestAwsConfig {

    @Bean
    public S3Client s3Client(
            @Value("${gateway.aws.endpoint-url}") String endpoint,
            @Value("${gateway.aws.region}") String region,
            @Value("${gateway.aws.access-key}") String accessKey,
            @Value("${gateway.aws.secret-key}") String secretKey) {
        return S3Client.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(region))
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(accessKey, secretKey)))
                .forcePathStyle(true)
                .httpClient(UrlConnectionHttpClient.create())
                .build();
    }

    @Bean
    public S3AssetStorageAdapter s3AssetStorageAdapter(S3Client s3,
            @Value("${gateway.s3.bucket}") String bucket) {
        return new S3AssetStorageAdapter(s3, bucket);
    }

    @Bean
    public SnsClient snsClient(
            @Value("${gateway.aws.endpoint-url}") String endpoint,
            @Value("${gateway.aws.region}") String region,
            @Value("${gateway.aws.access-key}") String accessKey,
            @Value("${gateway.aws.secret-key}") String secretKey) {
        return SnsClient.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(region))
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(accessKey, secretKey)))
                .httpClient(UrlConnectionHttpClient.create())
                .build();
    }

    @Bean
    public SqsClient sqsClient(
            @Value("${gateway.aws.endpoint-url}") String endpoint,
            @Value("${gateway.aws.region}") String region,
            @Value("${gateway.aws.access-key}") String accessKey,
            @Value("${gateway.aws.secret-key}") String secretKey) {
        return SqsClient.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(region))
                .credentialsProvider(StaticCredentialsProvider.create(
                        AwsBasicCredentials.create(accessKey, secretKey)))
                .httpClient(UrlConnectionHttpClient.create())
                .build();
    }

    @Bean(initMethod = "start", destroyMethod = "stop")
    public SessionEventSqsConsumer sessionEventSqsConsumer(
            SqsClient sqsClient,
            @Value("${gateway.sqs.session-events-url}") String queueUrl,
            @Value("${gateway.sqs.poll-wait-seconds:1}") int waitSeconds,
            ObjectMapper mapper,
            @Value("${gateway.contracts-dir}") String contractsDir,
            RecordSessionEventUseCase recorder) {
        ContractValidator validator = new ContractValidator(new File(contractsDir).getAbsoluteFile());
        Clock clock = Instant::now;
        return new SessionEventSqsConsumer(sqsClient, queueUrl, waitSeconds, mapper, validator, recorder, clock);
    }
}
