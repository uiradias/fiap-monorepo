package com.fiap.gateway.adapter.out.persistence;

import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

public interface SessionProjectionJpaRepository
        extends JpaRepository<SessionProjectionEntity, UUID> {}
