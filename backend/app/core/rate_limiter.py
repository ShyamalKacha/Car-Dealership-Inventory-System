"""In-memory sliding-window rate limiter.

Zero external dependencies, zero ASGI middleware overhead.
Replaces slowapi which auto-registered ASGI middleware that
interfered with CORS OPTIONS preflight handling.
"""

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import HTTPException, Request, status


class _SlidingWindowCounter:
    """Tracks request timestamps per key within a sliding window."""

    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def reset(self) -> None:
        self._buckets.clear()

    def allow(self, key: str, max_count: int, window_s: float) -> bool:
        now = time.monotonic()
        cutoff = now - window_s
        self._buckets[key] = [t for t in self._buckets[key] if t > cutoff]
        if len(self._buckets[key]) >= max_count:
            return False
        self._buckets[key].append(now)
        return True


_counter = _SlidingWindowCounter()


def reset_rate_limiter() -> None:
    """Clear all rate-limit state. Called between tests."""
    _counter.reset()


def rate_limit(max_count: int, window_seconds: int = 60) -> Callable:
    """FastAPI dependency factory.

    Usage: ``Depends(rate_limit(5, 60))`` — 5 requests per 60 seconds.
    """

    async def dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        key = f"{request.url.path}:{ip}"
        if not _counter.allow(key, max_count, window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {max_count} per {window_seconds}s",
                },
            )

    return dependency
