package com.fiap.orchestrator.application.service;

import java.time.Instant;

@FunctionalInterface
public interface Clock {
    Instant now();
}
