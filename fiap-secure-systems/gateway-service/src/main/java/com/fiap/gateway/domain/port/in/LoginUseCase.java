package com.fiap.gateway.domain.port.in;

import com.fiap.gateway.domain.model.Email;

public interface LoginUseCase {
    TokenPair login(Email email, String plaintextPassword);

    record TokenPair(String accessToken, String refreshToken, long expiresInSeconds) {}
}
