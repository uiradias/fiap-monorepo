package com.fiap.orchestrator.domain.model;

import java.util.Optional;

public record SessionListItem(Session session, Optional<ReportId> reportId) {}
