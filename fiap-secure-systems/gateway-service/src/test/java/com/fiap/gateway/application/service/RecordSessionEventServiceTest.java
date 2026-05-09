package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.model.*;
import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class RecordSessionEventServiceTest {

    private final InMemoryFakes.FakeEventLog log = new InMemoryFakes.FakeEventLog();
    private final InMemoryFakes.FakeProjections proj = new InMemoryFakes.FakeProjections();
    private final InMemoryFakes.FakeBroadcaster bcast = new InMemoryFakes.FakeBroadcaster();
    private final RecordSessionEventService svc = new RecordSessionEventService(log, proj, bcast);

    private final SessionId SID = new SessionId(UUID.randomUUID());
    private final UserId UID = new UserId(UUID.randomUUID());
    private final Instant T0 = Instant.parse("2026-05-09T12:00:00Z");

    @Test
    void records_inserts_log_upserts_projection_and_broadcasts() {
        boolean fresh = svc.record(
                new EventId(UUID.randomUUID()), SID, UID, null, SessionState.ASSETS_UPLOADED,
                Map.of(), T0, T0);
        assertThat(fresh).isTrue();
        assertThat(log.byEventId).hasSize(1);
        assertThat(proj.byId.get(SID).state()).isEqualTo(SessionState.ASSETS_UPLOADED);
        assertThat(bcast.broadcasts).hasSize(1);
    }

    @Test
    void duplicate_eventId_is_silent_ack_no_double_broadcast() {
        EventId eid = new EventId(UUID.randomUUID());
        svc.record(eid, SID, UID, null, SessionState.ASSETS_UPLOADED, Map.of(), T0, T0);
        boolean dup = svc.record(eid, SID, UID, null, SessionState.ASSETS_UPLOADED, Map.of(), T0, T0);
        assertThat(dup).isFalse();
        assertThat(bcast.broadcasts).hasSize(1);
    }
}
