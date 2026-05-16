package com.fiap.gateway.domain.port.out;

import java.util.List;
import java.util.Optional;

import com.fiap.gateway.domain.model.*;

public interface SessionProjectionRepositoryPort {
    SessionProjection upsert(SessionProjection projection);

    Optional<SessionProjection> findById(SessionId id);

    /**
     * Sessions this user has touched (finalize seeds a row; SQS events keep it fresh). Joins the
     * originating asset bundle when present so the list can show asset counts and created time.
     */
    List<SessionSummary> listSummariesByUser(UserId userId, int limit);
}
