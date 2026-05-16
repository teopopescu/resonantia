"""Small async circuit breaker for external provider calls."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
import time
from typing import TypeVar


T = TypeVar("T")


class ProviderCircuitOpen(RuntimeError):
    """Raised when a provider circuit is open and calls should be skipped."""

    def __init__(self, provider_name: str, retry_after_seconds: float) -> None:
        self.provider_name = provider_name
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"{provider_name} is temporarily unavailable. Please retry in "
            f"{int(retry_after_seconds) + 1} seconds."
        )


@dataclass
class CircuitBreaker:
    provider_name: str
    failure_threshold: int = 3
    failure_window_seconds: float = 60.0
    open_seconds: float = 30.0
    _failures: deque[float] = field(default_factory=deque)
    _opened_at: float | None = None

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at >= self.open_seconds:
            self._opened_at = None
            self._failures.clear()
            return False
        return True

    def retry_after_seconds(self) -> float:
        if self._opened_at is None:
            return 0.0
        return max(0.0, self.open_seconds - (time.monotonic() - self._opened_at))

    def record_success(self) -> None:
        self._failures.clear()
        self._opened_at = None

    def record_failure(self) -> None:
        now = time.monotonic()
        self._failures.append(now)
        while self._failures and now - self._failures[0] > self.failure_window_seconds:
            self._failures.popleft()
        if len(self._failures) >= self.failure_threshold:
            self._opened_at = now

    async def call(self, operation: Callable[[], Awaitable[T]], *, timeout_seconds: float) -> T:
        if self.is_open():
            raise ProviderCircuitOpen(self.provider_name, self.retry_after_seconds())
        try:
            result = await asyncio.wait_for(operation(), timeout=timeout_seconds)
        except Exception:
            self.record_failure()
            raise
        self.record_success()
        return result
