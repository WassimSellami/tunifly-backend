import asyncio
import os
import time
from collections import deque
from typing import Deque

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        return default

    return max(1, value)


def _env_paths(name: str, default: str) -> tuple[str, ...]:
    raw_value = os.getenv(name, default)
    return tuple(
        path.strip()
        for path in raw_value.split(",")
        if path.strip()
    )


def _normalize_path(path: str) -> str:
    return path.rstrip("/") or "/"


def _path_matches_template(path: str, template: str) -> bool:
    path_parts = [part for part in _normalize_path(path).split("/") if part]
    template_parts = [part for part in _normalize_path(template).split("/") if part]

    if len(path_parts) != len(template_parts):
        return False

    for path_part, template_part in zip(path_parts, template_parts):
        if template_part.startswith("{") and template_part.endswith("}"):
            if not path_part:
                return False
            continue
        if path_part != template_part:
            return False

    return True


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        max_requests: int | None = None,
        heavy_route_max_requests: int | None = None,
        window_seconds: int | None = None,
        exempt_paths: tuple[str, ...] | None = None,
        route_limits: tuple[tuple[str, tuple[str, ...], int], ...] | None = None,
    ) -> None:
        self.app = app
        self.max_requests = max_requests or _env_int("RATE_LIMIT_REQUESTS", 60)
        self.heavy_route_max_requests = (
            heavy_route_max_requests
            or _env_int("RATE_LIMIT_HEAVY_ROUTE_REQUESTS", 20)
        )
        self.window_seconds = window_seconds or _env_int("RATE_LIMIT_WINDOW_SECONDS", 60)
        self.exempt_paths = exempt_paths or _env_paths(
            "RATE_LIMIT_EXEMPT_PATHS",
            "/docs,/redoc,/openapi.json,/ping",
        )
        self.route_limits = route_limits or (
            ("/flights/", ("GET",), self.heavy_route_max_requests),
            ("/flights/{flight_id}", ("GET",), self.heavy_route_max_requests),
            ("/price-history/flight/{flight_id}", ("GET",), self.heavy_route_max_requests),
        )
        self._requests: dict[str, Deque[float]] = {}
        self._lock = asyncio.Lock()
        self._last_cleanup = time.monotonic()

    def _is_exempt(self, path: str) -> bool:
        normalized_path = _normalize_path(path)
        return any(
            normalized_path == exempt.rstrip("/") or normalized_path.startswith(f"{exempt.rstrip('/')}/")
            for exempt in self.exempt_paths
        )

    def _get_request_limit(self, method: str, path: str) -> int:
        for template, methods, limit in self.route_limits:
            if method in methods and _path_matches_template(path, template):
                return limit
        return self.max_requests

    def _get_bucket_id(self, method: str, path: str) -> str:
        for template, methods, _ in self.route_limits:
            if method in methods and _path_matches_template(path, template):
                return f"{method}:{_normalize_path(template)}"
        return f"{method}:default"

    def _client_identifier(self, scope: Scope) -> str:
        client = scope.get("client")
        if client:
            host = client[0]
            if host:
                return host

        return "unknown"

    def _cleanup(self, now: float) -> None:
        if now - self._last_cleanup < self.window_seconds:
            return

        cutoff = now - self.window_seconds
        stale_keys: list[str] = []

        for key, timestamps in self._requests.items():
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if not timestamps:
                stale_keys.append(key)

        for key in stale_keys:
            del self._requests[key]

        self._last_cleanup = now

    def _register_request(
        self, client_id: str, now: float, limit: int
    ) -> tuple[bool, int, int, int]:
        timestamps = self._requests.setdefault(client_id, deque())
        cutoff = now - self.window_seconds

        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

        if len(timestamps) >= limit:
            reset_at = int(timestamps[0] + self.window_seconds)
            retry_after = max(1, reset_at - int(now))
            return False, 0, reset_at, retry_after

        timestamps.append(now)
        remaining = max(0, limit - len(timestamps))
        reset_at = int(timestamps[0] + self.window_seconds)
        return True, remaining, reset_at, 0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        path = scope.get("path", "")

        if method == "OPTIONS" or self._is_exempt(path):
            await self.app(scope, receive, send)
            return

        request_limit = self._get_request_limit(method, path)
        bucket_id = self._get_bucket_id(method, path)
        client_id = self._client_identifier(scope)
        now = time.monotonic()

        async with self._lock:
            self._cleanup(now)
            allowed, remaining, reset_at, retry_after = self._register_request(
                f"{client_id}:{bucket_id}", now, request_limit
            )

        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "limit": request_limit,
                    "window_seconds": self.window_seconds,
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(request_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                },
            )
            await response(scope, receive, send)
            return

        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-RateLimit-Limit"] = str(request_limit)
                headers["X-RateLimit-Remaining"] = str(remaining)
                headers["X-RateLimit-Reset"] = str(reset_at)
            await send(message)

        await self.app(scope, receive, send_with_headers)
