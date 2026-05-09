package com.fiap.gateway.domain.port.in;

public interface LogoutUseCase {
    void logout(String refreshToken);
}
