"""Per-client request budget for the public demo.

The demo is open (no API key). Limits keep accidental or automated traffic from
spinning the Container App. Set GATEWAY_RATE_LIMIT_PER_MINUTE=0 to disable.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# Paths that must stay cheap and unthrottled for probes and the OpenAPI UI.
EXEMPT_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon",
)


def _env(*names: str, default: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def rate_limit_per_minute() -> int:
    raw = _env(
        "gateway-rate-limit-per-minute",
        "GATEWAY_RATE_LIMIT_PER_MINUTE",
        default="30",
    )
    try:
        return max(0, int(raw))
    except ValueError:
        return 30


def max_prompt_chars() -> int:
    raw = _env(
        "gateway-max-prompt-chars",
        "GATEWAY_MAX_PROMPT_CHARS",
        default="4000",
    )
    try:
        return max(256, int(raw))
    except ValueError:
        return 4000


def client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: float = 60.0) -> bool:
        if limit <= 0:
            return True
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                return False
            bucket.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if any(path == p or path.startswith(p + "/") for p in EXEMPT_PREFIXES):
            return await call_next(request)
        # Agent cards and static discovery stay readable without burning the budget.
        if path.endswith("agent-card.json") or path == "/.well-known/agent-card.json":
            return await call_next(request)

        limit = rate_limit_per_minute()
        if not limiter.allow(client_key(request), limit):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "rate_limit_exceeded",
                    "limit_per_minute": limit,
                },
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
