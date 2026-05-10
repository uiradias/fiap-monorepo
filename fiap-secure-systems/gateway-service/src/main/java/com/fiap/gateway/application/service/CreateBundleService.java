package com.fiap.gateway.application.service;

import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.CreateBundleUseCase;
import com.fiap.gateway.domain.port.out.AssetBundleRepositoryPort;

@Service
public class CreateBundleService implements CreateBundleUseCase {

    private final AssetBundleRepositoryPort bundles;
    private final Clock clock;

    public CreateBundleService(AssetBundleRepositoryPort bundles, Clock clock) {
        this.bundles = bundles;
        this.clock = clock;
    }

    @Override
    @Transactional
    public AssetBundle create(UserId owner) {
        AssetBundle b = AssetBundle.newBundle(new BundleId(UUID.randomUUID()), owner, clock.now());
        return bundles.insert(b);
    }
}
