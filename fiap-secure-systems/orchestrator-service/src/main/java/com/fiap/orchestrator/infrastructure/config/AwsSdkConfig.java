package com.fiap.orchestrator.infrastructure.config;

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
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sqs.SqsClient;

@Configuration
public class AwsSdkConfig {

    @Bean
    public ExecutionInterceptor awsSdkOtelInterceptor(OpenTelemetry openTelemetry) {
        return AwsSdkTelemetry.builder(openTelemetry)
                .setCaptureExperimentalSpanAttributes(true)
                .setMessagingReceiveInstrumentationEnabled(true)
                .setUseConfiguredPropagatorForMessaging(true)
                .build()
                .newExecutionInterceptor();
    }

    @Bean
    public SqsClient sqsClient(
            @Value("${orchestrator.aws.endpoint-url}") String endpoint,
            @Value("${orchestrator.aws.region}") String region,
            @Value("${orchestrator.aws.access-key}") String accessKey,
            @Value("${orchestrator.aws.secret-key}") String secretKey,
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
    public SnsClient snsClient(
            @Value("${orchestrator.aws.endpoint-url}") String endpoint,
            @Value("${orchestrator.aws.region}") String region,
            @Value("${orchestrator.aws.access-key}") String accessKey,
            @Value("${orchestrator.aws.secret-key}") String secretKey,
            ExecutionInterceptor awsSdkOtelInterceptor) {
        return SnsClient.builder()
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
    @Qualifier("analysisJobsQueueUrl")
    public String analysisJobsQueueUrl(@Value("${orchestrator.sqs.analysis-jobs-url}") String url) {
        return url;
    }

    @Bean
    @Qualifier("analysisResultsQueueUrl")
    public String analysisResultsQueueUrl(
            @Value("${orchestrator.sqs.analysis-results-url}") String url) {
        return url;
    }

    @Bean
    @Qualifier("analysisResultsDlqUrl")
    public String analysisResultsDlqUrl(
            @Value("${orchestrator.sqs.analysis-results-dlq-url}") String url) {
        return url;
    }

    @Bean
    @Qualifier("sessionEventsTopicArn")
    public String sessionEventsTopicArn(
            @Value("${orchestrator.sns.session-events-topic-arn}") String arn) {
        return arn;
    }
}
