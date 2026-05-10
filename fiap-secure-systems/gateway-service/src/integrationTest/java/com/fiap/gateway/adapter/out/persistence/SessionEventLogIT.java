package com.fiap.gateway.adapter.out.persistence;

import static org.assertj.core.api.Assertions.assertThat;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import com.fiap.gateway.PostgresTestcontainersBase;
import com.fiap.gateway.domain.model.*;

class SessionEventLogIT extends PostgresTestcontainersBase {

    @Autowired SessionEventLogRepositoryAdapter log;
    @Autowired SessionProjectionRepositoryAdapter projections;

    @Test
    void insertIfAbsent_dedups_on_eventId_and_tail_returns_in_order() {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        Instant t0 = Instant.parse("2026-05-09T12:00:00Z");

        // Establish a projection so the user_id linkage exists for inspection.
        projections.upsert(SessionProjection.initial(sid, uid, SessionState.ASSETS_UPLOADED, t0));

        SessionEventLogEntry e1 =
                new SessionEventLogEntry(
                        new EventId(UUID.randomUUID()),
                        sid,
                        uid,
                        null,
                        SessionState.ASSETS_UPLOADED,
                        Map.of(),
                        t0,
                        t0);
        SessionEventLogEntry e2 =
                new SessionEventLogEntry(
                        new EventId(UUID.randomUUID()),
                        sid,
                        uid,
                        SessionState.ASSETS_UPLOADED,
                        SessionState.QUEUED_FOR_ANALYSIS,
                        Map.of(),
                        t0.plusSeconds(1),
                        t0.plusSeconds(1));

        assertThat(log.insertIfAbsent(e1)).isTrue();
        assertThat(log.insertIfAbsent(e2)).isTrue();
        assertThat(log.insertIfAbsent(e1)).isFalse(); // duplicate, silent ack

        assertThat(log.tailForSession(sid, 10))
                .extracting(x -> x.toState().name())
                .containsExactly("ASSETS_UPLOADED", "QUEUED_FOR_ANALYSIS");
    }
}
