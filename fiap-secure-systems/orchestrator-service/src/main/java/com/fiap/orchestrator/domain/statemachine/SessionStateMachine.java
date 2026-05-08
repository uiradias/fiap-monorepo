package com.fiap.orchestrator.domain.statemachine;

import com.fiap.orchestrator.domain.model.SessionState;

import static com.fiap.orchestrator.domain.model.SessionState.*;

public class SessionStateMachine {

    public enum Trigger {
        OUTBOX_JOB_PUBLISHED,
        RECEIVE_RESULT_STARTED,
        RECEIVE_RESULT_SUCCEEDED,
        REPORT_PERSISTED,
        RECEIVE_RESULT_FAILED,
        DLQ_TRIPPED,
        CANCEL
    }

    public Transition next(SessionState from, Trigger trigger) {
        if (from.isTerminal()) {
            throw new IllegalSessionTransitionException(from, trigger);
        }
        SessionState to = switch (trigger) {
            case OUTBOX_JOB_PUBLISHED ->
                    from == ASSETS_UPLOADED ? QUEUED_FOR_ANALYSIS : null;
            case RECEIVE_RESULT_STARTED ->
                    from == QUEUED_FOR_ANALYSIS ? ANALYZING : null;
            case RECEIVE_RESULT_SUCCEEDED ->
                    from == ANALYZING ? ANALYSIS_COMPLETED : null;
            case REPORT_PERSISTED ->
                    from == ANALYSIS_COMPLETED ? REPORT_READY : null;
            case RECEIVE_RESULT_FAILED, DLQ_TRIPPED -> FAILED;
            case CANCEL -> CANCELED;
        };
        if (to == null) {
            throw new IllegalSessionTransitionException(from, trigger);
        }
        return new Transition(from, to, trigger);
    }
}
