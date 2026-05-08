package com.fiap.orchestrator.domain.port.out;

import com.fiap.orchestrator.domain.model.AnalysisStatus;
import com.fiap.orchestrator.domain.model.JobId;

import java.time.Instant;

public interface ProcessedResultsPort {
    boolean recordIfAbsent(JobId jobId, AnalysisStatus status, Instant processedAt);
}
