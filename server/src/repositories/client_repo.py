from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.business import Client
from src.schemas.business import ClientStats


class ClientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_stats(self) -> ClientStats:
        total = (await self._session.execute(select(func.count(Client.id)))).scalar() or 0

        tier_rows = (await self._session.execute(
            select(Client.tier, func.count(Client.id).label("client_count")).group_by(Client.tier)
        )).all()
        by_tier = {row.tier: int(row.client_count) for row in tier_rows}

        new_count = (await self._session.execute(
            select(func.count(Client.id)).where(
                Client.created_at >= func.date_trunc("month", func.current_timestamp())
            )
        )).scalar() or 0

        return ClientStats(total=int(total), by_tier=by_tier, new_this_month=int(new_count))
