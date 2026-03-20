import json
import sys

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.timing import TimingMiddleware
from loguru import logger
from starlette.responses import JSONResponse

from src.config import settings
from src.guards.auth import AuthGuard
from src.guards.auth_middleware import AuthMiddleware
from src.guards.validator import (
    VALID_FORMATS,
    VALID_GROUP_BY,
    VALID_REPORT_TYPES,
    VALID_TIME_RANGES,
)
from src.tools.registry import register_tools

logger.remove()
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
)


@lifespan
async def app_lifespan(server: FastMCP):
    from src.infra.database import dispose_engine, engine

    logger.info("Lifespan: DB engine ready")
    try:
        yield {"db_engine": engine}
    finally:
        await dispose_engine()
        logger.info("Lifespan: DB engine disposed")


mcp = FastMCP(
    settings.mcp_server_name,
    lifespan=app_lifespan,
)

mcp.add_middleware(ErrorHandlingMiddleware(include_traceback=False))
mcp.add_middleware(AuthMiddleware(
    AuthGuard(secret=settings.auth_secret, dev_mode=settings.auth_dev_mode, admin_ids=settings.admin_ids_set)
))
mcp.add_middleware(TimingMiddleware())
mcp.add_middleware(LoggingMiddleware(include_payloads=False))


@mcp.resource("config://time_ranges")
def get_time_ranges() -> str:
    return json.dumps(sorted(VALID_TIME_RANGES))


@mcp.resource("config://report_types")
def get_report_types() -> str:
    return json.dumps(sorted(VALID_REPORT_TYPES))


@mcp.resource("config://group_by_options")
def get_group_by() -> str:
    return json.dumps(sorted(VALID_GROUP_BY))


@mcp.resource("config://formats")
def get_formats() -> str:
    return json.dumps(sorted(VALID_FORMATS))


@mcp.resource("config://schema")
def get_schema() -> str:
    return json.dumps({
        "sales": {"columns": ["id", "date", "client_name", "product", "amount", "status"]},
        "clients": {"columns": ["id", "name", "email", "phone", "created_at", "tier"]},
        "financial_summary": {"columns": ["id", "month", "revenue", "expenses", "profit", "active_clients"]},
    })


# --- MCP tools ---
register_tools(mcp)


@mcp.custom_route("/ping", methods=["GET"])
def ping(request):
    return JSONResponse({"status": "healthy", "server": settings.mcp_server_name})


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting {settings.mcp_server_name} on {settings.mcp_host}:{settings.mcp_port}")
    app = mcp.http_app(path="/mcp", stateless_http=True)
    uvicorn.run(app, host=settings.mcp_host, port=settings.mcp_port)
