package com.fiap.orchestrator.adapter.out.persistence;

import java.util.Collection;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface AnalysisReportJpaRepository extends JpaRepository<AnalysisReportEntity, UUID> {
    Optional<AnalysisReportEntity> findBySessionId(UUID sessionId);

    @Query("select r.sessionId, r.id from AnalysisReportEntity r where r.sessionId in :ids")
    List<Object[]> findReportIdPairsBySessionIdIn(@Param("ids") Collection<UUID> ids);
}
