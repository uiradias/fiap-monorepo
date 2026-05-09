package com.fiap.gateway.adapter.in.rest;

import com.fiap.gateway.adapter.in.rest.dto.ProblemDetailFactory;
import com.fiap.gateway.domain.exception.*;
import com.fiap.gateway.infrastructure.schema.InvalidPayloadException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail validation(MethodArgumentNotValidException e) {
        return ProblemDetailFactory.of(HttpStatus.BAD_REQUEST,
                "Validation failed", e.getMessage(), "VALIDATION_FAILED");
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ProblemDetail badRequest(IllegalArgumentException e) {
        return ProblemDetailFactory.of(HttpStatus.BAD_REQUEST,
                "Bad request", e.getMessage(), "BAD_REQUEST");
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ProblemDetail tooBig(MaxUploadSizeExceededException e) {
        return ProblemDetailFactory.of(HttpStatus.PAYLOAD_TOO_LARGE,
                "Asset too large", "files must be <= 25 MB", "ASSET_TOO_LARGE");
    }

    @ExceptionHandler(DuplicateEmailException.class)
    public ProblemDetail dupEmail(DuplicateEmailException e) {
        return ProblemDetailFactory.of(HttpStatus.CONFLICT,
                "Email already registered", e.getMessage(), "EMAIL_TAKEN");
    }

    @ExceptionHandler(InvalidCredentialsException.class)
    public ProblemDetail badCreds(InvalidCredentialsException e) {
        return ProblemDetailFactory.of(HttpStatus.UNAUTHORIZED,
                "Invalid credentials", e.getMessage(), "INVALID_CREDENTIALS");
    }

    @ExceptionHandler(InvalidTokenException.class)
    public ProblemDetail badToken(InvalidTokenException e) {
        return ProblemDetailFactory.of(HttpStatus.UNAUTHORIZED,
                "Invalid or expired token", e.getMessage(), "INVALID_TOKEN");
    }

    @ExceptionHandler(BundleNotFoundException.class)
    public ProblemDetail bundleNotFound(BundleNotFoundException e) {
        return ProblemDetailFactory.of(HttpStatus.NOT_FOUND,
                "Bundle not found", e.getMessage(), "BUNDLE_NOT_FOUND");
    }

    @ExceptionHandler(SessionNotFoundException.class)
    public ProblemDetail sessionNotFound(SessionNotFoundException e) {
        return ProblemDetailFactory.of(HttpStatus.NOT_FOUND,
                "Session not found", e.getMessage(), "SESSION_NOT_FOUND");
    }

    @ExceptionHandler(ForbiddenException.class)
    public ProblemDetail forbidden(ForbiddenException e) {
        return ProblemDetailFactory.of(HttpStatus.FORBIDDEN,
                "Forbidden", e.getMessage(), "FORBIDDEN");
    }

    @ExceptionHandler(ReportNotReadyException.class)
    public ProblemDetail notReady(ReportNotReadyException e) {
        return ProblemDetailFactory.of(HttpStatus.CONFLICT,
                "Report not ready", e.getMessage(), "REPORT_NOT_READY");
    }

    @ExceptionHandler(IllegalStateException.class)
    public ProblemDetail illegalState(IllegalStateException e) {
        // Domain-level business rule violations (e.g. uploading after finalize) → 409.
        return ProblemDetailFactory.of(HttpStatus.CONFLICT,
                "Illegal state", e.getMessage(), "ILLEGAL_STATE");
    }

    @ExceptionHandler(InvalidPayloadException.class)
    public ProblemDetail badPayload(InvalidPayloadException e) {
        return ProblemDetailFactory.of(HttpStatus.BAD_REQUEST,
                "Invalid payload", e.getMessage(), "INVALID_PAYLOAD");
    }
}
