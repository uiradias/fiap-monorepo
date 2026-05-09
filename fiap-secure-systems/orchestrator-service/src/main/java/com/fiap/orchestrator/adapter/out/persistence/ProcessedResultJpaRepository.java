package com.fiap.orchestrator.adapter.out.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ProcessedResultJpaRepository
        extends JpaRepository<ProcessedResultEntity, ProcessedResultId> {}
