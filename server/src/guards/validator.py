import re
from datetime import date, timedelta

from fastmcp.exceptions import ToolError

VALID_TIME_RANGES = frozenset({"today", "7d", "14d", "30d", "this_month", "last_month", "90d"})
VALID_GROUP_BY = frozenset({"date", "product", "client"})
VALID_FORMATS = frozenset({"text", "pdf", "html"})
VALID_REPORT_TYPES = frozenset({"business", "code", "combined"})
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_REPO_RE = re.compile(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$")


class InputValidator:
    @staticmethod
    def time_range(value: str) -> str:
        if value in VALID_TIME_RANGES:
            return value
        return "this_month"

    @staticmethod
    def date_str(value: str) -> str:
        if not _DATE_RE.match(value):
            raise ToolError(f"ERROR_INPUT: Invalid date: '{value}'. Expected YYYY-MM-DD.")
        return value

    @staticmethod
    def to_date(value: str) -> date:
        validated = InputValidator.date_str(value)
        return date.fromisoformat(validated)

    @staticmethod
    def time_range_to_date(time_range: str) -> date:
        today = date.today()
        if time_range == "today":
            return today
        if time_range == "this_month":
            return today.replace(day=1)
        if time_range == "last_month":
            first_of_month = today.replace(day=1)
            return (first_of_month - timedelta(days=1)).replace(day=1)
        days_map = {"7d": 7, "14d": 14, "30d": 30, "90d": 90}
        days = days_map.get(time_range, 30)
        return today - timedelta(days=days)

    @staticmethod
    def repo(value: str) -> str:
        if not value:
            return ""
        if not _REPO_RE.match(value):
            raise ToolError(f"ERROR_INPUT: Invalid repo: '{value}'. Expected 'owner/repo'.")
        return value

    @staticmethod
    def group_by(value: str) -> str:
        return value if value in VALID_GROUP_BY else "date"

    @staticmethod
    def report_type(value: str) -> str:
        return value if value in VALID_REPORT_TYPES else "business"

    @staticmethod
    def format_type(value: str) -> str:
        return value if value in VALID_FORMATS else "text"

    @staticmethod
    def months(value: int) -> int:
        return max(1, min(value, 12))

    @staticmethod
    def limit(value: int, ceiling: int = 10) -> int:
        return max(1, min(value, ceiling))
