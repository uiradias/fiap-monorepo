package com.fiap.gateway.domain.port.in;

import com.fiap.gateway.domain.model.*;

public interface GetReportUseCase {
    AnalysisReport get(SessionId sessionId, UserId requester);
}
