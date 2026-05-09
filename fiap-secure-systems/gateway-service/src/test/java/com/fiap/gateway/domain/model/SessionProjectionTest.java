package com.fiap.gateway.domain.model;

import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class SessionProjectionTest {

    private final SessionId SID = new SessionId(UUID.randomUUID());
    private final UserId UID = new UserId(UUID.randomUUID());
    private final Instant T0 = Instant.parse("2026-05-09T12:00:00Z");

    private SessionEventLogEntry event(SessionState from, SessionState to, Instant t, Map<String, Object> p) {
        return new SessionEventLogEntry(
                new EventId(UUID.randomUUID()), SID, UID, from, to, p, t, t);
    }

    @Test
    void initial_creates_with_state_and_timestamps() {
        SessionProjection p = SessionProjection.initial(SID, UID, SessionState.ASSETS_UPLOADED, T0);
        assertThat(p.state()).isEqualTo(SessionState.ASSETS_UPLOADED);
        assertThat(p.lastEventAt()).isEqualTo(T0);
        assertThat(p.failureReason()).isNull();
    }

    @Test
    void applyEvent_advances_state() {
        SessionProjection p = SessionProjection.initial(SID, UID, SessionState.ASSETS_UPLOADED, T0)
                .applyEvent(event(SessionState.ASSETS_UPLOADED, SessionState.QUEUED_FOR_ANALYSIS,
                        T0.plusSeconds(1), Map.of()));
        assertThat(p.state()).isEqualTo(SessionState.QUEUED_FOR_ANALYSIS);
        assertThat(p.lastEventAt()).isEqualTo(T0.plusSeconds(1));
    }

    @Test
    void applyEvent_captures_errorCode_on_FAILED() {
        SessionProjection p = SessionProjection.initial(SID, UID, SessionState.ANALYZING, T0)
                .applyEvent(event(SessionState.ANALYZING, SessionState.FAILED,
                        T0.plusSeconds(1), Map.of("errorCode", "MODEL_RATE_LIMITED")));
        assertThat(p.failureReason()).isEqualTo("MODEL_RATE_LIMITED");
        assertThat(p.state().isTerminal()).isTrue();
    }

    @Test
    void applyEvent_captures_reportId_on_REPORT_READY() {
        UUID rid = UUID.randomUUID();
        SessionProjection p = SessionProjection.initial(SID, UID, SessionState.ANALYSIS_COMPLETED, T0)
                .applyEvent(event(SessionState.ANALYSIS_COMPLETED, SessionState.REPORT_READY,
                        T0.plusSeconds(1), Map.of("reportId", rid.toString())));
        assertThat(p.reportIdOpt()).contains(new ReportId(rid));
    }

    @Test
    void applyEvent_keeps_latest_lastEventAt_on_late_arrival() {
        SessionProjection p1 = SessionProjection.initial(SID, UID, SessionState.QUEUED_FOR_ANALYSIS, T0.plusSeconds(10));
        SessionProjection p2 = p1.applyEvent(event(SessionState.QUEUED_FOR_ANALYSIS, SessionState.ANALYZING,
                T0.plusSeconds(5), Map.of()));
        // late arrival still advances state, but lastEventAt sticks at the latest seen
        assertThat(p2.state()).isEqualTo(SessionState.ANALYZING);
        assertThat(p2.lastEventAt()).isEqualTo(T0.plusSeconds(10));
    }

    @Test
    void applyEvent_rejects_mismatched_session_id() {
        SessionEventLogEntry foreign = new SessionEventLogEntry(
                new EventId(UUID.randomUUID()),
                new SessionId(UUID.randomUUID()),
                UID,
                null,
                SessionState.ASSETS_UPLOADED,
                Map.of(),
                T0, T0);
        SessionProjection p = SessionProjection.initial(SID, UID, SessionState.ASSETS_UPLOADED, T0);
        org.junit.jupiter.api.Assertions.assertThrows(IllegalArgumentException.class,
                () -> p.applyEvent(foreign));
    }
}
