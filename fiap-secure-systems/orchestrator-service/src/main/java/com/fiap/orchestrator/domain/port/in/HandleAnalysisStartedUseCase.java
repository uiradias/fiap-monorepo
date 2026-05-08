package com.fiap.orchestrator.domain.port.in;

import com.fiap.orchestrator.domain.model.JobId;
import com.fiap.orchestrator.domain.model.SessionId;

public interface HandleAnalysisStartedUseCase {
    void onStarted(JobId jobId, SessionId sessionId);
}
