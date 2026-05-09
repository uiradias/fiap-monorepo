package com.fiap.gateway.domain.model;
import java.util.Objects; import java.util.UUID;
public record ReportId(UUID value) {
    public ReportId { Objects.requireNonNull(value, "value"); }
    public static ReportId of(String s) { return new ReportId(UUID.fromString(s)); }
    @Override public String toString() { return value.toString(); }
}
