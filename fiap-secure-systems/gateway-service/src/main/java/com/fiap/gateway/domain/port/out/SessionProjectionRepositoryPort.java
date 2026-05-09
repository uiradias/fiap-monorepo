package com.fiap.gateway.domain.port.out;

import com.fiap.gateway.domain.model.*;

import java.util.Optional;

public interface SessionProjectionRepositoryPort {
    SessionProjection upsert(SessionProjection projection);
    Optional<SessionProjection> findById(SessionId id);
}
