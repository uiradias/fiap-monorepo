package com.fiap.orchestrator.domain.exception;

import com.fiap.orchestrator.domain.model.SessionId;

/**
 * Permanent error: the referenced session does not exist in the orchestrator's store. Treated as a
 * poison pill by message consumers — the message is forwarded to its DLQ rather than left for
 * visibility-timeout redelivery (which would never succeed).
 */
public class UnknownSessionException extends RuntimeException {
    private final SessionId sessionId;

    public UnknownSessionException(SessionId sessionId) {
        super("unknown session: " + sessionId);
        this.sessionId = sessionId;
    }

    public SessionId sessionId() {
        return sessionId;
    }
}
