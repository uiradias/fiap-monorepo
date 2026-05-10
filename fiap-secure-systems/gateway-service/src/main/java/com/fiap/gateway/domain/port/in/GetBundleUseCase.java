package com.fiap.gateway.domain.port.in;

import java.util.List;

import com.fiap.gateway.domain.model.*;

public interface GetBundleUseCase {
    View get(BundleId bundleId, UserId requester);

    record View(AssetBundle bundle, List<Asset> assets) {}
}
