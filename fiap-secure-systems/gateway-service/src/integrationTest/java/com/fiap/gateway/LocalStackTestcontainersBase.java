package com.fiap.gateway;

import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.localstack.LocalStackContainer;
import org.testcontainers.utility.DockerImageName;

// Singleton container pattern — see PostgresTestcontainersBase for the rationale on why
// @Testcontainers/@Container are intentionally absent here.
public abstract class LocalStackTestcontainersBase extends PostgresTestcontainersBase {

    static final LocalStackContainer LOCALSTACK;

    static {
        LOCALSTACK =
                new LocalStackContainer(DockerImageName.parse("localstack/localstack:3.5"))
                        .withServices(
                                LocalStackContainer.Service.S3,
                                LocalStackContainer.Service.SQS,
                                LocalStackContainer.Service.SNS);
        LOCALSTACK.start();
    }

    @DynamicPropertySource
    static void registerLocalStackProperties(DynamicPropertyRegistry registry) throws Exception {
        Provisioning.ensure(LOCALSTACK);
        registry.add("gateway.aws.endpoint-url", LOCALSTACK::getEndpoint);
        registry.add("gateway.aws.region", LOCALSTACK::getRegion);
        registry.add("gateway.aws.access-key", LOCALSTACK::getAccessKey);
        registry.add("gateway.aws.secret-key", LOCALSTACK::getSecretKey);
        registry.add("gateway.s3.bucket", () -> Provisioning.bucket);
        registry.add("gateway.sqs.session-events-url", () -> Provisioning.sessionEventsUrl);
        registry.add(
                "gateway.contracts-dir",
                () -> new java.io.File("../infrastructure/contracts").getAbsolutePath());
    }
}
