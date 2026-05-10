package com.fiap.gateway.domain.port.out;

import java.util.Optional;

import com.fiap.gateway.domain.model.*;

public interface UserRepositoryPort {
    User insertOrThrow(User user); // throws DuplicateEmailException on email collision

    Optional<User> findByEmail(Email email);

    Optional<User> findById(UserId id);
}
