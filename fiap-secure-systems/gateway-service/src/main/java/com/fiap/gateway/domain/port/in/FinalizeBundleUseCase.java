package com.fiap.gateway.domain.port.in;

import com.fiap.gateway.domain.model.*;

public interface FinalizeBundleUseCase {
    /** Returns the sessionId (== bundleId) and the orchestrator-reported state. */
    Result finalize(BundleId bundleId, UserId requester);
    record Result(SessionId sessionId, SessionState state) {}
}
