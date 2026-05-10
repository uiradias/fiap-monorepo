package com.fiap.orchestrator.domain.port.out;

import java.util.Optional;

import com.fiap.orchestrator.domain.model.AnalysisReport;
import com.fiap.orchestrator.domain.model.SessionId;

public interface ReportRepositoryPort {
    Optional<AnalysisReport> findBySessionId(SessionId sessionId);

    AnalysisReport save(AnalysisReport report);
}
