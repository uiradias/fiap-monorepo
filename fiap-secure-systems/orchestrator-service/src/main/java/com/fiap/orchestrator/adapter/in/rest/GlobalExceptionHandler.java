package com.fiap.orchestrator.adapter.in.rest;

import org.springframework.dao.OptimisticLockingFailureException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import com.fiap.orchestrator.adapter.in.rest.dto.ProblemDetailFactory;
import com.fiap.orchestrator.domain.statemachine.IllegalSessionTransitionException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail validation(MethodArgumentNotValidException e) {
        return ProblemDetailFactory.of(
                HttpStatus.BAD_REQUEST, "Validation failed", e.getMessage(), "VALIDATION_FAILED");
    }

    @ExceptionHandler(IllegalSessionTransitionException.class)
    public ProblemDetail illegalTransition(IllegalSessionTransitionException e) {
        return ProblemDetailFactory.of(
                HttpStatus.CONFLICT,
                "Illegal session transition",
                e.getMessage(),
                "ILLEGAL_TRANSITION");
    }

    @ExceptionHandler(OptimisticLockingFailureException.class)
    public ProblemDetail optimisticLock(OptimisticLockingFailureException e) {
        return ProblemDetailFactory.of(
                HttpStatus.CONFLICT, "Concurrent modification", e.getMessage(), "OPTIMISTIC_LOCK");
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ProblemDetail badRequest(IllegalArgumentException e) {
        return ProblemDetailFactory.of(
                HttpStatus.BAD_REQUEST, "Bad request", e.getMessage(), "BAD_REQUEST");
    }
}
