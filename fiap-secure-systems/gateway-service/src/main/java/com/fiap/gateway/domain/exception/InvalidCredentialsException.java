package com.fiap.gateway.domain.exception;

public class InvalidCredentialsException extends RuntimeException {
    public InvalidCredentialsException() { super("invalid credentials"); }
}
