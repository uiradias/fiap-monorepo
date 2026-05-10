package com.fiap.gateway.application.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.exception.ForbiddenException;
import com.fiap.gateway.domain.exception.SessionNotFoundException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.CancelSessionUseCase;
import com.fiap.gateway.domain.port.out.OrchestratorClientPort;
import com.fiap.gateway.domain.port.out.SessionProjectionRepositoryPort;

@Service
public class CancelSessionService implements CancelSessionUseCase {

    private final SessionProjectionRepositoryPort projections;
    private final OrchestratorClientPort orchestrator;

    public CancelSessionService(
            SessionProjectionRepositoryPort projections, OrchestratorClientPort orchestrator) {
        this.projections = projections;
        this.orchestrator = orchestrator;
    }

    @Override
    @Transactional
    public void cancel(SessionId sessionId, UserId requester) {
        SessionProjection p =
                projections
                        .findById(sessionId)
                        .orElseThrow(() -> new SessionNotFoundException(sessionId));
        if (!p.userId().equals(requester)) throw new ForbiddenException("session " + sessionId);
        // canonical state lives in orchestrator; gateway just relays
        orchestrator.cancelSession(sessionId);
    }
}
