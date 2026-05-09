package com.fiap.gateway.domain.port.out;

import com.fiap.gateway.domain.model.*;

import java.util.List;

public interface OrchestratorClientPort {
    void createSession(SessionId sessionId, UserId userId, int assetCount, List<String> assetKeys);
    SessionProjection getSession(SessionId sessionId);     // not currently used by gateway services, but useful for repair tooling
    AnalysisReport getReport(SessionId sessionId);
    void cancelSession(SessionId sessionId);
}
