from dataclasses import dataclass


@dataclass
class CircuitState:
    failure_count: int = 0
    last_failure_time: float = 0.0
    is_open: bool = False
