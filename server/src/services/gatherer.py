from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from src.schemas.pipeline import ClassifyResult, GatherResult

if TYPE_CHECKING:
    from datetime import date

    from src.repositories.client_repo import ClientRepository
    from src.repositories.financial_repo import FinancialRepository
    from src.repositories.sales_repo import SalesRepository


class DataGatherer:
    def __init__(
        self,
        sales: SalesRepository,
        clients: ClientRepository,
        financial: FinancialRepository,
    ) -> None:
        self._sales = sales
        self._clients = clients
        self._financial = financial

    async def gather(self, spec: ClassifyResult, since: date) -> GatherResult:
        result = GatherResult()

        try:
            result.sales_summary = await self._sales.get_summary(since)
            result.top_clients = await self._sales.get_top_clients(since)
            result.products = await self._sales.get_by_product(since)
        except Exception as e:
            result.source_errors.append(f"sales: {e}")
            logger.error(f"[GATHER] sales failed: {e}")

        try:
            result.client_stats = await self._clients.get_stats()
        except Exception as e:
            result.source_errors.append(f"clients: {e}")

        try:
            result.financial = await self._financial.get_trend(6)
        except Exception as e:
            result.source_errors.append(f"financial: {e}")

        logger.info(f"[GATHER] has_data={result.has_data} errors={len(result.source_errors)}")
        return result
