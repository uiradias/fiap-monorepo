package com.fiap.orchestrator.domain.statemachine;

import com.fiap.orchestrator.domain.model.SessionState;

public class IllegalSessionTransitionException extends RuntimeException {
    private final SessionState fromState;
    private final SessionStateMachine.Trigger trigger;

    public IllegalSessionTransitionException(SessionState fromState, SessionStateMachine.Trigger trigger) {
        super("Illegal transition: %s + %s".formatted(fromState, trigger));
        this.fromState = fromState;
        this.trigger = trigger;
    }

    public SessionState getFromState() { return fromState; }
    public SessionStateMachine.Trigger getTrigger() { return trigger; }
}
