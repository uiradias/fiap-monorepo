package com.fiap.gateway.adapter.out.persistence;

import java.util.Optional;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.exception.DuplicateEmailException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.out.UserRepositoryPort;

@Repository
public class UserRepositoryAdapter implements UserRepositoryPort {

    private final UserJpaRepository repo;

    public UserRepositoryAdapter(UserJpaRepository repo) {
        this.repo = repo;
    }

    @Override
    @Transactional
    public User insertOrThrow(User user) {
        UserEntity e = new UserEntity();
        e.id = user.id().value();
        e.email = user.email().value();
        e.passwordHash = user.passwordHash().value();
        e.displayName = user.displayName();
        e.createdAt = user.createdAt();
        e.updatedAt = user.updatedAt();
        try {
            repo.saveAndFlush(e);
        } catch (DataIntegrityViolationException dive) {
            throw new DuplicateEmailException(user.email());
        }
        return user;
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<User> findByEmail(Email email) {
        return repo.findByEmail(email.value()).map(this::toDomain);
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<User> findById(UserId id) {
        return repo.findById(id.value()).map(this::toDomain);
    }

    private User toDomain(UserEntity e) {
        return new User(
                new UserId(e.id),
                Email.of(e.email),
                new PasswordHash(e.passwordHash),
                e.displayName,
                e.createdAt,
                e.updatedAt);
    }
}
