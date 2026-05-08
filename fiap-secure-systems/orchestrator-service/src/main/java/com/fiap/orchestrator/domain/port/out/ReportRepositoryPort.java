package com.fiap.orchestrator.domain.port.out;

import com.fiap.orchestrator.domain.model.AnalysisReport;
import com.fiap.orchestrator.domain.model.SessionId;

import java.util.Optional;

public interface ReportRepositoryPort {
    Optional<AnalysisReport> findBySessionId(SessionId sessionId);
    AnalysisReport save(AnalysisReport report);
}
