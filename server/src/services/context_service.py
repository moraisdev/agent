from loguru import logger

from src.guards.circuit_breaker import CircuitBreaker
from src.services.memory_service import MemoryService


class ContextService:
    def __init__(self, memory: MemoryService, circuit_breaker: CircuitBreaker) -> None:
        self._memory = memory
        self._circuit_breaker = circuit_breaker

    async def build(self, user_id: str) -> str:
        sections: list[str] = []

        user_ctx = await self._memory.get_user_context(user_id)
        sections.append(
            f"USER:\n"
            f"  Report: {user_ctx.preferred_report_type} | Range: {user_ctx.preferred_time_range}\n"
            f"  Format: {user_ctx.preferred_format} | Lang: {user_ctx.preferred_language}"
        )

        history = await self._memory.get_history_text(user_id, limit=3)
        sections.append(f"HISTORY:\n  {history}")

        db_status = "FAILING" if self._circuit_breaker.is_open("database") else "OK"
        sections.append(f"SYSTEM:\n  Database: {db_status}")

        context = "\n\n".join(sections)
        logger.debug(f"Context for {user_id}: {len(context)} chars")
        return context
