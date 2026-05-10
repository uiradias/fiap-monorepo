package com.fiap.gateway.domain.exception;

import com.fiap.gateway.domain.model.BundleId;

public class BundleNotFoundException extends RuntimeException {
    public BundleNotFoundException(BundleId id) {
        super("bundle not found: " + id);
    }
}
