package com.fiap.orchestrator.domain.model;

import java.util.EnumSet;
import java.util.Set;

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

    public static Set<SessionState> nonTerminal() {
        return EnumSet.complementOf(EnumSet.of(REPORT_READY, FAILED, CANCELED));
    }
}
