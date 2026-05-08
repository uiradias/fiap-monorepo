package com.fiap.orchestrator.domain.port.out;

import com.fiap.orchestrator.domain.model.SessionEvent;
import com.fiap.orchestrator.domain.model.UserId;

public interface SessionEventPublisherPort {
    void publish(SessionEvent event, UserId userId);
}
