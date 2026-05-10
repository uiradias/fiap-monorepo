package com.fiap.gateway.domain.port.out;

import java.util.List;

import com.fiap.gateway.domain.model.*;

public interface OrchestratorClientPort {
    /**
     * Posts to orchestrator's POST /internal/sessions. The orchestrator's request body uses an
     * {@code assets} field containing one {@code AssetRequest} per asset (assetId, s3Key,
     * contentType, filename, sizeBytes) — pass the full {@link Asset} records and let the adapter
     * serialize the inner shape.
     */
    void createSession(SessionId sessionId, UserId userId, int assetCount, List<Asset> assets);

    SessionProjection getSession(
            SessionId sessionId); // not currently used by gateway services, but useful for repair

    // tooling

    AnalysisReport getReport(SessionId sessionId);

    void cancelSession(SessionId sessionId);
}
