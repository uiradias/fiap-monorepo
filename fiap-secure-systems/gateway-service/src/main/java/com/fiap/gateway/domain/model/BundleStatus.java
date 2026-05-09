package com.fiap.gateway.domain.model;

public enum BundleStatus {
    INITIATED, UPLOADING, UPLOADED, FAILED;

    public boolean isTerminal() {
        return this == FAILED;
    }

    public boolean canAcceptAssets() {
        return this == INITIATED || this == UPLOADING;
    }

    public boolean canBeFinalized() {
        return this == UPLOADING;
    }
}
