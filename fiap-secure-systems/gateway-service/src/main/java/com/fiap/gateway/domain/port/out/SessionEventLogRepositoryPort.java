package com.fiap.gateway.domain.port.out;

import java.util.List;

import com.fiap.gateway.domain.model.*;

public interface SessionEventLogRepositoryPort {
    /**
     * Insert if absent (PK conflict on event_id => silent ack). Returns true if the row was newly
     * inserted.
     */
    boolean insertIfAbsent(SessionEventLogEntry entry);

    /** Last N events for a session, oldest first. */
    List<SessionEventLogEntry> tailForSession(SessionId sessionId, int limit);
}
