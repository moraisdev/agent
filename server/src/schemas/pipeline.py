from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schemas.business import (
        ClientStats,
        FinancialMonth,
        ProductSales,
        SalesSummary,
        TopClient,
    )


class Stage(Enum):
    CLASSIFY = auto()
    GATHER = auto()
    ANALYZE = auto()
    FORMAT = auto()
    DONE = auto()


@dataclass
class PipelineState:
    current: Stage = Stage.CLASSIFY
    history: list[Stage] = field(default_factory=list)
    retries: int = 0
    max_retries: int = 1

    def transition(self, to: Stage) -> None:
        self.history.append(self.current)
        self.current = to

    @property
    def can_retry(self) -> bool:
        return self.retries < self.max_retries


@dataclass
class ClassifyResult:
    report_type: str
    time_range: str
    user_id: str
    language: str = "pt-BR"
    output_format: str = "text"
    explicit_metrics: list[str] = field(default_factory=list)


@dataclass
class GatherResult:
    sales_summary: SalesSummary | None = None
    top_clients: list[TopClient] | None = None
    products: list[ProductSales] | None = None
    financial: list[FinancialMonth] | None = None
    client_stats: ClientStats | None = None
    source_errors: list[str] = field(default_factory=list)

    @property
    def has_data(self) -> bool:
        return self.sales_summary is not None


@dataclass
class AnalyzeResult:
    anomalies: list[str] = field(default_factory=list)
    comparisons: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    completeness: float = 1.0
    needs_regather: bool = False
    regather_sources: list[str] = field(default_factory=list)
