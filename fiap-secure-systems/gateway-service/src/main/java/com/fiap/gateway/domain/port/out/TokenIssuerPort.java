package com.fiap.gateway.domain.port.out;

import com.fiap.gateway.domain.model.*;

public interface TokenIssuerPort {
    /** Returns a signed compact JWS string. */
    String issueAccessToken(UserId userId, java.time.Instant now);
    /** Returns a fresh opaque refresh token (unhashed plaintext for the client). */
    String generateRefreshTokenPlaintext();
    /** Hashes a refresh-token plaintext with SHA-256 (hex). */
    String hashRefreshToken(String plaintext);
    /** Verifies + parses; throws InvalidTokenException on failure. */
    UserId verifyAccessToken(String accessJws);
}
