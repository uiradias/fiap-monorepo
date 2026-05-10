package com.fiap.orchestrator.domain.port.out;

import java.time.Instant;

import com.fiap.orchestrator.domain.model.AnalysisStatus;
import com.fiap.orchestrator.domain.model.JobId;

public interface ProcessedResultsPort {
    boolean recordIfAbsent(JobId jobId, AnalysisStatus status, Instant processedAt);
}
