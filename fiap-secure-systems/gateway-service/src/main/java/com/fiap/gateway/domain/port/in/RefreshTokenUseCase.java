package com.fiap.gateway.domain.port.in;

public interface RefreshTokenUseCase {
    LoginUseCase.TokenPair refresh(String refreshToken);
}
