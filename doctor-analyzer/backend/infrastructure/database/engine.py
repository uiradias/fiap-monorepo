"""Async SQLAlchemy engine and session factory."""

from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def get_engine(database_url: str) -> AsyncEngine:
    """Get or create the async engine singleton."""
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(database_url, echo=False)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Get the async session factory. Engine must be initialized first."""
    if _session_factory is None:
        raise RuntimeError("Database engine not initialized. Call get_engine() first.")
    return _session_factory


async def dispose_engine() -> None:
    """Dispose the engine and release connections."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
