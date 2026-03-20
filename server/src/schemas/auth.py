from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuthResult:
    authenticated: bool
    user_id: str
    reason: str = ""


@dataclass
class UserACL:
    allowed_tools: frozenset[str] = field(default_factory=lambda: frozenset({
        "generate_business_report",
        "query_sales", "query_clients", "query_financial",
        "get_user_context", "save_user_preference", "get_report_history",
        "health_check",
    }))
    can_access_other_users: bool = False
