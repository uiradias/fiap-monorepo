package com.fiap.gateway;

import com.fiap.gateway.adapter.out.s3.S3AssetStorageAdapter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.http.urlconnection.UrlConnectionHttpClient;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;

import java.net.URI;

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
}
