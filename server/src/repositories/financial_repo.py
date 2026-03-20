from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.business import FinancialSummary
from src.schemas.business import FinancialMonth


class FinancialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_trend(self, months: int = 6) -> list[FinancialMonth]:
        stmt = (
            select(FinancialSummary)
            .order_by(FinancialSummary.month.desc())
            .limit(months)
        )
        rows = (await self._session.execute(stmt)).scalars().all()

        result: list[FinancialMonth] = []
        for row in reversed(rows):
            revenue = float(row.revenue)
            profit = float(row.profit)
            margin = round((profit / revenue) * 100, 2) if revenue > 0 else 0.0
            result.append(FinancialMonth(
                month=row.month.strftime("%Y-%m"),
                revenue=revenue,
                expenses=float(row.expenses),
                profit=profit,
                active_clients=row.active_clients,
                margin=margin,
            ))
        return result
