package com.fiap.orchestrator;

import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.localstack.LocalStackContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.utility.DockerImageName;

public abstract class LocalStackTestcontainersBase extends PostgresTestcontainersBase {

    @Container
    public static final LocalStackContainer LOCALSTACK =
            new LocalStackContainer(DockerImageName.parse("localstack/localstack:3.5"))
                    .withServices(LocalStackContainer.Service.SQS, LocalStackContainer.Service.SNS);

    @DynamicPropertySource
    static void registerLocalStackProperties(DynamicPropertyRegistry registry) {
        registry.add("orchestrator.aws.endpoint-url", () -> LOCALSTACK.getEndpoint().toString());
        registry.add("orchestrator.aws.region", LOCALSTACK::getRegion);
        registry.add("orchestrator.aws.access-key", LOCALSTACK::getAccessKey);
        registry.add("orchestrator.aws.secret-key", LOCALSTACK::getSecretKey);
    }
}
