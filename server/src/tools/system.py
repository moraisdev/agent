from __future__ import annotations

from fastmcp import FastMCP

from src.infra.database import check_connection


def register_system_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def health_check() -> str:
        """Check database connectivity."""
        database_ok = await check_connection()
        return f"Status: {'HEALTHY' if database_ok else 'DEGRADED'}\nDatabase: {'OK' if database_ok else 'FAILED'}"

    @mcp.tool()
    async def describe_capabilities(language: str = "pt-BR") -> str:
        """Describe all available tools and resources in plain language. Call this when the user asks what you can do."""
        if language.startswith("pt"):
            return (
                "Sou o Nex, assistente de inteligência de negócios da Namastex.\n\n"
                "Posso fazer:\n"
                "1. *Relatório completo de negócios* — vendas, financeiro, clientes, detecção de anomalias, comparação com período anterior\n"
                "2. *Consultar vendas* — por data, por produto, ou por cliente\n"
                "3. *Consultar clientes* — total, por plano, novos no mês\n"
                "4. *Consultar financeiro* — receita, despesas, lucro, margem por mês\n"
                "5. *Lembrar suas preferências* — período favorito, formato, idioma\n"
                "6. *Mostrar histórico* — relatórios que já gerei pra você\n"
                "7. *Verificar saúde do sistema* — se o banco está online\n\n"
                "Períodos disponíveis: hoje, 7 dias, 14 dias, 30 dias, mês atual, mês passado, 90 dias\n"
                "Agrupamentos de vendas: por data, por produto, por cliente\n\n"
                "O que quer saber?"
            )
        return (
            "I'm Nex, Namastex's business intelligence assistant.\n\n"
            "I can:\n"
            "1. *Full business report* — sales, financial, clients, anomaly detection, trend comparison\n"
            "2. *Query sales* — by date, product, or client\n"
            "3. *Query clients* — total, by tier, new this month\n"
            "4. *Query financials* — revenue, expenses, profit, margin by month\n"
            "5. *Remember your preferences* — preferred period, format, language\n"
            "6. *Show history* — reports I've generated for you\n"
            "7. *System health* — check if database is online\n\n"
            "Available periods: today, 7d, 14d, 30d, this_month, last_month, 90d\n"
            "Sales groupings: by date, product, or client\n\n"
            "What would you like to know?"
        )
