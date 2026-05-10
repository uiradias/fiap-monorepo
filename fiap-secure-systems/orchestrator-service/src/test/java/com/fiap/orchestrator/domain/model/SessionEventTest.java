package com.fiap.orchestrator.domain.model;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.Test;

class SessionEventTest {

    @Test
    void initial_event_has_null_fromState() {
        SessionEvent e =
                SessionEvent.initial(
                        new EventId(UUID.randomUUID()),
                        new SessionId(UUID.randomUUID()),
                        SessionState.ASSETS_UPLOADED,
                        Map.of(),
                        Instant.parse("2026-01-01T00:00:00Z"));
        assertThat(e.fromState()).isNull();
        assertThat(e.toState()).isEqualTo(SessionState.ASSETS_UPLOADED);
    }

    @Test
    void transition_event_has_both_states() {
        SessionEvent e =
                SessionEvent.transition(
                        new EventId(UUID.randomUUID()),
                        new SessionId(UUID.randomUUID()),
                        SessionState.ASSETS_UPLOADED,
                        SessionState.QUEUED_FOR_ANALYSIS,
                        Map.of("reason", "outbox-confirmed"),
                        Instant.parse("2026-01-01T00:00:00Z"));
        assertThat(e.fromState()).isEqualTo(SessionState.ASSETS_UPLOADED);
        assertThat(e.toState()).isEqualTo(SessionState.QUEUED_FOR_ANALYSIS);
        assertThat(e.payload()).containsEntry("reason", "outbox-confirmed");
    }

    @Test
    void transition_must_change_state() {
        assertThatThrownBy(
                        () ->
                                SessionEvent.transition(
                                        new EventId(UUID.randomUUID()),
                                        new SessionId(UUID.randomUUID()),
                                        SessionState.ANALYZING,
                                        SessionState.ANALYZING,
                                        Map.of(),
                                        Instant.now()))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("must change");
    }
}
