package com.fiap.gateway;

import java.net.URI;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.sns.SnsClient;

// Production AwsSdkConfig provides s3Client + sqsClient pointed at ${gateway.aws.endpoint-url};
// LocalStackTestcontainersBase overrides that property via @DynamicPropertySource, so prod's
// beans work against LocalStack without redefinition. SnsClient is the only client prod doesn't
// wire (gateway publishes via orchestrator), so tests bring their own.
@Configuration
public class IntegrationTestAwsConfig {

    @Bean
    public SnsClient snsClient(
            @Value("${gateway.aws.endpoint-url}") String endpoint,
            @Value("${gateway.aws.region}") String region,
            @Value("${gateway.aws.access-key}") String accessKey,
            @Value("${gateway.aws.secret-key}") String secretKey) {
        return SnsClient.builder()
                .endpointOverride(URI.create(endpoint))
                .region(Region.of(region))
                .credentialsProvider(
                        StaticCredentialsProvider.create(
                                AwsBasicCredentials.create(accessKey, secretKey)))
                .httpClient(UrlConnectionHttpClient.create())
                .build();
    }
}
