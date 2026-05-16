package com.fiap.gateway.application.service;

import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fiap.gateway.domain.model.SessionSummary;
import com.fiap.gateway.domain.model.UserId;
import com.fiap.gateway.domain.port.in.ListUserSessionsUseCase;
import com.fiap.gateway.domain.port.out.SessionProjectionRepositoryPort;

@Service
public class ListUserSessionsService implements ListUserSessionsUseCase {

    private static final int DEFAULT_LIMIT = 50;
    private static final int MAX_LIMIT = 100;

    private final SessionProjectionRepositoryPort projections;

    public ListUserSessionsService(SessionProjectionRepositoryPort projections) {
        this.projections = projections;
    }

    @Override
    @Transactional(readOnly = true)
    public List<SessionSummary> list(UserId requester, int limit) {
        int cap = limit < 1 ? DEFAULT_LIMIT : Math.min(limit, MAX_LIMIT);
        return projections.listSummariesByUser(requester, cap);
    }
}
