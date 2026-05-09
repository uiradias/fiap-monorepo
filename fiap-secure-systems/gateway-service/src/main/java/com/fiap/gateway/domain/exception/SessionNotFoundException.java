package com.fiap.gateway.domain.exception;

import com.fiap.gateway.domain.model.SessionId;

public class SessionNotFoundException extends RuntimeException {
    public SessionNotFoundException(SessionId id) { super("session not found: " + id); }
}
