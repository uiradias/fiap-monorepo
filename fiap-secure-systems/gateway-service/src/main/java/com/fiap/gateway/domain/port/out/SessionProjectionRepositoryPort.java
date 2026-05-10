package com.fiap.gateway.domain.port.out;

import java.util.Optional;

import com.fiap.gateway.domain.model.*;

public interface SessionProjectionRepositoryPort {
    SessionProjection upsert(SessionProjection projection);

    Optional<SessionProjection> findById(SessionId id);
}
