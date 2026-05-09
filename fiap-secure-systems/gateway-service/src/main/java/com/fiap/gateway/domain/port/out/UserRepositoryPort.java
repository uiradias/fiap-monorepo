package com.fiap.gateway.domain.port.out;

import com.fiap.gateway.domain.model.*;

import java.util.Optional;

public interface UserRepositoryPort {
    User insertOrThrow(User user);              // throws DuplicateEmailException on email collision
    Optional<User> findByEmail(Email email);
    Optional<User> findById(UserId id);
}
