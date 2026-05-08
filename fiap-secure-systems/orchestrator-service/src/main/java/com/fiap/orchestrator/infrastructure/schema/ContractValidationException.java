package com.fiap.orchestrator.infrastructure.schema;

public class ContractValidationException extends RuntimeException {
    public ContractValidationException(String message) { super(message); }
    public ContractValidationException(String message, Throwable cause) { super(message, cause); }
}
