package com.fiap.gateway.adapter.out.persistence;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface SessionEventLogJpaRepository extends JpaRepository<SessionEventLogEntity, UUID> {

    @Modifying
    @Query(
            value =
                    """
INSERT INTO session_event_log
  (event_id, session_id, user_id, from_state, to_state, payload, occurred_at, received_at)
VALUES
  (:eventId, :sessionId, :userId, :fromState, :toState, CAST(:payload AS jsonb), :occurredAt, :receivedAt)
ON CONFLICT (event_id) DO NOTHING
""",
            nativeQuery = true)
    int insertIfAbsent(
            @Param("eventId") UUID eventId,
            @Param("sessionId") UUID sessionId,
            @Param("userId") UUID userId,
            @Param("fromState") String fromState,
            @Param("toState") String toState,
            @Param("payload") String payload,
            @Param("occurredAt") Instant occurredAt,
            @Param("receivedAt") Instant receivedAt);

    @Query(
            value =
                    """
                    SELECT * FROM session_event_log
                    WHERE session_id = :sid
                    ORDER BY occurred_at ASC, event_id ASC
                    LIMIT :limit
                    """,
            nativeQuery = true)
    List<SessionEventLogEntity> tailForSession(@Param("sid") UUID sid, @Param("limit") int limit);
}
