from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from fastmcp.exceptions import ToolError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.guards import CircuitBreaker
from src.repositories import (
    ClientRepository,
    FinancialRepository,
    MemoryRepository,
    SalesRepository,
)
from src.services import DataGatherer, MemoryService, ReportService
from src.services.analyzer import DataAnalyzer
from src.utils.report_formatter import ReportFormatter

circuit_breaker = CircuitBreaker(
    max_failures=settings.circuit_breaker_max_failures,
    cooldown_seconds=settings.circuit_breaker_cooldown_seconds,
)

REPORT_OK_PREFIX = "REPORT_OK"
QUERY_OK_PREFIX = "QUERY_OK"

_MAX_RETRIES = 2
_RETRY_BACKOFF_SECONDS = 1.0

T = TypeVar("T")


async def with_retry(fn: Callable[[], Awaitable[T]], retries: int = _MAX_RETRIES) -> T:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return await fn()
        except ToolError:
            raise
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                wait = _RETRY_BACKOFF_SECONDS * attempt
                logger.warning(f"Retry {attempt}/{retries} after {type(exc).__name__}, backoff {wait}s")
                await asyncio.sleep(wait)
    raise last_exc  # type: ignore[misc]


def check_circuit() -> None:
    if circuit_breaker.is_open("database"):
        raise ToolError("ERROR_SERVICE: database is temporarily down.")


def record_success() -> None:
    circuit_breaker.record_success("database")


def record_failure_and_raise(message: str) -> ToolError:
    circuit_breaker.record_failure("database")
    logger.exception(f"Tool failed (database): {message}")
    return ToolError(f"ERROR_SERVICE: {message}")


def build_services(session: AsyncSession) -> tuple[ReportService, MemoryService]:
    memory = MemoryService(MemoryRepository(session))
    gatherer = DataGatherer(
        SalesRepository(session), ClientRepository(session),
        FinancialRepository(session),
    )
    return ReportService(gatherer, memory, DataAnalyzer(), ReportFormatter()), memory
