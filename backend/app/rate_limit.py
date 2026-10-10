import threading
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request

from app.auth import get_current_user
from app.schemas import User


class SlidingWindowLimiter:
    """In-memory sliding-window counter. State is per process, so with several
    workers/instances each one enforces its own limit; use a shared store (e.g. Redis)
    if that matters."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> int | None:
        """Record a hit. Returns None if allowed, else seconds until the next slot frees up."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= now - window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                return max(1, int(hits[0] + window_seconds - now) + 1)
            hits.append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()


def _enforce(key: str, limit: int, window_seconds: int) -> None:
    retry_after = limiter.check(key, limit, window_seconds)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please slow down and try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def _client_ip(request: Request) -> str:
    # Behind a reverse proxy this is the proxy's address; run uvicorn with
    # --proxy-headers/--forwarded-allow-ips so request.client reflects the real client.
    return request.client.host if request.client else "unknown"


def limit_by_ip(name: str, limit: int, window_seconds: int):
    def dependency(request: Request) -> None:
        _enforce(f"{name}:ip:{_client_ip(request)}", limit, window_seconds)

    return dependency


def limit_by_user(name: str, limit: int, window_seconds: int):
    def dependency(request: Request, user: User = Depends(get_current_user)) -> User:
        _enforce(f"{name}:user:{user.id}", limit, window_seconds)
        return user

    return dependency
