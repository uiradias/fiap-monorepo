package com.fiap.gateway.application.service;

import com.fiap.gateway.domain.exception.ForbiddenException;
import com.fiap.gateway.domain.exception.SessionNotFoundException;
import com.fiap.gateway.domain.model.*;
import com.fiap.gateway.domain.port.in.GetSessionUseCase;
import com.fiap.gateway.domain.port.out.SessionProjectionRepositoryPort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class GetSessionService implements GetSessionUseCase {

    private final SessionProjectionRepositoryPort projections;

    public GetSessionService(SessionProjectionRepositoryPort projections) {
        this.projections = projections;
    }

    @Override
    @Transactional(readOnly = true)
    public SessionProjection get(SessionId sessionId, UserId requester) {
        SessionProjection p = projections.findById(sessionId)
                .orElseThrow(() -> new SessionNotFoundException(sessionId));
        if (!p.userId().equals(requester)) throw new ForbiddenException("session " + sessionId);
        return p;
    }
}
