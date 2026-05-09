package com.fiap.gateway.adapter.out.http;

import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;

import static org.assertj.core.api.Assertions.assertThat;

class InternalHmacRequestSignerTest {

    @Test
    void produces_stable_canonical_form() {
        InternalHmacRequestSigner signer = new InternalHmacRequestSigner("secret");
        String canonical = signer.canonicalize(1714003200000L, "POST", "/internal/sessions",
                "{\"k\":\"v\"}".getBytes(StandardCharsets.UTF_8));
        // separator='\n', sha256 of '{"k":"v"}' = a8a3...
        assertThat(canonical).startsWith("1714003200000\nPOST\n/internal/sessions\n");
        assertThat(canonical).hasSize("1714003200000\nPOST\n/internal/sessions\n".length() + 64);
    }

    @Test
    void different_bodies_produce_different_signatures() {
        InternalHmacRequestSigner signer = new InternalHmacRequestSigner("secret");
        String s1 = signer.signature(1L, "POST", "/x", "a".getBytes());
        String s2 = signer.signature(1L, "POST", "/x", "b".getBytes());
        assertThat(s1).hasSize(64).isNotEqualTo(s2);
    }

    @Test
    void empty_body_produces_a_signature() {
        InternalHmacRequestSigner signer = new InternalHmacRequestSigner("secret");
        String s = signer.signature(1L, "GET", "/x", new byte[0]);
        assertThat(s).hasSize(64);
    }
}
