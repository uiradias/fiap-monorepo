package com.fiap.orchestrator.domain.statemachine;

import java.util.Objects;

import com.fiap.orchestrator.domain.model.SessionState;

public record Transition(SessionState from, SessionState to, SessionStateMachine.Trigger trigger) {
    public Transition {
        Objects.requireNonNull(from, "from");
        Objects.requireNonNull(to, "to");
        Objects.requireNonNull(trigger, "trigger");
    }
}
