package com.fiap.orchestrator.application.service;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.in.ListUserSessionsUseCase;
import com.fiap.orchestrator.domain.port.out.ReportRepositoryPort;
import com.fiap.orchestrator.domain.port.out.SessionRepositoryPort;

@Service
@Transactional(readOnly = true)
public class ListUserSessionsService implements ListUserSessionsUseCase {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 100;

    private final SessionRepositoryPort sessions;
    private final ReportRepositoryPort reports;

    public ListUserSessionsService(SessionRepositoryPort sessions, ReportRepositoryPort reports) {
        this.sessions = sessions;
        this.reports = reports;
    }

    @Override
    public List<SessionListItem> list(UserId userId, int limit) {
        int cap = limit < 1 ? DEFAULT_LIMIT : Math.min(limit, MAX_LIMIT);
        List<Session> rows = sessions.listByUserId(userId, cap);
        if (rows.isEmpty()) {
            return List.of();
        }
        List<SessionId> ids = rows.stream().map(Session::id).toList();
        Map<SessionId, ReportId> reportBySession = reports.findReportIdsBySessionIds(ids);
        return rows.stream()
                .map(s -> new SessionListItem(s, Optional.ofNullable(reportBySession.get(s.id()))))
                .toList();
    }
}
