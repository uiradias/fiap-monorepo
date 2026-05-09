package com.fiap.gateway.adapter.in.rest.dto;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;

public final class ProblemDetailFactory {
    private ProblemDetailFactory() {}

    public static ProblemDetail of(HttpStatus status, String title, String detail, String code) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(status, detail);
        pd.setTitle(title);
        pd.setProperty("code", code);
        return pd;
    }
}
