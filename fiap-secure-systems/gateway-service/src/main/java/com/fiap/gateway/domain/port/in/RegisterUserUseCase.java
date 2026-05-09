package com.fiap.gateway.domain.port.in;

import com.fiap.gateway.domain.model.*;

public interface RegisterUserUseCase {
    User register(Email email, String plaintextPassword, String displayName);
}
