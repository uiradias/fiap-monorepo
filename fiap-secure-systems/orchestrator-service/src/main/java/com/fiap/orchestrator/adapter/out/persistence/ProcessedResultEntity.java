package com.fiap.orchestrator.adapter.out.persistence;

import java.time.Instant;

import jakarta.persistence.*;

@Entity
@Table(name = "processed_results")
public class ProcessedResultEntity {

    @EmbeddedId private ProcessedResultId id;

    @Column(name = "processed_at", nullable = false)
    private Instant processedAt;

    public ProcessedResultEntity() {}

    public ProcessedResultEntity(ProcessedResultId id, Instant processedAt) {
        this.id = id;
        this.processedAt = processedAt;
    }

    public ProcessedResultId getId() {
        return id;
    }
}
