package com.fiap.orchestrator.application.service;

import java.util.Optional;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.orchestrator.domain.model.AnalysisReport;
import com.fiap.orchestrator.domain.model.Session;
import com.fiap.orchestrator.domain.model.SessionId;
import com.fiap.orchestrator.domain.port.in.GetSessionUseCase;
import com.fiap.orchestrator.domain.port.out.ReportRepositoryPort;
import com.fiap.orchestrator.domain.port.out.SessionRepositoryPort;

@Service
@Transactional(readOnly = true)
public class GetSessionService implements GetSessionUseCase {

    private final SessionRepositoryPort sessions;
    private final ReportRepositoryPort reports;

    public GetSessionService(SessionRepositoryPort sessions, ReportRepositoryPort reports) {
        this.sessions = sessions;
        this.reports = reports;
    }

    @Override
    public Optional<Session> findSession(SessionId id) {
        return sessions.findById(id);
    }

    @Override
    public Optional<AnalysisReport> findReport(SessionId id) {
        return reports.findBySessionId(id);
    }
}
