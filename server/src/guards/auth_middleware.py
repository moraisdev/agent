"""Auth middleware — validates user identity on tool calls that require it."""

from fastmcp.exceptions import ToolError
from fastmcp.server.middleware import Middleware, MiddlewareContext

from src.guards.auth import AuthGuard

PUBLIC_TOOLS = frozenset({"health_check", "describe_capabilities"})


class AuthMiddleware(Middleware):
    def __init__(self, auth: AuthGuard) -> None:
        self._auth = auth

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        tool_name = context.message.name

        if tool_name in PUBLIC_TOOLS:
            return await call_next(context)

        args = context.message.arguments or {}
        user_id = args.get("user_id", "")

        result = self._auth.authenticate(user_id)
        if not result.authenticated:
            raise ToolError(f"ERROR_AUTH: {result.reason}")

        if not self._auth.authorize(user_id, tool_name):
            raise ToolError(f"ERROR_AUTH: Not authorized for {tool_name}")

        return await call_next(context)
