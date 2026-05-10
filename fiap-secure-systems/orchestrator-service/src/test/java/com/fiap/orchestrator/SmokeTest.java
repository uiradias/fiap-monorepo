package com.fiap.orchestrator;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class SmokeTest {
    @Test
    void compiles_and_runs() {
        assertThat(1 + 1).isEqualTo(2);
    }
}
