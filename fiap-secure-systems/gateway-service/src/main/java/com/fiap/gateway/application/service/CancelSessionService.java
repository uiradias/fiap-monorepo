package com.fiap.gateway.application.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.model.SessionId;
import com.fiap.gateway.domain.model.UserId;
import com.fiap.gateway.domain.port.in.CancelSessionUseCase;
import com.fiap.gateway.domain.port.in.GetSessionUseCase;
import com.fiap.gateway.domain.port.out.OrchestratorClientPort;

@Service
public class CancelSessionService implements CancelSessionUseCase {

    private final GetSessionUseCase getSession;
    private final OrchestratorClientPort orchestrator;

    public CancelSessionService(GetSessionUseCase getSession, OrchestratorClientPort orchestrator) {
        this.getSession = getSession;
        this.orchestrator = orchestrator;
    }

    @Override
    @Transactional
    public void cancel(SessionId sessionId, UserId requester) {
        getSession.get(sessionId, requester);
        orchestrator.cancelSession(sessionId);
    }
}
