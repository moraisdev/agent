from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="positive_amount"),
        CheckConstraint("status IN ('completed', 'pending', 'cancelled')", name="valid_status"),
        Index("ix_sales_date_status", "date", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="completed")


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint("tier IN ('standard', 'premium', 'enterprise')", name="valid_tier"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    tier: Mapped[str] = mapped_column(String(20), nullable=False, server_default="standard")


class FinancialSummary(Base):
    __tablename__ = "financial_summary"
    __table_args__ = (
        Index("ix_financial_month", "month", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[date] = mapped_column(Date, nullable=False)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expenses: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    active_clients: Mapped[int] = mapped_column(Integer, nullable=False)
