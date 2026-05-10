package com.fiap.gateway.adapter.out.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.UUID;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import com.fiap.gateway.domain.exception.InvalidTokenException;
import com.fiap.gateway.domain.model.UserId;

class JwtTokenIssuerTest {

    @TempDir static Path tmp;

    static Path priv;
    static Path pub;

    @BeforeAll
    static void writeKeys() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048);
        KeyPair kp = kpg.generateKeyPair();

        priv = tmp.resolve("priv.pem");
        pub = tmp.resolve("pub.pem");

        String privPem =
                "-----BEGIN PRIVATE KEY-----\n"
                        + Base64.getMimeEncoder(64, "\n".getBytes())
                                .encodeToString(kp.getPrivate().getEncoded())
                        + "\n-----END PRIVATE KEY-----\n";
        String pubPem =
                "-----BEGIN PUBLIC KEY-----\n"
                        + Base64.getMimeEncoder(64, "\n".getBytes())
                                .encodeToString(kp.getPublic().getEncoded())
                        + "\n-----END PUBLIC KEY-----\n";

        Files.writeString(priv, privPem);
        Files.writeString(pub, pubPem);
    }

    private JwtTokenIssuer newIssuer() throws IOException {
        return new JwtTokenIssuer(
                priv.toString(),
                pub.toString(),
                "gateway-service",
                Duration.ofMinutes(15),
                Duration.ofDays(7));
    }

    @Test
    void issues_and_verifies_access_token() throws Exception {
        JwtTokenIssuer issuer = newIssuer();
        UserId uid = new UserId(UUID.randomUUID());
        Instant now = Instant.now();

        String jws = issuer.issueAccessToken(uid, now);
        UserId verified = issuer.verifyAccessToken(jws);

        assertThat(verified).isEqualTo(uid);
    }

    @Test
    void rejects_token_signed_with_a_different_key() throws Exception {
        JwtTokenIssuer issuer = newIssuer();
        Instant now = Instant.now();
        String jws = issuer.issueAccessToken(new UserId(UUID.randomUUID()), now);

        // tamper: replace the last char of the signature
        String tampered = jws.substring(0, jws.length() - 1) + (jws.endsWith("a") ? "b" : "a");

        assertThatThrownBy(() -> issuer.verifyAccessToken(tampered))
                .isInstanceOf(InvalidTokenException.class);
    }

    @Test
    void refresh_token_plaintext_is_random_and_hash_is_deterministic() throws Exception {
        JwtTokenIssuer issuer = newIssuer();
        String t1 = issuer.generateRefreshTokenPlaintext();
        String t2 = issuer.generateRefreshTokenPlaintext();
        assertThat(t1).isNotEqualTo(t2);
        assertThat(t1).hasSizeGreaterThan(20);

        String h = issuer.hashRefreshToken(t1);
        assertThat(h).hasSize(64); // sha256 hex
        assertThat(h).isEqualTo(issuer.hashRefreshToken(t1)); // deterministic
    }
}
