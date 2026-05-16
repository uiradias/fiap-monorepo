package com.fiap.gateway.domain.port.in;

import java.util.List;

import com.fiap.gateway.domain.model.SessionSummary;
import com.fiap.gateway.domain.model.UserId;

public interface ListUserSessionsUseCase {

    List<SessionSummary> list(UserId requester, int limit);
}
