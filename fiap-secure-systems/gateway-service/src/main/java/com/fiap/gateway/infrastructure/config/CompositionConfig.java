package com.fiap.gateway.infrastructure.config;

import java.io.File;
import java.io.IOException;
import java.time.Duration;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fiap.gateway.adapter.in.messaging.SessionEventSqsConsumer;
import com.fiap.gateway.adapter.out.http.InternalHmacRequestSigner;
import com.fiap.gateway.adapter.out.http.OrchestratorRestClient;
import com.fiap.gateway.adapter.out.s3.S3AssetStorageAdapter;
import com.fiap.gateway.adapter.out.security.BcryptPasswordHasher;
import com.fiap.gateway.adapter.out.security.JwtTokenIssuer;
import com.fiap.gateway.application.service.Clock;
import com.fiap.gateway.domain.port.in.RecordSessionEventUseCase;
import com.fiap.gateway.domain.port.out.AssetStoragePort;
import com.fiap.gateway.domain.port.out.OrchestratorClientPort;
import com.fiap.gateway.domain.port.out.PasswordHasherPort;
import com.fiap.gateway.domain.port.out.TokenIssuerPort;
import com.fiap.gateway.infrastructure.schema.ContractValidator;

import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.sqs.SqsClient;

@Configuration
public class CompositionConfig {

    @Bean
    public Clock systemClock() {
        java.time.Clock jdk = java.time.Clock.systemUTC();
        return jdk::instant;
    }

    @Bean
    public Duration refreshTokenTtl(@Value("${gateway.jwt.refresh-ttl-days}") int days) {
        return Duration.ofDays(days);
    }

    @Bean
    public ContractValidator contractValidator(
            @Value("${gateway.contracts-dir}") String contractsDir) {
        return new ContractValidator(new File(contractsDir).getAbsoluteFile());
    }

    @Bean
    public PasswordHasherPort passwordHasher() {
        return new BcryptPasswordHasher();
    }

    @Bean
    public TokenIssuerPort jwtTokenIssuer(
            @Value("${gateway.jwt.private-key-path}") String priv,
            @Value("${gateway.jwt.public-key-path}") String pub,
            @Value("${gateway.jwt.issuer}") String issuer,
            @Value("${gateway.jwt.access-ttl-minutes}") int accessMinutes,
            @Value("${gateway.jwt.refresh-ttl-days}") int refreshDays)
            throws IOException {
        return new JwtTokenIssuer(
                priv, pub, issuer, Duration.ofMinutes(accessMinutes), Duration.ofDays(refreshDays));
    }

    @Bean
    public AssetStoragePort assetStorage(
            S3Client s3, @Value("${gateway.s3.bucket}") String bucket) {
        return new S3AssetStorageAdapter(s3, bucket);
    }

    @Bean
    public InternalHmacRequestSigner internalHmacRequestSigner(
            @Value("${gateway.orchestrator.hmac-secret}") String secret) {
        return new InternalHmacRequestSigner(secret);
    }

    @Bean
    public OrchestratorClientPort orchestratorClient(
            @Value("${gateway.orchestrator.base-url}") String baseUrl,
            InternalHmacRequestSigner signer,
            Clock clock,
            @Value("${gateway.orchestrator.hmac-secret}") String secret) {
        return new OrchestratorRestClient(
                RestClient.builder().baseUrl(baseUrl).build(), signer, clock, secret);
    }

    @Bean(initMethod = "start", destroyMethod = "stop")
    public SessionEventSqsConsumer sessionEventSqsConsumer(
            SqsClient sqs,
            @Qualifier("sessionEventsQueueUrl") String queueUrl,
            @Value("${gateway.sqs.poll-wait-seconds:10}") int waitSeconds,
            ObjectMapper mapper,
            ContractValidator validator,
            RecordSessionEventUseCase recorder,
            Clock clock) {
        return new SessionEventSqsConsumer(
                sqs, queueUrl, waitSeconds, mapper, validator, recorder, clock);
    }
}
