package com.fiap.gateway.domain.exception;

import com.fiap.gateway.domain.model.SessionId;
import com.fiap.gateway.domain.model.SessionState;

public class ReportNotReadyException extends RuntimeException {
    public ReportNotReadyException(SessionId id, SessionState current) {
        super("session " + id + " is " + current + "; report not yet available");
    }
}
