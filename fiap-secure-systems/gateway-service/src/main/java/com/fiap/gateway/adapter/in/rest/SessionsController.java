package com.fiap.gateway.adapter.in.rest;

import java.util.List;
import java.util.UUID;

import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import com.fiap.gateway.adapter.in.rest.dto.*;
import com.fiap.gateway.domain.model.SessionId;
import com.fiap.gateway.domain.model.UserId;
import com.fiap.gateway.domain.port.in.*;

@RestController
@RequestMapping("/api/v1/sessions")
public class SessionsController {

    private final GetSessionUseCase getSession;
    private final GetReportUseCase getReport;
    private final CancelSessionUseCase cancel;
    private final ListUserSessionsUseCase listUserSessions;

    public SessionsController(
            GetSessionUseCase g,
            GetReportUseCase gr,
            CancelSessionUseCase c,
            ListUserSessionsUseCase listUserSessions) {
        this.getSession = g;
        this.getReport = gr;
        this.cancel = c;
        this.listUserSessions = listUserSessions;
    }

    @GetMapping
    public List<SessionSummaryResponse> list(
            @AuthenticationPrincipal UserId requester,
            @RequestParam(value = "limit", defaultValue = "50") int limit) {
        return listUserSessions.list(requester, limit).stream()
                .map(SessionSummaryResponse::of)
                .toList();
    }

    @GetMapping("/{id}")
    public SessionResponse get(
            @AuthenticationPrincipal UserId requester, @PathVariable("id") UUID id) {
        return SessionResponse.of(getSession.get(new SessionId(id), requester));
    }

    @GetMapping("/{id}/report")
    public ReportResponse report(
            @AuthenticationPrincipal UserId requester, @PathVariable("id") UUID id) {
        return ReportResponse.of(getReport.get(new SessionId(id), requester));
    }

    @PostMapping("/{id}/cancel")
    @ResponseStatus(HttpStatus.ACCEPTED)
    public void cancel(@AuthenticationPrincipal UserId requester, @PathVariable("id") UUID id) {
        cancel.cancel(new SessionId(id), requester);
    }
}
