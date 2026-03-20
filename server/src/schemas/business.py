from dataclasses import dataclass


@dataclass(frozen=True)
class SalesSummary:
    total_revenue: float
    total_sales: int
    avg_ticket: float
    pending_count: int
    pending_amount: float


@dataclass(frozen=True)
class TopClient:
    name: str
    total: float
    purchases: int


@dataclass(frozen=True)
class ProductSales:
    product: str
    total: float
    count: int


@dataclass(frozen=True)
class DailySales:
    date: str
    total: float
    count: int


@dataclass(frozen=True)
class ClientStats:
    total: int
    by_tier: dict[str, int]
    new_this_month: int


@dataclass(frozen=True)
class FinancialMonth:
    month: str
    revenue: float
    expenses: float
    profit: float
    active_clients: int
    margin: float
