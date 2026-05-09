package com.fiap.gateway.adapter.in.rest.dto;

import com.fiap.gateway.domain.model.SessionProjection;
import java.time.Instant;
import java.util.UUID;

public record SessionResponse(
        UUID id, String state, Instant lastEventAt, String failureReason, UUID reportId) {
    public static SessionResponse of(SessionProjection p) {
        return new SessionResponse(
                p.id().value(), p.state().name(), p.lastEventAt(),
                p.failureReason(),
                p.reportIdOpt().map(r -> r.value()).orElse(null));
    }
}
