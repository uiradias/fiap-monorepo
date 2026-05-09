package com.fiap.orchestrator.adapter.out.persistence;

import com.fiap.orchestrator.domain.model.AnalysisReport;
import com.fiap.orchestrator.domain.model.SessionId;
import com.fiap.orchestrator.domain.port.out.ReportRepositoryPort;
import org.springframework.stereotype.Repository;

import java.util.Optional;

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
}
