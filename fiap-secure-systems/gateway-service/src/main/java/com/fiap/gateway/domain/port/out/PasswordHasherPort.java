package com.fiap.gateway.domain.port.out;

import com.fiap.gateway.domain.model.PasswordHash;

public interface PasswordHasherPort {
    PasswordHash hash(String plaintext);

    boolean matches(String plaintext, PasswordHash hash);
}
