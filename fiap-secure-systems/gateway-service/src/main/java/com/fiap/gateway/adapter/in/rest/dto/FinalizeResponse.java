package com.fiap.gateway.adapter.in.rest.dto;

import java.util.UUID;

public record FinalizeResponse(UUID sessionId, String state) {}
