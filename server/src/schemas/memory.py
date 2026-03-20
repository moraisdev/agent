from dataclasses import dataclass


@dataclass(frozen=True)
class UserContext:
    preferred_time_range: str
    preferred_report_type: str
    preferred_format: str
    preferred_language: str
