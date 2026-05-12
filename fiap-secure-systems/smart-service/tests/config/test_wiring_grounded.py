from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from smart_service.config.settings import AnalysisStrategy, Profile, Settings
from smart_service.config.wiring import build_components

# Absolute path to the contracts directory at the monorepo root so tests do not
# depend on the caller's CWD.
_CONTRACTS_DIR = (
    Path(__file__).resolve().parents[3] / "infrastructure" / "contracts"
)


def _settings_kwargs():
    return dict(
        SMART_DATABASE_URL="postgresql+psycopg://x:x@localhost:5432/x",
        AWS_REGION="us-east-1",
        AWS_ENDPOINT_URL="http://localhost:4566",
        S3_BUCKET="b",
        SQS_ANALYSIS_JOBS_URL="http://localhost:4566/q1",
        SQS_ANALYSIS_RESULTS_URL="http://localhost:4566/q2",
        ANTHROPIC_MODEL="claude-sonnet-4-6",
        INTERNAL_HMAC_SECRET="hmac-secret",
        OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317",
        SMART_SERVICE_PROFILE=Profile.PRODUCTION.value,
    )


@pytest.fixture
def fake_engine():
    """Patch build_engine to avoid touching a real DB during wiring tests."""
    from sqlalchemy import create_engine
    with patch(
        "smart_service.config.wiring.build_engine",
        return_value=create_engine("sqlite:///:memory:"),
    ) as m:
        yield m


def test_grounded_strategy_without_voyage_key_raises(monkeypatch, fake_engine):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    settings = Settings(
        SMART_ANALYSIS_STRATEGY=AnalysisStrategy.GROUNDED.value,
        **_settings_kwargs(),
    )
    with pytest.raises(RuntimeError, match="VOYAGE_API_KEY"):
        build_components(settings, contracts_dir=_CONTRACTS_DIR)


def test_baseline_strategy_builds_components(monkeypatch, fake_engine):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    settings = Settings(
        SMART_ANALYSIS_STRATEGY=AnalysisStrategy.BASELINE.value,
        **_settings_kwargs(),
    )
    components = build_components(settings, contracts_dir=_CONTRACTS_DIR)
    assert components.consumer is not None
    assert components.voyage_client is None


def test_e2e_profile_uses_fake_model_regardless_of_strategy(monkeypatch, fake_engine):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    kwargs = _settings_kwargs()
    kwargs["SMART_SERVICE_PROFILE"] = Profile.E2E.value
    settings = Settings(
        SMART_ANALYSIS_STRATEGY=AnalysisStrategy.GROUNDED.value,
        **kwargs,
    )
    components = build_components(settings, contracts_dir=_CONTRACTS_DIR)
    assert components.consumer is not None
    # No voyage client opened in e2e
    assert components.voyage_client is None


def test_grounded_strategy_opens_voyage_client_when_keys_present(monkeypatch, fake_engine):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.setenv("VOYAGE_API_KEY", "fake-voyage")
    settings = Settings(
        SMART_ANALYSIS_STRATEGY=AnalysisStrategy.GROUNDED.value,
        **_settings_kwargs(),
    )
    components = build_components(settings, contracts_dir=_CONTRACTS_DIR)
    assert components.voyage_client is not None
    components.voyage_client.close()  # don't leak the client across tests
