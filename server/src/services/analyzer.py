from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from src.schemas.pipeline import AnalyzeResult, ClassifyResult, GatherResult
from src.utils.report_formatter import format_brl

if TYPE_CHECKING:
    from src.services.memory_service import MemoryService


class DataAnalyzer:
    async def analyze(
        self,
        spec: ClassifyResult,
        data: GatherResult,
        memory: MemoryService | None = None,
        previous_metrics: dict | None = None,
    ) -> AnalyzeResult:
        result = AnalyzeResult()

        if not data.has_data:
            result.completeness = 0.0
            result.needs_regather = True
            result.regather_sources.append("database")
            logger.warning("[ANALYZE] Business data missing — requesting re-gather")
            return result

        if data.sales_summary and memory:
            anomalies = await memory.check_anomalies(
                data.sales_summary.total_revenue, data.sales_summary.total_sales
            )
            result.anomalies.extend(anomalies)

        if previous_metrics and data.sales_summary:
            self._compare_with_previous(data, previous_metrics, result)

        if spec.explicit_metrics:
            result.highlights.append(f"Focused on: {', '.join(spec.explicit_metrics)}")
        if data.source_errors:
            result.highlights.append(
                f"Partial data: {len(data.source_errors)} source(s) failed — "
                f"{', '.join(data.source_errors)}"
            )

        logger.info(
            f"[ANALYZE] completeness={result.completeness} "
            f"anomalies={len(result.anomalies)} regather={result.needs_regather}"
        )
        return result

    def _compare_with_previous(
        self, data: GatherResult, previous: dict, result: AnalyzeResult
    ) -> None:
        prev_revenue = previous.get("total_revenue")
        if prev_revenue and prev_revenue > 0:
            revenue_change = ((data.sales_summary.total_revenue - prev_revenue) / prev_revenue) * 100
            result.comparisons.append(
                f"vs last report: revenue {revenue_change:+.1f}% "
                f"({format_brl(prev_revenue)} → {format_brl(data.sales_summary.total_revenue)})"
            )

        prev_sales = previous.get("total_sales")
        if prev_sales and prev_sales > 0:
            sales_change = ((data.sales_summary.total_sales - prev_sales) / prev_sales) * 100
            result.comparisons.append(
                f"vs last report: sales count {sales_change:+.1f}% "
                f"({prev_sales} → {data.sales_summary.total_sales})"
            )
