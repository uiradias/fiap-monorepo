package com.fiap.orchestrator.adapter.out.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface SessionEventJpaRepository extends JpaRepository<SessionEventEntity, UUID> {}
