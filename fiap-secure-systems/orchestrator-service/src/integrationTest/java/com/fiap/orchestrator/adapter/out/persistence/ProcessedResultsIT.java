package com.fiap.orchestrator.adapter.out.persistence;

import com.fiap.orchestrator.PostgresTestcontainersBase;
import com.fiap.orchestrator.domain.model.AnalysisStatus;
import com.fiap.orchestrator.domain.model.JobId;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import java.time.Instant;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class ProcessedResultsIT extends PostgresTestcontainersBase {

    @Autowired ProcessedResultsAdapter results;

    @Test
    void recordIfAbsent_returns_true_first_time_false_after() {
        JobId job = new JobId(UUID.randomUUID());
        assertThat(results.recordIfAbsent(job, AnalysisStatus.STARTED, Instant.now())).isTrue();
        assertThat(results.recordIfAbsent(job, AnalysisStatus.STARTED, Instant.now())).isFalse();
        assertThat(results.recordIfAbsent(job, AnalysisStatus.SUCCEEDED, Instant.now())).isTrue();
        assertThat(results.recordIfAbsent(job, AnalysisStatus.SUCCEEDED, Instant.now())).isFalse();
    }
}
