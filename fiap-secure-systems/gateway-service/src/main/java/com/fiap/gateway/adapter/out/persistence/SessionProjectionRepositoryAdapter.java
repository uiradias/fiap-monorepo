package com.fiap.gateway.adapter.out.persistence;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.out.SessionProjectionRepositoryPort;

@Repository
public class SessionProjectionRepositoryAdapter implements SessionProjectionRepositoryPort {

    private final SessionProjectionJpaRepository repo;

    public SessionProjectionRepositoryAdapter(SessionProjectionJpaRepository repo) {
        this.repo = repo;
    }

    @Override
    @Transactional
    public SessionProjection upsert(SessionProjection p) {
        SessionProjectionEntity e = new SessionProjectionEntity();
        e.id = p.id().value();
        e.userId = p.userId().value();
        e.state = p.state().name();
        e.lastEventAt = p.lastEventAt();
        e.failureReason = p.failureReason();
        e.reportId = p.reportIdOpt().map(ReportId::value).orElse(null);
        repo.save(e);
        return p;
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<SessionProjection> findById(SessionId id) {
        return repo.findById(id.value()).map(this::toDomain);
    }

    @Override
    @Transactional(readOnly = true)
    public List<SessionSummary> listSummariesByUser(UserId userId, int limit) {
        return repo.findSummaryRowsByUserId(userId.value(), PageRequest.of(0, limit)).stream()
                .map(
                        row -> {
                            SessionProjectionEntity sp = (SessionProjectionEntity) row[0];
                            int assetCount = row[1] instanceof Number n ? n.intValue() : 0;
                            Instant createdAt = row[2] instanceof Instant t ? t : sp.lastEventAt;
                            return new SessionSummary(
                                    new SessionId(sp.id),
                                    new UserId(sp.userId),
                                    SessionState.valueOf(sp.state),
                                    assetCount,
                                    sp.failureReason,
                                    createdAt,
                                    sp.lastEventAt,
                                    Optional.ofNullable(sp.reportId).map(ReportId::new));
                        })
                .toList();
    }

    private SessionProjection toDomain(SessionProjectionEntity e) {
        return new SessionProjection(
                new SessionId(e.id),
                new UserId(e.userId),
                SessionState.valueOf(e.state),
                e.lastEventAt,
                e.failureReason,
                e.reportId == null ? null : new ReportId(e.reportId));
    }
}
