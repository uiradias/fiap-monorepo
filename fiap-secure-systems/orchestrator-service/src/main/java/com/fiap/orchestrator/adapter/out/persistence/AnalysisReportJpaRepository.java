package com.fiap.orchestrator.adapter.out.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface AnalysisReportJpaRepository extends JpaRepository<AnalysisReportEntity, UUID> {
    Optional<AnalysisReportEntity> findBySessionId(UUID sessionId);
}
