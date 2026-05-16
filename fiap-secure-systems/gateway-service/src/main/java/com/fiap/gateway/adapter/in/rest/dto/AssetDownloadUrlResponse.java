package com.fiap.gateway.adapter.in.rest.dto;

import com.fiap.gateway.domain.port.in.IssueAssetDownloadUrlUseCase;

public record AssetDownloadUrlResponse(String url, long expiresInSeconds) {
    public static AssetDownloadUrlResponse of(IssueAssetDownloadUrlUseCase.DownloadUrl u) {
        return new AssetDownloadUrlResponse(u.url().toString(), u.expiresInSeconds());
    }
}
