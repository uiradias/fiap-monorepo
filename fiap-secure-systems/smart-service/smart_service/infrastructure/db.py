"""SQLAlchemy engine bootstrap. One engine per process; sessions per call."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine


def build_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        future=True,
    )
