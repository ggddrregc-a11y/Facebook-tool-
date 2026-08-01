from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        database_url = settings.database_url

        # SQLite support
        if database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            _engine = create_async_engine(
                database_url,
                echo=settings.debug,
                connect_args=connect_args,
            )
        else:
            # PostgreSQL / Supabase
            connect_args = {"ssl": "require"} if "supabase" in database_url else {"ssl": "prefer"}
            _engine = create_async_engine(
                database_url,
                echo=settings.debug,
                poolclass=NullPool,
                connect_args=connect_args,
            )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    import os
    from app.models.base import Base
    engine = get_engine()
    settings = get_settings()
    # Create data directory for SQLite
    if settings.database_url.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_initialized")


async def close_db() -> None:
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("database_connection_closed")
