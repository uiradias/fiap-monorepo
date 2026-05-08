from __future__ import annotations

from enum import StrEnum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Profile(StrEnum):
    PRODUCTION = "production"
    E2E = "e2e"


class Settings(BaseSettings):
    """All env-driven configuration for smart-service.

    Loaded once at startup; passed by reference to adapters and the application
    service. Pydantic enforces required-vs-optional and type coercion. Secret values
    use `SecretStr` so they don't leak into logs or repr.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Profile
    profile: Profile = Field(default=Profile.PRODUCTION, alias="SMART_SERVICE_PROFILE")

    # Database
    smart_database_url: str = Field(alias="SMART_DATABASE_URL")

    # AWS / LocalStack
    aws_region: str = Field(alias="AWS_REGION")
    aws_endpoint_url: str = Field(alias="AWS_ENDPOINT_URL")
    s3_bucket: str = Field(alias="S3_BUCKET")
    sqs_analysis_jobs_url: str = Field(alias="SQS_ANALYSIS_JOBS_URL")
    sqs_analysis_results_url: str = Field(alias="SQS_ANALYSIS_RESULTS_URL")

    # Anthropic
    anthropic_api_key: SecretStr | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(alias="ANTHROPIC_MODEL")

    # Internal HMAC secret (used by /admin/replay)
    internal_hmac_secret: SecretStr = Field(alias="INTERNAL_HMAC_SECRET")

    # Observability
    otel_exporter_otlp_endpoint: str = Field(alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    service_name: str = Field(default="smart-service", alias="OTEL_SERVICE_NAME")

    # Worker tuning
    sqs_long_poll_seconds: int = Field(default=20, alias="SMART_SQS_LONG_POLL_SECONDS")
    sqs_visibility_seconds: int = Field(default=300, alias="SMART_SQS_VISIBILITY_SECONDS")
    prompt_version: str = Field(default="v1", alias="SMART_PROMPT_VERSION")
