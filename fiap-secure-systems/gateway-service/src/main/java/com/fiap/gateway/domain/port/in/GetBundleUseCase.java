package com.fiap.gateway.domain.port.in;

import com.fiap.gateway.domain.model.*;

import java.util.List;

public interface GetBundleUseCase {
    View get(BundleId bundleId, UserId requester);
    record View(AssetBundle bundle, List<Asset> assets) {}
}
