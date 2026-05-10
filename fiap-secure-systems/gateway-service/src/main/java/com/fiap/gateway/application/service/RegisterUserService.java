package com.fiap.gateway.application.service;

import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.RegisterUserUseCase;
import com.fiap.gateway.domain.port.out.PasswordHasherPort;
import com.fiap.gateway.domain.port.out.UserRepositoryPort;

@Service
public class RegisterUserService implements RegisterUserUseCase {

    private final UserRepositoryPort users;
    private final PasswordHasherPort hasher;
    private final Clock clock;

    public RegisterUserService(UserRepositoryPort users, PasswordHasherPort hasher, Clock clock) {
        this.users = users;
        this.hasher = hasher;
        this.clock = clock;
    }

    @Override
    @Transactional
    public User register(Email email, String plaintextPassword, String displayName) {
        if (plaintextPassword == null || plaintextPassword.length() < 8) {
            throw new IllegalArgumentException("password must be at least 8 characters");
        }
        User u =
                User.newUser(
                        new UserId(UUID.randomUUID()),
                        email,
                        hasher.hash(plaintextPassword),
                        displayName,
                        clock.now());
        return users.insertOrThrow(u);
    }
}
