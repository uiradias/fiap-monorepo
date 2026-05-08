package com.fiap.orchestrator.domain.port.in;

import com.fiap.orchestrator.domain.model.AnalysisOutcome;

public interface HandleAnalysisFailedUseCase {
    void onFailed(AnalysisOutcome outcome);
}
