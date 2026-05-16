package com.fiap.gateway.application.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.exception.ForbiddenException;
import com.fiap.gateway.domain.exception.SessionNotFoundException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.GetSessionUseCase;
import com.fiap.gateway.domain.port.out.OrchestratorClientPort;
import com.fiap.gateway.domain.port.out.SessionProjectionRepositoryPort;

@Service
public class GetSessionService implements GetSessionUseCase {

    private final SessionProjectionRepositoryPort projections;
    private final OrchestratorClientPort orchestrator;

    public GetSessionService(
            SessionProjectionRepositoryPort projections, OrchestratorClientPort orchestrator) {
        this.projections = projections;
        this.orchestrator = orchestrator;
    }

    @Override
    @Transactional
    public SessionProjection get(SessionId sessionId, UserId requester) {
        SessionProjection local =
                projections
                        .findById(sessionId)
                        .filter(p -> p.userId().equals(requester))
                        .orElse(null);
        if (local != null) {
            return local;
        }
        SessionProjection fromOrch = orchestrator.getSession(sessionId);
        if (fromOrch == null) {
            throw new SessionNotFoundException(sessionId);
        }
        if (!fromOrch.userId().equals(requester)) {
            throw new ForbiddenException("session " + sessionId);
        }
        projections.upsert(fromOrch);
        return fromOrch;
    }
}
