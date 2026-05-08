package com.fiap.orchestrator.domain.statemachine;

import com.fiap.orchestrator.domain.model.SessionState;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;

import static com.fiap.orchestrator.domain.model.SessionState.*;
import static com.fiap.orchestrator.domain.statemachine.SessionStateMachine.Trigger.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class SessionStateMachineTest {

    private final SessionStateMachine sm = new SessionStateMachine();

    @Test
    void happy_path_walks_to_REPORT_READY() {
        SessionState s = ASSETS_UPLOADED;
        s = sm.next(s, OUTBOX_JOB_PUBLISHED).to();
        assertThat(s).isEqualTo(QUEUED_FOR_ANALYSIS);
        s = sm.next(s, RECEIVE_RESULT_STARTED).to();
        assertThat(s).isEqualTo(ANALYZING);
        s = sm.next(s, RECEIVE_RESULT_SUCCEEDED).to();
        assertThat(s).isEqualTo(ANALYSIS_COMPLETED);
        s = sm.next(s, REPORT_PERSISTED).to();
        assertThat(s).isEqualTo(REPORT_READY);
    }

    @Test
    void cancel_from_any_non_terminal_yields_CANCELED() {
        for (SessionState from : SessionState.nonTerminal()) {
            assertThat(sm.next(from, CANCEL).to()).isEqualTo(CANCELED);
        }
    }

    @ParameterizedTest
    @EnumSource(value = SessionState.class, names = {"REPORT_READY", "FAILED", "CANCELED"})
    void cancel_from_terminal_is_illegal(SessionState terminal) {
        assertThatThrownBy(() -> sm.next(terminal, CANCEL))
                .isInstanceOf(IllegalSessionTransitionException.class)
                .hasMessageContaining(terminal.name());
    }

    @Test
    void result_failed_from_any_non_terminal_yields_FAILED() {
        for (SessionState from : SessionState.nonTerminal()) {
            assertThat(sm.next(from, RECEIVE_RESULT_FAILED).to()).isEqualTo(FAILED);
        }
    }

    @Test
    void dlq_tripped_from_any_non_terminal_yields_FAILED() {
        for (SessionState from : SessionState.nonTerminal()) {
            assertThat(sm.next(from, DLQ_TRIPPED).to()).isEqualTo(FAILED);
        }
    }

    @Test
    void wrong_trigger_for_state_is_illegal() {
        assertThatThrownBy(() -> sm.next(ASSETS_UPLOADED, RECEIVE_RESULT_STARTED))
                .isInstanceOf(IllegalSessionTransitionException.class);
        assertThatThrownBy(() -> sm.next(QUEUED_FOR_ANALYSIS, RECEIVE_RESULT_SUCCEEDED))
                .isInstanceOf(IllegalSessionTransitionException.class);
        assertThatThrownBy(() -> sm.next(QUEUED_FOR_ANALYSIS, OUTBOX_JOB_PUBLISHED))
                .isInstanceOf(IllegalSessionTransitionException.class);
        assertThatThrownBy(() -> sm.next(ANALYZING, REPORT_PERSISTED))
                .isInstanceOf(IllegalSessionTransitionException.class);
    }

    @Test
    void any_trigger_from_REPORT_READY_is_illegal() {
        for (SessionStateMachine.Trigger t : SessionStateMachine.Trigger.values()) {
            assertThatThrownBy(() -> sm.next(REPORT_READY, t))
                    .as("trigger %s on REPORT_READY", t)
                    .isInstanceOf(IllegalSessionTransitionException.class);
        }
    }

    @Test
    void exception_carries_from_and_trigger() {
        try {
            sm.next(REPORT_READY, CANCEL);
        } catch (IllegalSessionTransitionException e) {
            assertThat(e.getFromState()).isEqualTo(REPORT_READY);
            assertThat(e.getTrigger()).isEqualTo(CANCEL);
        }
    }
}
