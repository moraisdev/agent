from datetime import datetime
from typing import ClassVar

from sqlalchemy import CheckConstraint, DateTime, Float, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin

_SCHEMA = "agent_memory"


class UserPreference(TimestampMixin, Base):
    __tablename__ = "user_preferences"
    __table_args__: ClassVar[tuple] = (
        CheckConstraint(
            "user_id ~ '^[0-9]{10,15}$' OR user_id ~ '^[a-zA-Z0-9._-]+$'",
            name="ck_user_id_format",
        ),
        {"schema": _SCHEMA},
    )

    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    preferred_time_range: Mapped[str] = mapped_column(String(20), server_default="this_month")
    preferred_report_type: Mapped[str] = mapped_column(String(20), server_default="business")
    preferred_language: Mapped[str] = mapped_column(String(10), server_default="pt-BR")
    preferred_format: Mapped[str] = mapped_column(String(10), server_default="text")


class ReportHistory(Base):
    __tablename__ = "report_history"
    __table_args__ = (
        Index("ix_report_history_user_date", "user_id", "generated_at"),
        {"schema": _SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)
    time_range: Mapped[str] = mapped_column(String(20), nullable=False)
    key_metrics: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LearnedPattern(TimestampMixin, Base):
    __tablename__ = "learned_patterns"
    __table_args__ = (
        UniqueConstraint("pattern_type", "pattern_key", name="uq_pattern_type_key"),
        Index("ix_pattern_type_key", "pattern_type", "pattern_key"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_confidence_range"),
        {"schema": _SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pattern_type: Mapped[str] = mapped_column(String(50), nullable=False)
    pattern_key: Mapped[str] = mapped_column(String(100), nullable=False)
    pattern_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, server_default="0.5")
    sample_count: Mapped[int] = mapped_column(Integer, server_default="0")
