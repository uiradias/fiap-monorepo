from __future__ import annotations

from smart_service.config.settings import Profile, Settings


def _required_env(monkeypatch):
    monkeypatch.setenv("SMART_DATABASE_URL", "postgresql+psycopg://u:p@h:5432/d")
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localstack:4566")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv(
        "SQS_ANALYSIS_JOBS_URL",
        "http://localstack:4566/000000000000/analysis-jobs",
    )
    monkeypatch.setenv(
        "SQS_ANALYSIS_RESULTS_URL",
        "http://localstack:4566/000000000000/analysis-results",
    )
    monkeypatch.setenv("S3_BUCKET", "fiap-secure-systems-assets")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    monkeypatch.setenv("INTERNAL_HMAC_SECRET", "x" * 32)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")


def test_settings_load_from_env(monkeypatch):
    _required_env(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("SMART_SERVICE_PROFILE", "production")

    s = Settings()

    assert s.profile is Profile.PRODUCTION
    assert s.smart_database_url.startswith("postgresql+psycopg://")
    assert s.s3_bucket == "fiap-secure-systems-assets"
    assert s.anthropic_model == "claude-sonnet-4-6"


def test_e2e_profile_does_not_require_anthropic_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _required_env(monkeypatch)
    monkeypatch.setenv("SMART_SERVICE_PROFILE", "e2e")

    s = Settings()

    assert s.profile is Profile.E2E
    assert s.anthropic_api_key is None
