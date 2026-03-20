from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastmcp.exceptions import ToolError
from loguru import logger
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import settings

engine: AsyncEngine = create_async_engine(
    settings.async_database_url,
    pool_size=5,
    max_overflow=2,
    pool_pre_ping=True,
    pool_recycle=1800,
    echo=False,
)


@event.listens_for(engine.sync_engine, "connect")
def _set_statement_timeout(dbapi_conn, connection_record) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute(f"SET statement_timeout = '{settings.db_statement_timeout_ms}'")
    cursor.close()


SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = SessionFactory()
    try:
        yield session
        await session.commit()
    except ToolError:
        await session.rollback()
        raise
    except Exception as exc:
        await session.rollback()
        error_type = type(exc).__name__
        logger.error(f"Database error ({error_type}): {exc}")
        raise ToolError(f"ERROR_SERVICE: Database operation failed — {error_type}: {exc}") from exc
    finally:
        await session.close()


async def check_connection() -> bool:
    try:
        async with SessionFactory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def dispose_engine() -> None:
    await engine.dispose()
