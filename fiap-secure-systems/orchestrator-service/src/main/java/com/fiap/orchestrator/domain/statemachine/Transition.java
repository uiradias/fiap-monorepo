package com.fiap.orchestrator.domain.statemachine;

import com.fiap.orchestrator.domain.model.SessionState;

import java.util.Objects;

public record Transition(SessionState from, SessionState to, SessionStateMachine.Trigger trigger) {
    public Transition {
        Objects.requireNonNull(from, "from");
        Objects.requireNonNull(to, "to");
        Objects.requireNonNull(trigger, "trigger");
    }
}
