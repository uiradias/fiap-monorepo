package com.fiap.orchestrator.infrastructure.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.orchestrator.adapter.in.messaging.AnalysisResultSqsConsumer;
import com.fiap.orchestrator.adapter.out.messaging.SnsSessionEventPublisher;
import com.fiap.orchestrator.adapter.out.messaging.SqsAnalysisJobPublisher;
import com.fiap.orchestrator.application.service.Clock;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisCompletedUseCase;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisFailedUseCase;
import com.fiap.orchestrator.domain.port.in.HandleAnalysisStartedUseCase;
import com.fiap.orchestrator.infrastructure.schema.ContractValidator;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.services.sns.SnsClient;
import software.amazon.awssdk.services.sqs.SqsClient;

import java.io.File;

@Configuration
public class CompositionConfig {

    @Bean
    public Clock systemClock() {
        java.time.Clock jdk = java.time.Clock.systemUTC();
        return jdk::instant;
    }

    @Bean
    public ContractValidator contractValidator(
            @Value("${orchestrator.contracts-dir}") String contractsDir) {
        return new ContractValidator(new File(contractsDir).getAbsoluteFile());
    }

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper();
    }

    @Bean
    public SqsAnalysisJobPublisher sqsAnalysisJobPublisher(
            SqsClient sqs,
            @Qualifier("analysisJobsQueueUrl") String queueUrl,
            ContractValidator validator,
            ObjectMapper mapper) {
        return new SqsAnalysisJobPublisher(sqs, queueUrl, validator, mapper);
    }

    @Bean
    public SnsSessionEventPublisher snsSessionEventPublisher(
            SnsClient sns,
            @Qualifier("sessionEventsTopicArn") String topicArn,
            ContractValidator validator,
            ObjectMapper mapper) {
        return new SnsSessionEventPublisher(sns, topicArn, validator, mapper);
    }

    @Bean(initMethod = "start", destroyMethod = "stop")
    public AnalysisResultSqsConsumer analysisResultSqsConsumer(
            SqsClient sqs,
            @Qualifier("analysisResultsQueueUrl") String queueUrl,
            @Value("${orchestrator.sqs.poll-wait-seconds:10}") int waitSeconds,
            ObjectMapper mapper,
            ContractValidator validator,
            HandleAnalysisStartedUseCase started,
            HandleAnalysisCompletedUseCase completed,
            HandleAnalysisFailedUseCase failed,
            Clock clock) {
        return new AnalysisResultSqsConsumer(
                sqs, queueUrl, waitSeconds, mapper, validator, started, completed, failed, clock);
    }
}
