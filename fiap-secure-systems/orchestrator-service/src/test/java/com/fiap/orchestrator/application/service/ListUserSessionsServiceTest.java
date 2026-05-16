package com.fiap.orchestrator.application.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.Test;

import com.fiap.orchestrator.domain.model.*;
import com.fiap.orchestrator.domain.port.out.ReportRepositoryPort;
import com.fiap.orchestrator.domain.port.out.SessionRepositoryPort;

class ListUserSessionsServiceTest {

    @Test
    void lists_newest_first_and_attaches_report_ids() {
        SessionRepositoryPort sessions = new InMemoryFakes.SessionRepoFake();
        ReportRepositoryPort reports = new InMemoryFakes.ReportRepoFake();
        TestClock clock = new InMemoryFakes.TestClock();
        UserId uid = new UserId(UUID.randomUUID());

        SessionId s1 = new SessionId(UUID.randomUUID());
        SessionId s2 = new SessionId(UUID.randomUUID());
        sessions.insertIfAbsent(Session.newSession(s1, uid, 1, clock.now()));
        clock.advance(java.time.Duration.ofSeconds(1));
        sessions.insertIfAbsent(Session.newSession(s2, uid, 2, clock.now()));

        ReportId rid = new ReportId(UUID.randomUUID());
        reports.save(
                new AnalysisReport(
                        rid,
                        s2,
                        "ok",
                        "high",
                        java.util.Map.of(),
                        java.util.Map.of(),
                        clock.now()));

        ListUserSessionsService svc = new ListUserSessionsService(sessions, reports);
        List<SessionListItem> rows = svc.list(uid, 10);

        assertThat(rows).hasSize(2);
        assertThat(rows.getFirst().session().id()).isEqualTo(s2);
        assertThat(rows.getFirst().reportId()).isEqualTo(Optional.of(rid));
        assertThat(rows.get(1).session().id()).isEqualTo(s1);
        assertThat(rows.get(1).reportId()).isEmpty();
    }
}
