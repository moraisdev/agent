from __future__ import annotations

from fastmcp import FastMCP

from .memory import register_memory_tools
from .queries import register_query_tools
from .report import register_report_tools
from .system import register_system_tools


def register_tools(mcp: FastMCP) -> None:
    register_report_tools(mcp)
    register_query_tools(mcp)
    register_memory_tools(mcp)
    register_system_tools(mcp)
