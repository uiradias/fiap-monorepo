package com.fiap.orchestrator.domain.port.out;

import com.fiap.orchestrator.domain.model.AnalysisJob;

public interface AnalysisJobPublisherPort {
    void publish(AnalysisJob job);
}
