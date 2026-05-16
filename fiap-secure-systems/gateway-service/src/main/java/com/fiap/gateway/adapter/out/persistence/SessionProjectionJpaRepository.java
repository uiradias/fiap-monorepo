package com.fiap.gateway.adapter.out.persistence;

import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface SessionProjectionJpaRepository
        extends JpaRepository<SessionProjectionEntity, UUID> {

    @Query(
            """
            select sp, coalesce(ab.assetCount, 0), coalesce(ab.createdAt, sp.lastEventAt)
            from SessionProjectionEntity sp
            left join AssetBundleEntity ab on ab.id = sp.id
            where sp.userId = :userId
            order by sp.lastEventAt desc
            """)
    List<Object[]> findSummaryRowsByUserId(@Param("userId") UUID userId, Pageable pageable);
}
