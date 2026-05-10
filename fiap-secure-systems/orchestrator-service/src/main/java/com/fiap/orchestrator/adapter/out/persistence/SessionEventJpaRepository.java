package com.fiap.orchestrator.adapter.out.persistence;

import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

public interface SessionEventJpaRepository extends JpaRepository<SessionEventEntity, UUID> {}
