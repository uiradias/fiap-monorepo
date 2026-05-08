package com.fiap.orchestrator.domain.port.in;

import com.fiap.orchestrator.domain.model.AnalysisReport;
import com.fiap.orchestrator.domain.model.Session;
import com.fiap.orchestrator.domain.model.SessionId;

import java.util.Optional;

public interface GetSessionUseCase {
    Optional<Session> findSession(SessionId id);
    Optional<AnalysisReport> findReport(SessionId id);
}
