package com.fiap.gateway.domain.model;

import java.time.Instant;
import java.util.Objects;
import java.util.Optional;

public record SessionProjection(
        SessionId id,
        UserId userId,
        SessionState state,
        Instant lastEventAt,
        String failureReason, // populated on FAILED transitions
        ReportId reportId) { // populated when REPORT_READY arrives

    public SessionProjection {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(userId, "userId");
        Objects.requireNonNull(state, "state");
        Objects.requireNonNull(lastEventAt, "lastEventAt");
    }

    public static SessionProjection initial(
            SessionId id, UserId userId, SessionState toState, Instant occurredAt) {
        return new SessionProjection(id, userId, toState, occurredAt, null, null);
    }

    public SessionProjection applyEvent(SessionEventLogEntry e) {
        if (!e.sessionId().equals(id)) {
            throw new IllegalArgumentException(
                    "event session " + e.sessionId() + " != projection " + id);
        }
        // Late-arriving events (occurredAt before lastEventAt) are still applied if they advance
        // the terminal state; otherwise we keep the latest event_at to track liveness.
        Instant nextEventAt = e.occurredAt().isAfter(lastEventAt) ? e.occurredAt() : lastEventAt;

        String nextFailure = failureReason;
        ReportId nextReportId = reportId;
        if (e.toState() == SessionState.FAILED) {
            Object code = e.payload().get("errorCode");
            nextFailure =
                    code != null
                            ? code.toString()
                            : (failureReason != null ? failureReason : "FAILED");
        }
        if (e.toState() == SessionState.REPORT_READY) {
            Object rid = e.payload().get("reportId");
            if (rid != null) {
                try {
                    nextReportId = new ReportId(java.util.UUID.fromString(rid.toString()));
                } catch (IllegalArgumentException ignored) {
                    /* keep prior */
                }
            }
        }
        return new SessionProjection(
                id, userId, e.toState(), nextEventAt, nextFailure, nextReportId);
    }

    public Optional<ReportId> reportIdOpt() {
        return Optional.ofNullable(reportId);
    }
}
