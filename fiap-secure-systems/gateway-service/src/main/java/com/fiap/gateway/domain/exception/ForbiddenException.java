package com.fiap.gateway.domain.exception;

public class ForbiddenException extends RuntimeException {
    public ForbiddenException(String resource) {
        super("forbidden: " + resource);
    }
}
