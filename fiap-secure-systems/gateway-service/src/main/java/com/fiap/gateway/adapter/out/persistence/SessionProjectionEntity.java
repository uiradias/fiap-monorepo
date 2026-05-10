package com.fiap.gateway.adapter.out.persistence;

import java.time.Instant;
import java.util.UUID;

import jakarta.persistence.*;

@Entity
@Table(name = "session_projections")
public class SessionProjectionEntity {
    @Id public UUID id;

    @Column(name = "user_id", nullable = false)
    public UUID userId;

    @Column(nullable = false)
    public String state;

    @Column(name = "last_event_at", nullable = false)
    public Instant lastEventAt;

    @Column(name = "failure_reason")
    public String failureReason;

    @Column(name = "report_id")
    public UUID reportId;
}
