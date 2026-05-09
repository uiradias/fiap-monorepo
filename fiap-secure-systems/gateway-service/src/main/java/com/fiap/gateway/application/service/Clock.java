package com.fiap.gateway.application.service;

import java.time.Instant;

@FunctionalInterface
public interface Clock {
    Instant now();
}
