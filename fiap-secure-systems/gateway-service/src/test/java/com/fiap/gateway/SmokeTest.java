package com.fiap.gateway;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class SmokeTest {
    @Test
    void module_compiles() {
        assertThat("gateway-service").isEqualTo("gateway-service");
    }
}
