package com.fiap.orchestrator.infrastructure.schema;

import org.junit.jupiter.api.Test;

import java.io.File;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ContractValidatorTest {

    private static final File CONTRACTS_DIR =
            new File("src/test/resources/contracts").getAbsoluteFile();

    @Test
    void validates_a_well_formed_analysis_job() {
        ContractValidator v = new ContractValidator(CONTRACTS_DIR);
        Map<String, Object> body = Map.of(
                "schemaVersion", 1,
                "jobId", "00000000-0000-4000-8000-000000000001",
                "sessionId", "00000000-0000-4000-8000-000000000002",
                "userId", "00000000-0000-4000-8000-000000000003",
                "assets", List.of(Map.of(
                        "assetId", "00000000-0000-4000-8000-000000000004",
                        "s3Key", "sessions/x/file.png",
                        "contentType", "image/png",
                        "filename", "file.png",
                        "sizeBytes", 1024
                )),
                "promptVersion", "v1",
                "submittedAt", "2026-01-01T00:00:00Z"
        );
        v.validateAnalysisJob(body);
    }

    @Test
    void rejects_a_malformed_analysis_job_with_a_useful_message() {
        ContractValidator v = new ContractValidator(CONTRACTS_DIR);
        Map<String, Object> body = Map.of(
                "schemaVersion", 1,
                "jobId", "not-a-uuid",
                "sessionId", "00000000-0000-4000-8000-000000000002",
                "userId", "00000000-0000-4000-8000-000000000003",
                "assets", List.of(),
                "promptVersion", "v1",
                "submittedAt", "2026-01-01T00:00:00Z"
        );
        assertThatThrownBy(() -> v.validateAnalysisJob(body))
                .isInstanceOf(ContractValidationException.class)
                .hasMessageContaining("jobId");
    }

    @Test
    void validates_a_session_event() {
        ContractValidator v = new ContractValidator(CONTRACTS_DIR);
        Map<String, Object> body = Map.of(
                "schemaVersion", 1,
                "eventId", "00000000-0000-4000-8000-000000000005",
                "sessionId", "00000000-0000-4000-8000-000000000002",
                "userId", "00000000-0000-4000-8000-000000000003",
                "fromState", "ASSETS_UPLOADED",
                "toState", "QUEUED_FOR_ANALYSIS",
                "payload", Map.of(),
                "occurredAt", "2026-01-01T00:00:00Z"
        );
        v.validateSessionEvent(body);
    }

    @Test
    void validates_a_started_analysis_result_without_result_block() {
        ContractValidator v = new ContractValidator(CONTRACTS_DIR);
        Map<String, Object> body = Map.of(
                "schemaVersion", 1,
                "jobId", "00000000-0000-4000-8000-000000000001",
                "sessionId", "00000000-0000-4000-8000-000000000002",
                "status", "STARTED",
                "completedAt", "2026-01-01T00:00:00Z"
        );
        v.validateAnalysisResult(body);
    }

    @Test
    void rejects_succeeded_without_result_block() {
        ContractValidator v = new ContractValidator(CONTRACTS_DIR);
        Map<String, Object> body = Map.of(
                "schemaVersion", 1,
                "jobId", "00000000-0000-4000-8000-000000000001",
                "sessionId", "00000000-0000-4000-8000-000000000002",
                "status", "SUCCEEDED",
                "completedAt", "2026-01-01T00:00:00Z"
        );
        assertThatThrownBy(() -> v.validateAnalysisResult(body))
                .isInstanceOf(ContractValidationException.class);
    }

    @Test
    void misconfigured_contracts_dir_fails_fast() {
        File missing = new File("/tmp/this-path-does-not-exist-xyz");
        assertThatThrownBy(() -> new ContractValidator(missing))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("contracts");
    }
}
