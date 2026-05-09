package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.exception.ForbiddenException;
import com.fiap.gateway.domain.exception.ReportNotReadyException;
import com.fiap.gateway.domain.exception.SessionNotFoundException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.GetReportUseCase;
import com.fiap.gateway.domain.port.out.OrchestratorClientPort;
import com.fiap.gateway.domain.port.out.SessionProjectionRepositoryPort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class GetReportService implements GetReportUseCase {

    private final SessionProjectionRepositoryPort projections;
    private final OrchestratorClientPort orchestrator;

    public GetReportService(SessionProjectionRepositoryPort projections,
                            OrchestratorClientPort orchestrator) {
        this.projections = projections;
        this.orchestrator = orchestrator;
    }

    @Override
    @Transactional(readOnly = true)
    public AnalysisReport get(SessionId sessionId, UserId requester) {
        SessionProjection p = projections.findById(sessionId)
                .orElseThrow(() -> new SessionNotFoundException(sessionId));
        if (!p.userId().equals(requester)) throw new ForbiddenException("session " + sessionId);
        if (p.state() != SessionState.REPORT_READY) {
            throw new ReportNotReadyException(sessionId, p.state());
        }
        return orchestrator.getReport(sessionId);
    }
}
