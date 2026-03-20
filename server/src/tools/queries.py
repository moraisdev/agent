from __future__ import annotations

from datetime import date

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from src.guards import InputValidator, OutputSanitizer
from src.infra.database import get_session
from src.repositories import ClientRepository, FinancialRepository, SalesRepository

from ._common import (
    QUERY_OK_PREFIX,
    check_circuit,
    record_failure_and_raise,
    record_success,
)


async def _fetch_sales_text(sales_repo: SalesRepository, group_by: str, since_date: date) -> str:
    if group_by == "product":
        rows = await sales_repo.get_by_product(since_date)
        return "\n".join(f"{row.product}: R$ {row.total:,.2f} ({row.count}x)" for row in rows)
    if group_by == "client":
        rows = await sales_repo.get_top_clients(since_date, 10)
        return "\n".join(f"{row.name}: R$ {row.total:,.2f} ({row.purchases}x)" for row in rows)
    rows = await sales_repo.get_daily(since_date)
    return "\n".join(f"{row.date}: R$ {row.total:,.2f} ({row.count}x)" for row in rows)


def register_query_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def query_sales(since: str, group_by: str = "date", user_id: str = "default") -> str:
        """Query sales data. since: start date as YYYY-MM-DD (e.g. '2026-03-01'). group_by: 'date' for daily totals, 'product' for product breakdown, 'client' for top clients ranked by revenue."""
        since_date = InputValidator.to_date(since)
        group_by = InputValidator.group_by(group_by)
        check_circuit()
        try:
            async with get_session() as session:
                text = await _fetch_sales_text(SalesRepository(session), group_by, since_date)
            record_success()
            return f"{QUERY_OK_PREFIX}: {OutputSanitizer.sanitize(text)}" if text else f"{QUERY_OK_PREFIX}: No data."
        except ToolError:
            raise
        except Exception as exc:
            raise record_failure_and_raise("Could not fetch sales data.") from exc

    @mcp.tool()
    async def query_clients(user_id: str = "default") -> str:
        """Get client statistics: total count, new clients this month, and breakdown by tier (standard, premium, enterprise)."""
        check_circuit()
        try:
            async with get_session() as session:
                stats = await ClientRepository(session).get_stats()
            record_success()
            tiers = ", ".join(f"{tier}: {count}" for tier, count in stats.by_tier.items())
            return f"{QUERY_OK_PREFIX}: Total: {stats.total} | New: {stats.new_this_month} | Tiers: {tiers}"
        except ToolError:
            raise
        except Exception as exc:
            raise record_failure_and_raise("Could not fetch client data.") from exc

    @mcp.tool()
    async def query_financial(months: int = 6, user_id: str = "default") -> str:
        """Get financial trend data: monthly revenue, profit, margin percentage, and active client count. months: how many months of history (1-12)."""
        months = InputValidator.months(months)
        check_circuit()
        try:
            async with get_session() as session:
                trend = await FinancialRepository(session).get_trend(months)
            record_success()
            lines = [
                f"{month.month}: R$ {month.revenue:,.2f} | Profit R$ {month.profit:,.2f} ({month.margin}%) | {month.active_clients} clients"
                for month in trend
            ]
            text = "\n".join(lines) if lines else "No data."
            return f"{QUERY_OK_PREFIX}: {text}"
        except ToolError:
            raise
        except Exception as exc:
            raise record_failure_and_raise("Could not fetch financial data.") from exc
