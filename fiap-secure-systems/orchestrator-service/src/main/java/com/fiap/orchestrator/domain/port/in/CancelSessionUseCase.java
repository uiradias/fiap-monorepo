package com.fiap.orchestrator.domain.port.in;

import com.fiap.orchestrator.domain.model.SessionId;

public interface CancelSessionUseCase {
    void cancel(SessionId sessionId);
}
