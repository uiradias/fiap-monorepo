package com.fiap.orchestrator.domain.port.in;

import java.util.List;

import com.fiap.orchestrator.domain.model.SessionListItem;
import com.fiap.orchestrator.domain.model.UserId;

public interface ListUserSessionsUseCase {

    List<SessionListItem> list(UserId userId, int limit);
}
