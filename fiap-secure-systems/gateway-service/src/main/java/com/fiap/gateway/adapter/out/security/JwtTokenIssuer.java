package com.fiap.gateway.adapter.out.security;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyFactory;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.Date;
import java.util.HexFormat;
import java.util.UUID;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.exceptions.JWTVerificationException;
import com.auth0.jwt.interfaces.DecodedJWT;
import com.fiap.gateway.domain.exception.InvalidTokenException;
import com.fiap.gateway.domain.model.UserId;
import com.fiap.gateway.domain.port.out.TokenIssuerPort;

public class JwtTokenIssuer implements TokenIssuerPort {

    private final RSAPrivateKey privateKey;
    private final RSAPublicKey publicKey;
    private final String issuer;
    private final Duration accessTtl;

    @SuppressWarnings("unused") // ttl recorded for completeness; actual refresh expiry comes from
    // RefreshToken.issue
    private final Duration refreshTtl;

    private final Algorithm algorithm;
    private final JWTVerifier verifier;
    private final SecureRandom random = new SecureRandom();

    public JwtTokenIssuer(
            String privateKeyPath,
            String publicKeyPath,
            String issuer,
            Duration accessTtl,
            Duration refreshTtl)
            throws IOException {
        this.privateKey = readPrivateKey(Path.of(privateKeyPath));
        this.publicKey = readPublicKey(Path.of(publicKeyPath));
        this.issuer = issuer;
        this.accessTtl = accessTtl;
        this.refreshTtl = refreshTtl;
        this.algorithm = Algorithm.RSA256(publicKey, privateKey);
        this.verifier = JWT.require(algorithm).withIssuer(issuer).build();
    }

    @Override
    public String issueAccessToken(UserId userId, Instant now) {
        return JWT.create()
                .withIssuer(issuer)
                .withSubject(userId.value().toString())
                .withIssuedAt(Date.from(now))
                .withExpiresAt(Date.from(now.plus(accessTtl)))
                .withJWTId(UUID.randomUUID().toString())
                .sign(algorithm);
    }

    @Override
    public UserId verifyAccessToken(String accessJws) {
        try {
            DecodedJWT decoded = verifier.verify(accessJws);
            return new UserId(UUID.fromString(decoded.getSubject()));
        } catch (JWTVerificationException | IllegalArgumentException e) {
            throw new InvalidTokenException("invalid access token: " + e.getMessage());
        }
    }

    @Override
    public String generateRefreshTokenPlaintext() {
        byte[] buf = new byte[48];
        random.nextBytes(buf);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(buf);
    }

    @Override
    public String hashRefreshToken(String plaintext) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(plaintext.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (Exception e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
    }

    // --- PEM parsing helpers ---

    private static RSAPrivateKey readPrivateKey(Path path) throws IOException {
        String pem =
                Files.readString(path)
                        .replace("-----BEGIN PRIVATE KEY-----", "")
                        .replace("-----END PRIVATE KEY-----", "")
                        .replaceAll("\\s+", "");
        byte[] der = Base64.getDecoder().decode(pem);
        try {
            return (RSAPrivateKey)
                    KeyFactory.getInstance("RSA").generatePrivate(new PKCS8EncodedKeySpec(der));
        } catch (Exception e) {
            throw new IOException("invalid PKCS8 RSA private key at " + path, e);
        }
    }

    private static RSAPublicKey readPublicKey(Path path) throws IOException {
        String pem =
                Files.readString(path)
                        .replace("-----BEGIN PUBLIC KEY-----", "")
                        .replace("-----END PUBLIC KEY-----", "")
                        .replaceAll("\\s+", "");
        byte[] der = Base64.getDecoder().decode(pem);
        try {
            return (RSAPublicKey)
                    KeyFactory.getInstance("RSA").generatePublic(new X509EncodedKeySpec(der));
        } catch (Exception e) {
            throw new IOException("invalid X.509 RSA public key at " + path, e);
        }
    }
}
