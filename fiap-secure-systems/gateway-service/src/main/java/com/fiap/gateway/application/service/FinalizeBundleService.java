package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.exception.BundleNotFoundException;
import com.fiap.gateway.domain.exception.ForbiddenException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.FinalizeBundleUseCase;
import com.fiap.gateway.domain.port.out.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class FinalizeBundleService implements FinalizeBundleUseCase {

    private final AssetBundleRepositoryPort bundles;
    private final AssetRepositoryPort assets;
    private final OrchestratorClientPort orchestrator;
    private final SessionProjectionRepositoryPort projections;
    private final Clock clock;

    public FinalizeBundleService(AssetBundleRepositoryPort bundles, AssetRepositoryPort assets,
                                 OrchestratorClientPort orchestrator,
                                 SessionProjectionRepositoryPort projections, Clock clock) {
        this.bundles = bundles;
        this.assets = assets;
        this.orchestrator = orchestrator;
        this.projections = projections;
        this.clock = clock;
    }

    @Override
    @Transactional
    public Result finalize(BundleId bundleId, UserId requester) {
        AssetBundle bundle = bundles.findById(bundleId).orElseThrow(() -> new BundleNotFoundException(bundleId));
        if (!bundle.userId().equals(requester)) throw new ForbiddenException("bundle " + bundleId);

        AssetBundle finalized = bundle.finalize(clock.now());
        bundles.save(finalized);

        SessionId sessionId = new SessionId(UUID.fromString(bundleId.value().toString()));   // bundleId == sessionId
        List<String> keys = assets.findByBundleId(bundleId).stream().map(Asset::s3Key).toList();

        // Pre-seed the projection so the WS path can find it before the first SNS event arrives.
        projections.upsert(SessionProjection.initial(sessionId, requester, SessionState.ASSETS_UPLOADED, clock.now()));

        orchestrator.createSession(sessionId, requester, finalized.assetCount(), keys);
        return new Result(sessionId, SessionState.ASSETS_UPLOADED);
    }
}
