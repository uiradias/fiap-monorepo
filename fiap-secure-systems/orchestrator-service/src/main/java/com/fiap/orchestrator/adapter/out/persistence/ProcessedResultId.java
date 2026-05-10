package com.fiap.orchestrator.adapter.out.persistence;

import java.io.Serializable;
import java.util.Objects;
import java.util.UUID;

import com.fiap.orchestrator.domain.model.AnalysisStatus;

import jakarta.persistence.Embeddable;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;

@Embeddable
public class ProcessedResultId implements Serializable {
    private UUID jobId;

    @Enumerated(EnumType.STRING)
    private AnalysisStatus status;

    public ProcessedResultId() {}

    public ProcessedResultId(UUID jobId, AnalysisStatus status) {
        this.jobId = jobId;
        this.status = status;
    }

    public UUID getJobId() {
        return jobId;
    }

    public AnalysisStatus getStatus() {
        return status;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof ProcessedResultId other)) return false;
        return Objects.equals(jobId, other.jobId) && status == other.status;
    }

    @Override
    public int hashCode() {
        return Objects.hash(jobId, status);
    }
}
