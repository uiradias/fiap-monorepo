package com.fiap.orchestrator.domain.port.out;

import java.util.Collection;
import java.util.Map;
import java.util.Optional;

import com.fiap.orchestrator.domain.model.AnalysisReport;
import com.fiap.orchestrator.domain.model.ReportId;
import com.fiap.orchestrator.domain.model.SessionId;

public interface ReportRepositoryPort {
    Optional<AnalysisReport> findBySessionId(SessionId sessionId);

    AnalysisReport save(AnalysisReport report);

    /** Report id per session id (only sessions that already have a stored report). */
    Map<SessionId, ReportId> findReportIdsBySessionIds(Collection<SessionId> sessionIds);
}
