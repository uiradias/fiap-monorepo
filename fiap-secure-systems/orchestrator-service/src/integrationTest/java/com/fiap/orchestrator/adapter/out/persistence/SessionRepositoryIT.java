package com.fiap.orchestrator.adapter.out.persistence;

import com.fiap.orchestrator.PostgresTestcontainersBase;
import com.fiap.orchestrator.domain.model.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.OptimisticLockingFailureException;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class SessionRepositoryIT extends PostgresTestcontainersBase {

    @Autowired SessionRepositoryAdapter adapter;

    @Test
    void insertIfAbsent_is_idempotent() {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        Session s = Session.newSession(sid, uid, 3, Instant.now());
        Session a = adapter.insertIfAbsent(s);
        Session b = adapter.insertIfAbsent(s);
        assertThat(a.id()).isEqualTo(b.id());
        assertThat(b.version()).isEqualTo(0L);
    }

    @Test
    void save_increments_version_on_state_change() {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        Session s = adapter.insertIfAbsent(Session.newSession(sid, uid, 3, Instant.now()));
        Session moved = adapter.save(s.withState(SessionState.QUEUED_FOR_ANALYSIS, Instant.now()));
        assertThat(moved.state()).isEqualTo(SessionState.QUEUED_FOR_ANALYSIS);
        assertThat(moved.version()).isEqualTo(1L);
    }

    @Test
    void stale_save_throws_optimistic_lock() {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        Session s0 = adapter.insertIfAbsent(Session.newSession(sid, uid, 3, Instant.now()));
        adapter.save(s0.withState(SessionState.QUEUED_FOR_ANALYSIS, Instant.now()));
        assertThatThrownBy(() -> adapter.save(
                s0.withState(SessionState.QUEUED_FOR_ANALYSIS, Instant.now())))
                .isInstanceOf(OptimisticLockingFailureException.class);
    }

    @Test
    void appendEvent_persists_with_jsonb_payload() {
        SessionId sid = new SessionId(UUID.randomUUID());
        UserId uid = new UserId(UUID.randomUUID());
        Session s = adapter.insertIfAbsent(Session.newSession(sid, uid, 3, Instant.now()));
        SessionEvent ev = SessionEvent.transition(
                new EventId(UUID.randomUUID()), s.id(),
                SessionState.ASSETS_UPLOADED, SessionState.QUEUED_FOR_ANALYSIS,
                Map.of("trigger", "OUTBOX_JOB_PUBLISHED"),
                Instant.now());
        adapter.appendEvent(ev);
    }
}
