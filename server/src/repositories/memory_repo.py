from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.memory import LearnedPattern, ReportHistory, UserPreference

DEFAULT_RETENTION_DAYS = 90
MAX_REPORTS_PER_USER = 50


class MemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_preferences(self, user_id: str) -> UserPreference | None:
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def upsert_preferences(self, user_id: str, **fields: str) -> None:
        existing = await self.get_preferences(user_id)
        if existing:
            for key, value in fields.items():
                if value is not None and hasattr(existing, key):
                    setattr(existing, key, value)
        else:
            self._session.add(UserPreference(user_id=user_id, **fields))
        await self._session.flush()

    async def save_report(
        self, user_id: str, report_type: str, time_range: str, key_metrics: dict
    ) -> None:
        self._session.add(ReportHistory(
            user_id=user_id,
            report_type=report_type,
            time_range=time_range,
            key_metrics=key_metrics,
        ))
        await self._session.flush()

    async def get_history(self, user_id: str, limit: int = 5) -> list[ReportHistory]:
        stmt = (
            select(ReportHistory)
            .where(ReportHistory.user_id == user_id)
            .order_by(ReportHistory.generated_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def enforce_retention(
        self, user_id: str, max_age_days: int = DEFAULT_RETENTION_DAYS, max_rows: int = MAX_REPORTS_PER_USER
    ) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        age_stmt = (
            delete(ReportHistory)
            .where(ReportHistory.user_id == user_id, ReportHistory.generated_at < cutoff)
        )
        age_result = await self._session.execute(age_stmt)
        deleted = age_result.rowcount

        count_stmt = select(func.count(ReportHistory.id)).where(ReportHistory.user_id == user_id)
        total = (await self._session.execute(count_stmt)).scalar() or 0

        if total > max_rows:
            keep_ids_stmt = (
                select(ReportHistory.id)
                .where(ReportHistory.user_id == user_id)
                .order_by(ReportHistory.generated_at.desc())
                .limit(max_rows)
            )
            keep_ids = (await self._session.execute(keep_ids_stmt)).scalars().all()
            overflow_stmt = (
                delete(ReportHistory)
                .where(ReportHistory.user_id == user_id, ReportHistory.id.notin_(keep_ids))
            )
            overflow_result = await self._session.execute(overflow_stmt)
            deleted += overflow_result.rowcount

        if deleted > 0:
            await self._session.flush()
        return deleted

    async def upsert_pattern(
        self, pattern_type: str, pattern_key: str, value: dict, confidence: float = 0.5
    ) -> None:
        existing = await self._get_pattern(pattern_type, pattern_key)
        if existing:
            existing.pattern_value = value
            existing.sample_count = (existing.sample_count or 0) + 1
            existing.confidence = self._compute_confidence(existing.sample_count)
        else:
            self._session.add(LearnedPattern(
                pattern_type=pattern_type,
                pattern_key=pattern_key,
                pattern_value=value,
                confidence=confidence,
                sample_count=1,
            ))
        await self._session.flush()

    async def get_patterns_by_type(self, pattern_type: str) -> list[LearnedPattern]:
        stmt = (
            select(LearnedPattern)
            .where(LearnedPattern.pattern_type == pattern_type)
            .order_by(LearnedPattern.confidence.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def _get_pattern(self, pattern_type: str, key: str) -> LearnedPattern | None:
        stmt = select(LearnedPattern).where(
            LearnedPattern.pattern_type == pattern_type,
            LearnedPattern.pattern_key == key,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    @staticmethod
    def _compute_confidence(sample_count: int) -> float:
        """Confidence grows logarithmically: 1 sample → 0.3, 5 → 0.7, 10 → 0.83, 20+ → ~0.95."""
        import math
        return min(round(1 - 1 / (1 + math.log1p(sample_count * 0.5)), 2), 0.99)
