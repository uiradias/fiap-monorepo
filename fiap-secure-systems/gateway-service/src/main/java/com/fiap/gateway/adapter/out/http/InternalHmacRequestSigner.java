package com.fiap.gateway.adapter.out.http;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;

public class InternalHmacRequestSigner {

    private final byte[] secret;

    public InternalHmacRequestSigner(String secret) {
        this.secret = secret.getBytes(StandardCharsets.UTF_8);
    }

    public String canonicalize(long timestamp, String method, String path, byte[] body) {
        return timestamp + "\n"
                + method.toUpperCase() + "\n"
                + path + "\n"
                + sha256Hex(body);
    }

    public String signature(long timestamp, String method, String path, byte[] body) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret, "HmacSHA256"));
            byte[] sig = mac.doFinal(canonicalize(timestamp, method, path, body)
                    .getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(sig);
        } catch (Exception e) {
            throw new IllegalStateException("HMAC-SHA256 unavailable", e);
        }
    }

    private static String sha256Hex(byte[] body) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(md.digest(body));
        } catch (Exception e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
    }
}
