"""Shared test fixtures. Expanded in later tasks."""
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root(project_root: Path) -> Path:
    return project_root.parent


@pytest.fixture(scope="session")
def contracts_dir(repo_root: Path) -> Path:
    return repo_root / "infrastructure" / "contracts"
