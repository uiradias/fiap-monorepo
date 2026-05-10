package com.fiap.orchestrator.adapter.in.rest.dto;

import java.util.List;
import java.util.UUID;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;

public record CreateSessionRequest(
        @NotNull UUID sessionId,
        @NotNull UUID userId,
        @NotNull @Min(1) @Max(20) Integer assetCount,
        @NotEmpty @Valid List<AssetRequest> assets) {
    public record AssetRequest(
            @NotNull UUID assetId,
            @NotBlank String s3Key,
            @NotBlank String contentType,
            @NotBlank String filename,
            @Min(1) long sizeBytes) {}
}
