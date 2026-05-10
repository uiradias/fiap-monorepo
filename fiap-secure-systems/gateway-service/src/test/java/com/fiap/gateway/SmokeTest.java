package com.fiap.gateway;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class SmokeTest {
    @Test
    void module_compiles() {
        assertThat("gateway-service").isEqualTo("gateway-service");
    }
}
