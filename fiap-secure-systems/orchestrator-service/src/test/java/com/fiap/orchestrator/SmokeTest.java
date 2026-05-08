package com.fiap.orchestrator;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class SmokeTest {
    @Test
    void compiles_and_runs() {
        assertThat(1 + 1).isEqualTo(2);
    }
}
