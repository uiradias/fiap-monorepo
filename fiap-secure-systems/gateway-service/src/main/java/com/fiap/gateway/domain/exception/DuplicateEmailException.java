package com.fiap.gateway.domain.exception;

import com.fiap.gateway.domain.model.Email;

public class DuplicateEmailException extends RuntimeException {
    public DuplicateEmailException(Email email) { super("email already registered: " + email); }
}
