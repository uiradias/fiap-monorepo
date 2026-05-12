package com.fiap.gateway.infrastructure.config;

import java.net.URI;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.instrumentation.awssdk.v2_2.AwsSdkTelemetry;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.interceptor.ExecutionInterceptor;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.sqs.SqsClient;

@Configuration
public class AwsSdkConfig {

    @Bean
    public ExecutionInterceptor awsSdkOtelInterceptor(OpenTelemetry openTelemetry) {
        return AwsSdkTelemetry.builder(openTelemetry)
                .setCaptureExperimentalSpanAttributes(true)
                .setMessagingReceiveInstrumentationEnabled(true)
                .build()
                .newExecutionInterceptor();
    }

    @Bean
    public S3Client s3Client(
            @Value("${gateway.aws.endpoint-url}") String endpoint,
            @Value("${gateway.aws.region}") String region,
            @Value("${gateway.aws.access-key}") String accessKey,
            @Value("${gateway.aws.secret-key}") String secretKey,
            ExecutionInterceptor awsSdkOtelInterceptor) {
        return S3Client.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(region))
                .credentialsProvider(
                        StaticCredentialsProvider.create(
                                AwsBasicCredentials.create(accessKey, secretKey)))
                .forcePathStyle(true)
                .httpClient(UrlConnectionHttpClient.create())
                .overrideConfiguration(c -> c.addExecutionInterceptor(awsSdkOtelInterceptor))
                .build();
    }

    @Bean
    public SqsClient sqsClient(
            @Value("${gateway.aws.endpoint-url}") String endpoint,
            @Value("${gateway.aws.region}") String region,
            @Value("${gateway.aws.access-key}") String accessKey,
            @Value("${gateway.aws.secret-key}") String secretKey,
            ExecutionInterceptor awsSdkOtelInterceptor) {
        return SqsClient.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(region))
                .credentialsProvider(
                        StaticCredentialsProvider.create(
                                AwsBasicCredentials.create(accessKey, secretKey)))
                .httpClient(UrlConnectionHttpClient.create())
                .overrideConfiguration(c -> c.addExecutionInterceptor(awsSdkOtelInterceptor))
                .build();
    }

    @Bean
    @Qualifier("sessionEventsQueueUrl")
    public String sessionEventsQueueUrl(@Value("${gateway.sqs.session-events-url}") String url) {
        return url;
    }
}
