package com.fiap.gateway.application.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.exception.ReportNotReadyException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.GetReportUseCase;
import com.fiap.gateway.domain.port.in.GetSessionUseCase;
import com.fiap.gateway.domain.port.out.OrchestratorClientPort;

@Service
public class GetReportService implements GetReportUseCase {

    private final GetSessionUseCase getSession;
    private final OrchestratorClientPort orchestrator;

    public GetReportService(GetSessionUseCase getSession, OrchestratorClientPort orchestrator) {
        this.getSession = getSession;
        this.orchestrator = orchestrator;
    }

    @Override
    @Transactional
    public AnalysisReport get(SessionId sessionId, UserId requester) {
        SessionProjection p = getSession.get(sessionId, requester);
        if (p.state() != SessionState.REPORT_READY) {
            throw new ReportNotReadyException(sessionId, p.state());
        }
        return orchestrator.getReport(sessionId);
    }
}
