package com.fiap.orchestrator.adapter.out.persistence;

import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface OutboxJpaRepository extends JpaRepository<OutboxMessageEntity, UUID> {
    @Query(
            """
            SELECT m FROM OutboxMessageEntity m
            WHERE m.publishedAt IS NULL
            ORDER BY m.createdAt ASC
            """)
    List<OutboxMessageEntity> findUnpublished(Pageable pageable);
}
