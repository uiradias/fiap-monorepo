package com.fiap.gateway.application.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.exception.BundleNotFoundException;
import com.fiap.gateway.domain.exception.ForbiddenException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.GetBundleUseCase;
import com.fiap.gateway.domain.port.out.*;

@Service
public class GetBundleService implements GetBundleUseCase {

    private final AssetBundleRepositoryPort bundles;
    private final AssetRepositoryPort assets;

    public GetBundleService(AssetBundleRepositoryPort bundles, AssetRepositoryPort assets) {
        this.bundles = bundles;
        this.assets = assets;
    }

    @Override
    @Transactional(readOnly = true)
    public View get(BundleId bundleId, UserId requester) {
        AssetBundle b =
                bundles.findById(bundleId).orElseThrow(() -> new BundleNotFoundException(bundleId));
        if (!b.userId().equals(requester)) throw new ForbiddenException("bundle " + bundleId);
        return new View(b, assets.findByBundleId(bundleId));
    }
}
