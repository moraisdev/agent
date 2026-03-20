from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.guards import InputValidator
from src.infra.database import get_session
from src.repositories import MemoryRepository
from src.services import ContextService, MemoryService

from ._common import QUERY_OK_PREFIX, circuit_breaker


def register_memory_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_user_context(user_id: str) -> str:
        """Get user context: saved preferences (report type, time range, format, language), recent report history, and system status."""
        async with get_session() as session:
            memory = MemoryService(MemoryRepository(session))
            return await ContextService(memory, circuit_breaker).build(user_id)

    @mcp.tool()
    async def save_user_preference(user_id: str, preferred_report_type: str = "", preferred_time_range: str = "", preferred_format: str = "") -> str:
        """Save user preferences for future reports. preferred_report_type: business/code/combined. preferred_time_range: today/7d/14d/30d/this_month/last_month/90d. preferred_format: text/pdf/html."""
        kwargs = {}
        if preferred_report_type:
            kwargs["preferred_report_type"] = InputValidator.report_type(preferred_report_type)
        if preferred_time_range:
            kwargs["preferred_time_range"] = InputValidator.time_range(preferred_time_range)
        if preferred_format:
            kwargs["preferred_format"] = InputValidator.format_type(preferred_format)
        if not kwargs:
            raise ToolError("ERROR_INPUT: No preferences provided.")
        async with get_session() as session:
            await MemoryService(MemoryRepository(session)).save_preferences(user_id, **kwargs)
        return f"{QUERY_OK_PREFIX}: Preferences saved."

    @mcp.tool()
    async def get_report_history(user_id: str, limit: int = 5) -> str:
        """Get recently generated reports for this user with timestamps and key metrics. limit: number of reports to return (1-10)."""
        limit = InputValidator.limit(limit)
        async with get_session() as session:
            history_text = await MemoryService(MemoryRepository(session)).get_history_text(user_id, limit)
        return f"{QUERY_OK_PREFIX}: {history_text}"
