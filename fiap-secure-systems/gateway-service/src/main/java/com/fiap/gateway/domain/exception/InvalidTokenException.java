package com.fiap.gateway.domain.exception;

public class InvalidTokenException extends RuntimeException {
    public InvalidTokenException(String reason) {
        super(reason);
    }
}
