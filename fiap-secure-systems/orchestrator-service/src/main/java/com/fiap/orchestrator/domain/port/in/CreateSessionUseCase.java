package com.fiap.orchestrator.domain.port.in;

import java.util.List;

import com.fiap.orchestrator.domain.model.AssetRef;
import com.fiap.orchestrator.domain.model.Session;
import com.fiap.orchestrator.domain.model.SessionId;
import com.fiap.orchestrator.domain.model.UserId;

public interface CreateSessionUseCase {
    Session create(SessionId sessionId, UserId userId, List<AssetRef> assets);
}
