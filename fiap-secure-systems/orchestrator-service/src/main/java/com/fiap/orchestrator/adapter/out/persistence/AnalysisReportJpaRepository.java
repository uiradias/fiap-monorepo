package com.fiap.orchestrator.adapter.out.persistence;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AnalysisReportJpaRepository extends JpaRepository<AnalysisReportEntity, UUID> {
    Optional<AnalysisReportEntity> findBySessionId(UUID sessionId);
}
