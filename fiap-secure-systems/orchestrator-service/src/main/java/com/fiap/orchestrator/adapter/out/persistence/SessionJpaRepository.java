package com.fiap.orchestrator.adapter.out.persistence;

import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SessionJpaRepository extends JpaRepository<SessionEntity, UUID> {

    List<SessionEntity> findByUserIdOrderByCreatedAtDesc(UUID userId, Pageable pageable);
}
