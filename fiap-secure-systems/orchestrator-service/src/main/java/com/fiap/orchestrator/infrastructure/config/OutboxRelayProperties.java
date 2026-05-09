package com.fiap.orchestrator.infrastructure.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "orchestrator.outbox")
public record OutboxRelayProperties(
        long relayIntervalMs,
        int batchSize,
        int maxPublishAttemptsBeforeAlert
) {
    public OutboxRelayProperties {
        if (relayIntervalMs <= 0) relayIntervalMs = 500;
        if (batchSize <= 0) batchSize = 20;
        if (maxPublishAttemptsBeforeAlert <= 0) maxPublishAttemptsBeforeAlert = 10;
    }
}
