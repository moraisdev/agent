from loguru import logger

from src.config import settings
from src.repositories.memory_repo import MemoryRepository
from src.schemas.memory import UserContext

_BASELINE_TYPE = "baseline"
_REVENUE_KEY = "monthly_revenue"
_SALES_KEY = "monthly_sales"


class MemoryService:
    def __init__(self, repo: MemoryRepository) -> None:
        self._repo = repo

    async def get_user_context(self, user_id: str) -> UserContext:
        prefs = await self._repo.get_preferences(user_id)
        if prefs:
            return UserContext(
                preferred_time_range=prefs.preferred_time_range,
                preferred_report_type=prefs.preferred_report_type,
                preferred_format=prefs.preferred_format,
                preferred_language=prefs.preferred_language,
            )
        return UserContext("this_month", "business", "text", "pt-BR")

    async def save_preferences(self, user_id: str, **kwargs: str) -> None:
        non_empty = {key: value for key, value in kwargs.items() if value}
        if non_empty:
            await self._repo.upsert_preferences(user_id, **non_empty)

    async def record_report(
        self, user_id: str, report_type: str, time_range: str, key_metrics: dict
    ) -> None:
        await self._repo.save_report(user_id, report_type, time_range, key_metrics)
        await self._repo.upsert_preferences(
            user_id,
            preferred_report_type=report_type,
            preferred_time_range=time_range,
        )
        deleted = await self._repo.enforce_retention(user_id)
        if deleted > 0:
            logger.info(f"Retention: pruned {deleted} old reports for user={user_id}")
        logger.info(f"Report recorded: user={user_id} type={report_type}")

    async def get_history_text(self, user_id: str, limit: int = 5) -> str:
        records = await self._repo.get_history(user_id, limit)
        if not records:
            return "No report history."
        lines = [f"Reports ({len(records)} recent):"]
        for record in records:
            metric_summary = ", ".join(
                f"{key}: {value}" for key, value in list(record.key_metrics.items())[:3]
            )
            timestamp = record.generated_at.strftime("%Y-%m-%d %H:%M") if record.generated_at else "?"
            lines.append(f"  [{timestamp}] {record.report_type} ({record.time_range}) — {metric_summary}")
        return "\n".join(lines)

    async def get_previous_metrics(self, user_id: str, report_type: str) -> dict | None:
        records = await self._repo.get_history(user_id, limit=5)
        for record in records:
            if record.report_type == report_type:
                return record.key_metrics
        return None

    async def check_anomalies(self, revenue: float, sales: int) -> list[str]:
        anomalies: list[str] = []
        patterns = await self._repo.get_patterns_by_type(_BASELINE_TYPE)
        baselines: dict[str, tuple[float | None, float]] = {}
        for pattern in patterns:
            baselines[pattern.pattern_key] = (
                pattern.pattern_value.get("avg"),
                pattern.confidence,
            )

        revenue_entry = baselines.get(_REVENUE_KEY)
        if revenue_entry:
            revenue_avg, confidence = revenue_entry
            if revenue_avg and revenue_avg > 0 and confidence >= 0.5:
                ratio = revenue / revenue_avg
                if ratio < (1 - settings.anomaly_revenue_threshold):
                    drop_pct = round((1 - ratio) * 100, 1)
                    anomalies.append(
                        f"Revenue {drop_pct}% below baseline "
                        f"(avg: R$ {revenue_avg:,.2f}, confidence: {confidence:.0%})"
                    )
                elif ratio > (1 + settings.anomaly_revenue_threshold * 2):
                    spike_pct = round((ratio - 1) * 100, 1)
                    anomalies.append(f"Revenue {spike_pct}% above baseline — investigate")

        sales_entry = baselines.get(_SALES_KEY)
        if sales_entry:
            sales_avg, confidence = sales_entry
            if (
                sales_avg
                and sales_avg > 0
                and confidence >= 0.5
                and sales < sales_avg * (1 - settings.anomaly_sales_threshold)
            ):
                anomalies.append(f"Sales count ({sales}) below baseline ({sales_avg:.0f})")

        return anomalies

    async def update_baselines(self, revenue: float, sales: int) -> None:
        alpha = settings.ema_alpha
        patterns = await self._repo.get_patterns_by_type(_BASELINE_TYPE)
        baselines = {pattern.pattern_key: pattern.pattern_value.get("avg") for pattern in patterns}

        for key, new_value in [(_REVENUE_KEY, revenue), (_SALES_KEY, float(sales))]:
            old_avg = baselines.get(key)
            ema = alpha * new_value + (1 - alpha) * old_avg if old_avg else new_value
            await self._repo.upsert_pattern(
                _BASELINE_TYPE, key, {"avg": round(ema, 2)},
            )
