import re

_SECRET_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"postgresql(\+\w+)?://[^\s]+"), "postgresql://***REDACTED***"),
    (re.compile(r"mysql(\+\w+)?://[^\s]+"), "mysql://***REDACTED***"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36,}"), "ghp_***REDACTED***"),
    (re.compile(r"gho_[a-zA-Z0-9]{36,}"), "gho_***REDACTED***"),
    (re.compile(r"AKIA[A-Z0-9]{16}"), "***AWS_KEY_REDACTED***"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"), "Bearer ***REDACTED***"),
    (re.compile(r"(token|key|secret|password|credential)\s*[=:]\s*\S+", re.IGNORECASE), r"\1=***REDACTED***"),
]

_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\[(SYSTEM|INST|END|IGNORE)\]", re.IGNORECASE),
    re.compile(r"<<\s*(SYS|INST)\s*>>", re.IGNORECASE),
    re.compile(r"forget (everything|all|previous|instructions)", re.IGNORECASE),
    re.compile(r"ignore (previous|above|all) (instructions|context|rules)", re.IGNORECASE),
    re.compile(r"you are now a", re.IGNORECASE),
    re.compile(r"new instructions?:", re.IGNORECASE),
    re.compile(r"(override|bypass|disable) (safety|guard|filter|rules?)", re.IGNORECASE),
    re.compile(r"do not follow", re.IGNORECASE),
    re.compile(r"pretend (you are|to be)", re.IGNORECASE),
    re.compile(r"<\s*/?\s*(system|prompt|instruction)\s*>", re.IGNORECASE),
]


class OutputSanitizer:
    @staticmethod
    def sanitize(text: str) -> str:
        for pattern, replacement in _SECRET_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    @staticmethod
    def detect_injection(text: str) -> list[str]:
        detections: list[str] = []
        for pattern in _INJECTION_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                detections.append(f"Pattern '{pattern.pattern}' matched: {matches[:3]}")
        return detections

    @staticmethod
    def clean(text: str) -> tuple[str, list[str]]:
        cleaned = OutputSanitizer.sanitize(text)
        warnings = OutputSanitizer.detect_injection(cleaned)
        return cleaned, warnings
