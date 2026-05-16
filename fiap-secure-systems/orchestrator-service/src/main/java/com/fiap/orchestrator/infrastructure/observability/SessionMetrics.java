package com.fiap.orchestrator.infrastructure.observability;

import java.time.Duration;

import org.springframework.stereotype.Component;

import com.fiap.orchestrator.domain.model.SessionState;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;

@Component
public class SessionMetrics {

    private final MeterRegistry registry;
    private final Timer sessionDuration;

    public SessionMetrics(MeterRegistry registry) {
        this.registry = registry;
        this.sessionDuration =
                Timer.builder("fss_session_duration")
                        .description("End-to-end session duration from creation to terminal state")
                        .publishPercentileHistogram()
                        .register(registry);
    }

    public void recordTransition(SessionState toState, String errorCode) {
        Counter.builder("fss_session_transitions_total")
                .description("Session state transitions, labelled by destination state")
                .tag("to_state", toState.name())
                .tag("error_code", errorCode == null ? "" : errorCode)
                .register(registry)
                .increment();
    }

    public void recordSessionDuration(Duration duration) {
        sessionDuration.record(duration);
    }
}
