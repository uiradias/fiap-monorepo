package com.fiap.orchestrator.domain.port.in;

import java.util.Optional;

import com.fiap.orchestrator.domain.model.AnalysisReport;
import com.fiap.orchestrator.domain.model.Session;
import com.fiap.orchestrator.domain.model.SessionId;

public interface GetSessionUseCase {
    Optional<Session> findSession(SessionId id);

    Optional<AnalysisReport> findReport(SessionId id);
}
