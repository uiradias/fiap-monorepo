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

    /** Canonical session from orchestrator; {@code null} if not found (HTTP 404). */
    SessionProjection getSession(SessionId sessionId);

    List<SessionSummary> listSessions(UserId userId, int limit);

    AnalysisReport getReport(SessionId sessionId);

    void cancelSession(SessionId sessionId);
}
