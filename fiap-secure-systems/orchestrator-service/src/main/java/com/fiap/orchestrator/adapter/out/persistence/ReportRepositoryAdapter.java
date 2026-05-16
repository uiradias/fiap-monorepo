package com.fiap.orchestrator.adapter.out.persistence;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.springframework.stereotype.Repository;

import com.fiap.orchestrator.domain.model.AnalysisReport;
import com.fiap.orchestrator.domain.model.ReportId;
import com.fiap.orchestrator.domain.model.SessionId;
import com.fiap.orchestrator.domain.port.out.ReportRepositoryPort;

@Repository
public class ReportRepositoryAdapter implements ReportRepositoryPort {

    private final AnalysisReportJpaRepository reports;

    public ReportRepositoryAdapter(AnalysisReportJpaRepository reports) {
        this.reports = reports;
    }

    @Override
    public Optional<AnalysisReport> findBySessionId(SessionId sessionId) {
        return reports.findBySessionId(sessionId.value()).map(AnalysisReportEntity::toDomain);
    }

    @Override
    public AnalysisReport save(AnalysisReport report) {
        return reports.save(AnalysisReportEntity.from(report)).toDomain();
    }

    @Override
    public Map<SessionId, ReportId> findReportIdsBySessionIds(Collection<SessionId> sessionIds) {
        if (sessionIds == null || sessionIds.isEmpty()) {
            return Map.of();
        }
        List<UUID> ids = sessionIds.stream().map(SessionId::value).toList();
        List<Object[]> rows = reports.findReportIdPairsBySessionIdIn(ids);
        Map<SessionId, ReportId> out = new LinkedHashMap<>();
        for (Object[] row : rows) {
            out.put(new SessionId((UUID) row[0]), new ReportId((UUID) row[1]));
        }
        return out;
    }
}
