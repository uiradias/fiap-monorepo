package com.fiap.gateway.adapter.out.s3;

import com.fiap.gateway.LocalStackTestcontainersBase;
import com.fiap.gateway.Provisioning;
import com.fiap.gateway.domain.model.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;

import java.io.ByteArrayInputStream;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class S3AssetStorageAdapterIT extends LocalStackTestcontainersBase {

    @Autowired S3AssetStorageAdapter storage;
    @Autowired S3Client s3;

    @Test
    void puts_object_at_expected_key_with_content_type() throws Exception {
        BundleId bid = new BundleId(UUID.randomUUID());
        AssetId aid = new AssetId(UUID.randomUUID());
        byte[] body = "hello".getBytes();

        String key = storage.put(bid, aid, "hello.png", ContentType.IMAGE_PNG, body.length,
                new ByteArrayInputStream(body));

        assertThat(key).isEqualTo("sessions/" + bid + "/hello.png");
        var head = s3.headObject(b -> b.bucket(Provisioning.bucket).key(key));
        assertThat(head.contentType()).isEqualTo("image/png");
        assertThat(head.contentLength()).isEqualTo((long) body.length);
        var fetched = s3.getObject(GetObjectRequest.builder()
                .bucket(Provisioning.bucket).key(key).build());
        assertThat(fetched.readAllBytes()).isEqualTo(body);
    }
}
