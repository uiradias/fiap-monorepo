package com.fiap.gateway.adapter.out.persistence;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "session_event_log")
public class SessionEventLogEntity {
    @Id @Column(name = "event_id") public UUID eventId;
    @Column(name = "session_id", nullable = false) public UUID sessionId;
    @Column(name = "user_id", nullable = false) public UUID userId;
    @Column(name = "from_state") public String fromState;
    @Column(name = "to_state", nullable = false) public String toState;
    @Column(nullable = false, columnDefinition = "jsonb") public String payload;       // raw JSON string
    @Column(name = "occurred_at", nullable = false) public Instant occurredAt;
    @Column(name = "received_at", nullable = false) public Instant receivedAt;
}
