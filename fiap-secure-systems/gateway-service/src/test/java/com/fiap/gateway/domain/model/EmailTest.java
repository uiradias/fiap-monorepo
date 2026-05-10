package com.fiap.gateway.domain.model;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class EmailTest {

    @Test
    void normalizes_to_lowercase_and_trims() {
        assertThat(Email.of("  Foo@Bar.COM  ").value()).isEqualTo("foo@bar.com");
    }

    @Test
    void rejects_blank() {
        assertThatThrownBy(() -> Email.of("  ")).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void rejects_missing_at() {
        assertThatThrownBy(() -> Email.of("not-an-email"))
                .isInstanceOf(IllegalArgumentException.class);
    }
}
