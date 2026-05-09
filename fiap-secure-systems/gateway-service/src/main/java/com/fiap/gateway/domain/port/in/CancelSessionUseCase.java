package com.fiap.gateway.domain.port.in;

import com.fiap.gateway.domain.model.*;

public interface CancelSessionUseCase {
    void cancel(SessionId sessionId, UserId requester);
}
