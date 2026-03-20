import json
import time
from collections import defaultdict
from pathlib import Path

from loguru import logger

from src.schemas.circuit_breaker import CircuitState

_STATE_FILE = Path("/tmp/namastex_circuit_state.json")


class CircuitBreaker:
    def __init__(self, max_failures: int, cooldown_seconds: int) -> None:
        self._max_failures = max_failures
        self._cooldown_seconds = cooldown_seconds
        self._states: dict[str, CircuitState] = defaultdict(CircuitState)
        self._restore_state()

    def is_open(self, service: str) -> bool:
        state = self._states[service]
        if not state.is_open:
            return False
        if time.monotonic() - state.last_failure_time > self._cooldown_seconds:
            state.is_open = False
            state.failure_count = 0
            logger.info(f"Circuit reset: {service}")
            self._persist_state()
            return False
        return True

    def record_failure(self, service: str) -> None:
        state = self._states[service]
        state.failure_count += 1
        state.last_failure_time = time.monotonic()
        if state.failure_count >= self._max_failures:
            state.is_open = True
            logger.error(f"Circuit OPEN: {service} ({state.failure_count} failures)")
        self._persist_state()

    def record_success(self, service: str) -> None:
        state = self._states[service]
        if state.failure_count > 0:
            state.failure_count = 0
            state.is_open = False
            self._persist_state()

    def _persist_state(self) -> None:
        try:
            data = {
                svc: {
                    "failure_count": st.failure_count,
                    "last_failure_time": st.last_failure_time,
                    "is_open": st.is_open,
                }
                for svc, st in self._states.items()
            }
            _STATE_FILE.write_text(json.dumps(data))
        except OSError:
            pass

    def _restore_state(self) -> None:
        try:
            if not _STATE_FILE.exists():
                return
            data = json.loads(_STATE_FILE.read_text())
            for svc, vals in data.items():
                self._states[svc] = CircuitState(
                    failure_count=vals.get("failure_count", 0),
                    last_failure_time=vals.get("last_failure_time", 0.0),
                    is_open=vals.get("is_open", False),
                )
        except (OSError, json.JSONDecodeError, KeyError):
            pass
