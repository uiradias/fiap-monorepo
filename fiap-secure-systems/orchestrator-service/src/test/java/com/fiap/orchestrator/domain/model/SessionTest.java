package com.fiap.orchestrator.domain.model;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;
import java.util.UUID;

import org.junit.jupiter.api.Test;

class SessionTest {

    private static final SessionId SID = new SessionId(UUID.randomUUID());
    private static final UserId UID = new UserId(UUID.randomUUID());
    private static final Instant NOW = Instant.parse("2026-01-01T00:00:00Z");

    @Test
    void newSession_starts_in_ASSETS_UPLOADED_with_version_zero() {
        Session s = Session.newSession(SID, UID, 3, NOW);
        assertThat(s.id()).isEqualTo(SID);
        assertThat(s.userId()).isEqualTo(UID);
        assertThat(s.state()).isEqualTo(SessionState.ASSETS_UPLOADED);
        assertThat(s.assetCount()).isEqualTo(3);
        assertThat(s.version()).isEqualTo(0L);
        assertThat(s.failureReason()).isNull();
    }

    @Test
    void withState_returns_new_instance_with_bumped_version() {
        Session s = Session.newSession(SID, UID, 3, NOW);
        Session moved = s.withState(SessionState.QUEUED_FOR_ANALYSIS, NOW.plusSeconds(1));
        assertThat(moved.state()).isEqualTo(SessionState.QUEUED_FOR_ANALYSIS);
        assertThat(moved.version()).isEqualTo(1L);
        assertThat(moved.updatedAt()).isEqualTo(NOW.plusSeconds(1));
        // original is untouched
        assertThat(s.state()).isEqualTo(SessionState.ASSETS_UPLOADED);
        assertThat(s.version()).isEqualTo(0L);
    }

    @Test
    void asset_count_must_be_positive() {
        assertThatThrownBy(() -> Session.newSession(SID, UID, 0, NOW))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("assetCount");
        assertThatThrownBy(() -> Session.newSession(SID, UID, -1, NOW))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void failed_session_with_reason() {
        Session s = Session.newSession(SID, UID, 3, NOW);
        Session failed =
                s.withFailure(SessionState.FAILED, "MODEL_RATE_LIMITED", NOW.plusSeconds(5));
        assertThat(failed.state()).isEqualTo(SessionState.FAILED);
        assertThat(failed.failureReason()).isEqualTo("MODEL_RATE_LIMITED");
        assertThat(failed.version()).isEqualTo(1L);
    }
}
