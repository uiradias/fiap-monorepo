package com.fiap.gateway.adapter.in.rest;

import com.fiap.gateway.adapter.in.rest.dto.*;
import com.fiap.gateway.domain.model.SessionId;
import com.fiap.gateway.domain.model.UserId;
import com.fiap.gateway.domain.port.in.*;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/sessions")
public class SessionsController {

    private final GetSessionUseCase getSession;
    private final GetReportUseCase getReport;
    private final CancelSessionUseCase cancel;

    public SessionsController(GetSessionUseCase g, GetReportUseCase gr, CancelSessionUseCase c) {
        this.getSession = g;
        this.getReport = gr;
        this.cancel = c;
    }

    @GetMapping("/{id}")
    public SessionResponse get(
            @AuthenticationPrincipal UserId requester,
            @PathVariable("id") UUID id) {
        return SessionResponse.of(getSession.get(new SessionId(id), requester));
    }

    @GetMapping("/{id}/report")
    public ReportResponse report(
            @AuthenticationPrincipal UserId requester,
            @PathVariable("id") UUID id) {
        return ReportResponse.of(getReport.get(new SessionId(id), requester));
    }

    @PostMapping("/{id}/cancel")
    @ResponseStatus(HttpStatus.ACCEPTED)
    public void cancel(
            @AuthenticationPrincipal UserId requester,
            @PathVariable("id") UUID id) {
        cancel.cancel(new SessionId(id), requester);
    }
}
