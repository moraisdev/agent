from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.guards import InputValidator
from src.infra.database import get_session

from ._common import (
    REPORT_OK_PREFIX,
    build_services,
    check_circuit,
    record_failure_and_raise,
    record_success,
    with_retry,
)


def register_report_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def generate_business_report(time_range: str = "this_month", user_id: str = "default") -> str:
        """Generate a full business report with sales, financial trends, top clients, products, anomaly detection, and comparison with the previous period. time_range options: today, 7d, 14d, 30d, this_month, last_month, 90d."""
        time_range = InputValidator.time_range(time_range)
        check_circuit()
        try:
            async def _run() -> str:
                async with get_session() as session:
                    report_service, _ = build_services(session)
                    return await report_service.business_report(time_range, user_id)

            report = await with_retry(_run)
            record_success()
            return f"{REPORT_OK_PREFIX}: {report}"
        except ToolError:
            raise
        except Exception as exc:
            raise record_failure_and_raise("Could not generate business report.") from exc
