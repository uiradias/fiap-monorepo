package com.fiap.orchestrator.adapter.out.persistence;

import com.fiap.orchestrator.domain.model.AnalysisStatus;
import com.fiap.orchestrator.domain.model.JobId;
import com.fiap.orchestrator.domain.port.out.ProcessedResultsPort;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;

@Repository
public class ProcessedResultsAdapter implements ProcessedResultsPort {

    private final ProcessedResultJpaRepository repo;

    public ProcessedResultsAdapter(ProcessedResultJpaRepository repo) {
        this.repo = repo;
    }

    @Override
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public boolean recordIfAbsent(JobId jobId, AnalysisStatus status, Instant processedAt) {
        ProcessedResultId id = new ProcessedResultId(jobId.value(), status);
        if (repo.existsById(id)) return false;
        try {
            repo.saveAndFlush(new ProcessedResultEntity(id, processedAt));
            return true;
        } catch (DataIntegrityViolationException dup) {
            return false;
        }
    }
}
