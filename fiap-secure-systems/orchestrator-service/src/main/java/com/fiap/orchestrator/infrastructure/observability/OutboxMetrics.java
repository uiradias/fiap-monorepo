package com.fiap.orchestrator.infrastructure.observability;

import org.springframework.stereotype.Component;

import com.fiap.orchestrator.domain.port.out.OutboxPort;

import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;

@Component
public class OutboxMetrics {

    public OutboxMetrics(OutboxPort outbox, MeterRegistry registry) {
        Gauge.builder("fss_outbox_unpublished", outbox, OutboxPort::countUnpublished)
                .description("Outbox rows pending publication")
                .register(registry);
    }
}
