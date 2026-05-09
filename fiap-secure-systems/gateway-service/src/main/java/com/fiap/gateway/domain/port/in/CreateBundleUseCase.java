package com.fiap.gateway.domain.port.in;

import com.fiap.gateway.domain.model.*;

public interface CreateBundleUseCase {
    AssetBundle create(UserId owner);
}
