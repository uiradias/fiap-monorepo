package com.fiap.gateway.adapter.in.rest;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.method.annotation.AuthenticationPrincipalArgumentResolver;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import com.fiap.gateway.application.service.*;
import com.fiap.gateway.domain.model.*;

class SessionsControllerTest {

    private final Clock clock = () -> Instant.parse("2026-05-09T12:00:00Z");

    private final InMemoryFakes.FakeProjections projections = new InMemoryFakes.FakeProjections();
    private final InMemoryFakes.FakeOrchestrator orchestrator =
            new InMemoryFakes.FakeOrchestrator();

    private final GetSessionService getSession = new GetSessionService(projections, orchestrator);
    private final GetReportService getReport = new GetReportService(getSession, orchestrator);
    private final CancelSessionService cancel = new CancelSessionService(getSession, orchestrator);
    private final ListUserSessionsService listUserSessions =
            new ListUserSessionsService(projections);

    private final UserId userId = new UserId(UUID.randomUUID());

    private final MockMvc mvc =
            MockMvcBuilders.standaloneSetup(
                            new SessionsController(getSession, getReport, cancel, listUserSessions))
                    .setControllerAdvice(new GlobalExceptionHandler())
                    .setCustomArgumentResolvers(new AuthenticationPrincipalArgumentResolver())
                    .build();

    @BeforeEach
    void setAuth() {
        var token =
                new UsernamePasswordAuthenticationToken(
                        userId, null, List.of(new SimpleGrantedAuthority("ROLE_USER")));
        SecurityContextHolder.getContext().setAuthentication(token);
    }

    @AfterEach
    void clearAuth() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void list_sessions_returns_200() throws Exception {
        SessionId sessionId = new SessionId(UUID.randomUUID());
        ReportId reportId = new ReportId(UUID.randomUUID());
        projections.upsert(
                new SessionProjection(
                        sessionId, userId, SessionState.REPORT_READY, clock.now(), null, reportId));

        mvc.perform(get("/api/v1/sessions"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value(sessionId.value().toString()))
                .andExpect(jsonPath("$[0].state").value("REPORT_READY"))
                .andExpect(jsonPath("$[0].reportId").value(reportId.value().toString()));
    }

    @Test
    void get_session_returns_200() throws Exception {
        SessionId sessionId = new SessionId(UUID.randomUUID());
        projections.upsert(
                SessionProjection.initial(
                        sessionId, userId, SessionState.ASSETS_UPLOADED, clock.now()));

        mvc.perform(get("/api/v1/sessions/" + sessionId.value()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(sessionId.value().toString()))
                .andExpect(jsonPath("$.state").value("ASSETS_UPLOADED"));
    }

    @Test
    void get_report_when_not_ready_returns_409() throws Exception {
        SessionId sessionId = new SessionId(UUID.randomUUID());
        projections.upsert(
                SessionProjection.initial(sessionId, userId, SessionState.ANALYZING, clock.now()));

        mvc.perform(get("/api/v1/sessions/" + sessionId.value() + "/report"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("REPORT_NOT_READY"));
    }

    @Test
    void get_session_not_found_returns_404() throws Exception {
        UUID unknownId = UUID.randomUUID();
        mvc.perform(get("/api/v1/sessions/" + unknownId))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.code").value("SESSION_NOT_FOUND"));
    }
}
