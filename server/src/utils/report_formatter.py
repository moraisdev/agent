from src.schemas.pipeline import AnalyzeResult, ClassifyResult, GatherResult

WHATSAPP_MAX_CHARS = 4000

LABELS = {
    "pt-BR": {
        "report_title": "RELATÓRIO DE NEGÓCIOS",
        "alert": "ALERTA",
        "trend": "TENDÊNCIA",
        "note": "NOTA",
        "sales": "VENDAS",
        "financial": "FINANCEIRO",
        "top_clients": "TOP CLIENTES",
        "products": "PRODUTOS",
        "clients": "CLIENTES",
        "activity": "ATIVIDADE",
        "revenue": "Receita",
        "sales_count": "Vendas",
        "avg_ticket": "Ticket Médio",
        "pending": "Pendente",
        "profit": "Lucro",
        "margin": "Margem",
        "change": "Variação",
        "total": "Total",
        "new": "Novos",
        "tiers": "Planos",
        "data_incomplete": "Dados {pct} completos.",
        "failed_sources": "Fontes com falha",
        "truncated": "... (relatório truncado, use query_sales para detalhes)",
    },
    "en-US": {
        "report_title": "BUSINESS REPORT",
        "alert": "ALERT",
        "trend": "TREND",
        "note": "NOTE",
        "sales": "SALES",
        "financial": "FINANCIAL",
        "top_clients": "TOP CLIENTS",
        "products": "PRODUCTS",
        "clients": "CLIENTS",
        "activity": "ACTIVITY",
        "revenue": "Revenue",
        "sales_count": "Sales",
        "avg_ticket": "Avg Ticket",
        "pending": "Pending",
        "profit": "Profit",
        "margin": "Margin",
        "change": "Change",
        "total": "Total",
        "new": "New",
        "tiers": "Tiers",
        "data_incomplete": "Data is {pct} complete.",
        "failed_sources": "Failed sources",
        "truncated": "... (report truncated, use query_sales for details)",
    },
}


def format_brl(value: float) -> str:
    formatted = f"{value:,.2f}"
    return "R$ " + formatted.replace(",", "_").replace(".", ",").replace("_", ".")


def _get_labels(language: str) -> dict[str, str]:
    return LABELS.get(language, LABELS["pt-BR"])


def _truncate(text: str, max_chars: int, truncation_message: str) -> str:
    if len(text) <= max_chars:
        return text
    cut_point = text.rfind("\n", 0, max_chars - len(truncation_message) - 2)
    if cut_point == -1:
        cut_point = max_chars - len(truncation_message) - 2
    return text[:cut_point] + "\n" + truncation_message


class ReportFormatter:
    def format(self, spec: ClassifyResult, data: GatherResult, analysis: AnalyzeResult) -> str:  # noqa: A003
        label = _get_labels(spec.language)
        lines: list[str] = []

        lines.append(f"{label['report_title']} ({spec.time_range})")

        if analysis.anomalies:
            lines.append("")
            lines.extend(f"{label['alert']}: {anomaly}" for anomaly in analysis.anomalies)

        if analysis.comparisons:
            lines.append("")
            lines.extend(f"{label['trend']}: {comparison}" for comparison in analysis.comparisons)

        if analysis.completeness < 1.0:
            pct_text = f"{analysis.completeness:.0%}"
            lines.append(f"\n{label['note']}: {label['data_incomplete'].format(pct=pct_text)}")
            if data.source_errors:
                lines.append(f"{label['failed_sources']}: {', '.join(data.source_errors)}")

        if data.has_data:
            self._format_business(lines, data, label)

        if analysis.highlights:
            lines.append("")
            lines.extend(f"{label['note']}: {highlight}" for highlight in analysis.highlights)

        report = "\n".join(lines)
        return _truncate(report, WHATSAPP_MAX_CHARS, label["truncated"])

    def _format_business(self, lines: list[str], data: GatherResult, label: dict[str, str]) -> None:
        sales = data.sales_summary
        lines.extend([
            "", f"--- {label['sales']} ---",
            f"{label['revenue']}: {format_brl(sales.total_revenue)}",
            f"{label['sales_count']}: {sales.total_sales} | {label['avg_ticket']}: {format_brl(sales.avg_ticket)}",
            f"{label['pending']}: {sales.pending_count} ({format_brl(sales.pending_amount)})",
        ])

        if data.financial and len(data.financial) >= 2:
            current_month, previous_month = data.financial[-1], data.financial[-2]
            revenue_change_pct = (
                (current_month.revenue - previous_month.revenue) / previous_month.revenue * 100
            ) if previous_month.revenue else 0
            lines.extend([
                "", f"--- {label['financial']} ---",
                f"{current_month.month}: {format_brl(current_month.revenue)} | {label['profit']} {format_brl(current_month.profit)} | {label['margin']} {current_month.margin}%",
                f"{previous_month.month}: {format_brl(previous_month.revenue)} | {label['profit']} {format_brl(previous_month.profit)} | {label['margin']} {previous_month.margin}%",
                f"{label['change']}: {revenue_change_pct:+.1f}%",
            ])

        if data.top_clients:
            lines.extend(["", f"--- {label['top_clients']} ---"])
            for rank, client in enumerate(data.top_clients, 1):
                lines.append(f"  {rank}. {client.name} — {format_brl(client.total)} ({client.purchases}x)")

        if data.products:
            lines.extend(["", f"--- {label['products']} ---"])
            for product in data.products:
                lines.append(f"  {product.product}: {format_brl(product.total)} ({product.count}x)")

        if data.client_stats:
            client_stats = data.client_stats
            lines.extend([
                "", f"--- {label['clients']} ---",
                f"{label['total']}: {client_stats.total} | {label['new']}: {client_stats.new_this_month}",
                f"{label['tiers']}: {', '.join(f'{tier}: {count}' for tier, count in client_stats.by_tier.items())}",
            ])
