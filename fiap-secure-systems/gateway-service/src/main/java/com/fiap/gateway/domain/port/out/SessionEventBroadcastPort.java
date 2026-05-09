package com.fiap.gateway.domain.port.out;

import com.fiap.gateway.domain.model.SessionEventLogEntry;

public interface SessionEventBroadcastPort {
    /** Fan-out to any in-process WebSocket subscribers for the event's session id. */
    void broadcast(SessionEventLogEntry event);
}
