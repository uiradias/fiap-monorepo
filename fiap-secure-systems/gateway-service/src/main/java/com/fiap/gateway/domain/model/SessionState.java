package com.fiap.gateway.domain.model;

public enum SessionState {
    CREATED,
    ASSETS_UPLOADED,
    QUEUED_FOR_ANALYSIS,
    ANALYZING,
    ANALYSIS_COMPLETED,
    REPORT_READY,
    FAILED,
    CANCELED;

    public boolean isTerminal() {
        return this == REPORT_READY || this == FAILED || this == CANCELED;
    }

    public static SessionState fromString(String s) {
        return SessionState.valueOf(s);
    }
}
