from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.business import Sale
from src.schemas.business import DailySales, ProductSales, SalesSummary, TopClient

_COMPLETED = Sale.status == "completed"
_PENDING = Sale.status == "pending"


class SalesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_summary(self, since: date) -> SalesSummary:
        stmt = select(
            func.coalesce(func.sum(case((_COMPLETED, Sale.amount), else_=0)), 0).label("total_revenue"),
            func.count(case((_COMPLETED, 1))).label("completed_count"),
            func.coalesce(func.avg(case((_COMPLETED, Sale.amount))), 0).label("avg_ticket"),
            func.count(case((_PENDING, 1))).label("pending_count"),
            func.coalesce(func.sum(case((_PENDING, Sale.amount), else_=0)), 0).label("pending_amount"),
        ).where(Sale.date >= since)

        row = (await self._session.execute(stmt)).one()
        return SalesSummary(
            total_revenue=float(row.total_revenue),
            total_sales=int(row.completed_count),
            avg_ticket=round(float(row.avg_ticket), 2),
            pending_count=int(row.pending_count),
            pending_amount=float(row.pending_amount),
        )

    async def get_top_clients(self, since: date, limit: int = 5) -> list[TopClient]:
        stmt = (
            select(
                Sale.client_name,
                func.sum(Sale.amount).label("total"),
                func.count().label("purchases"),
            )
            .where(Sale.date >= since, _COMPLETED)
            .group_by(Sale.client_name)
            .order_by(func.sum(Sale.amount).desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [TopClient(name=row.client_name, total=float(row.total), purchases=int(row.purchases)) for row in rows]

    async def get_by_product(self, since: date) -> list[ProductSales]:
        stmt = (
            select(Sale.product, func.sum(Sale.amount).label("total"), func.count().label("count"))
            .where(Sale.date >= since, _COMPLETED)
            .group_by(Sale.product)
            .order_by(func.sum(Sale.amount).desc())
        )
        rows = (await self._session.execute(stmt)).all()
        return [ProductSales(product=row.product, total=float(row.total), count=int(row.count)) for row in rows]

    async def get_daily(self, since: date) -> list[DailySales]:
        stmt = (
            select(Sale.date, func.sum(Sale.amount).label("total"), func.count().label("count"))
            .where(Sale.date >= since)
            .group_by(Sale.date)
            .order_by(Sale.date)
        )
        rows = (await self._session.execute(stmt)).all()
        return [DailySales(date=str(row.date), total=float(row.total), count=int(row.count)) for row in rows]
