package com.fiap.gateway.adapter.in.rest.dto;

public record TokenPairResponse(String accessToken, String refreshToken, long expiresIn) {}
