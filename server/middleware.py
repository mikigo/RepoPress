from __future__ import annotations
import time
import logging
from collections import defaultdict
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

from config import settings

logger = logging.getLogger("repopress")

# Rate limiting state
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60  # seconds


def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    timestamps = _rate_limit_store[ip]
    # Keep only timestamps within the window
    timestamps[:] = [t for t in timestamps if t > window_start]
    if len(timestamps) >= RATE_LIMIT_MAX:
        return True
    timestamps.append(now)
    return False


async def _verify_jwt(request: Request) -> dict | None:
    """Verify JWT token from Authorization header. Returns payload dict or None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


class RateLimitMiddleware:
    """Rate limiting middleware applied selectively to login endpoint."""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        if request.url.path == "/api/auth/login" and request.method == "POST":
            ip = request.client.host if request.client else "unknown"
            if _is_rate_limited(ip):
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Too many login attempts. Try again later."},
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


class RequestLoggingMiddleware:
    """Middleware to log all requests."""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.time()
        request = Request(scope, receive)

        async def _send(message):
            if message["type"] == "http.response.start":
                elapsed = time.time() - start
                logger.info(
                    "%s %s -> %s (%.2fms)",
                    request.method,
                    request.url.path,
                    message["status"],
                    elapsed * 1000,
                )
            await send(message)

        await self.app(scope, receive, _send)


class JWTAuthMiddleware:
    """Extract JWT and attach user info to request.state.user."""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        path = request.url.path

        # Skip auth for login, docs/openapi, and static
        public_paths = [
            "/api/auth/login",
            "/api/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]
        if any(path.startswith(p) for p in public_paths):
            await self.app(scope, receive, send)
            return

        payload = await _verify_jwt(request)
        if payload is None and path.startswith("/api/"):
            response = JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )
            await response(scope, receive, send)
            return

        # Store user info in scope for later use
        if payload:
            scope["user"] = {
                "id": payload.get("sub"),
                "username": payload.get("username"),
            }

        await self.app(scope, receive, send)


def setup_middleware(app: FastAPI):
    """Configure all middleware on the FastAPI app."""
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware order: outermost first
    # Rate limit -> JWT auth -> Request logging -> App
    app.add_middleware(RateLimitMiddleware)  # type: ignore[arg-type]
    app.add_middleware(JWTAuthMiddleware)  # type: ignore[arg-type]
    app.add_middleware(RequestLoggingMiddleware)  # type: ignore[arg-type]
