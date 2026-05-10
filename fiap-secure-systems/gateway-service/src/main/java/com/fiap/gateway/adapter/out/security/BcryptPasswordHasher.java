package com.fiap.gateway.adapter.out.security;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

import com.fiap.gateway.domain.model.PasswordHash;
import com.fiap.gateway.domain.port.out.PasswordHasherPort;

public class BcryptPasswordHasher implements PasswordHasherPort {

    private static final int COST = 12;
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder(COST);

    @Override
    public PasswordHash hash(String plaintext) {
        return new PasswordHash(encoder.encode(plaintext));
    }

    @Override
    public boolean matches(String plaintext, PasswordHash hash) {
        if (plaintext == null || plaintext.isEmpty()) return false;
        return encoder.matches(plaintext, hash.value());
    }
}
