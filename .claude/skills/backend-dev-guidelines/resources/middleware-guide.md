<!-- v2.0 | 2025-10-30 -->
# Middleware Guide - FastAPI & Starlette Patterns

Complete reference for composing middleware and dependencies in the Unified Dental FastAPI backend.

> Migration Note: Express `app.use()` chains and AsyncLocalStorage helpers have been replaced by Starlette-compatible middleware classes, FastAPI dependency injection, and contextvars-based state. Use the patterns below when adding cross-cutting concerns.

## Table of Contents

- [Middleware Stack Overview](#middleware-stack-overview)
- [Global Middleware Registration](#global-middleware-registration)
- [Authentication & Authorization](#authentication--authorization)
- [Request Context & Audit Trail](#request-context--audit-trail)
- [Error Handling](#error-handling)
- [CORS, Compression & Security Headers](#cors-compression--security-headers)
- [Instrumenting Requests](#instrumenting-requests)
- [Testing Middleware](#testing-middleware)
- [Anti-Patterns](#anti-patterns)
- [Quick Reference](#quick-reference)

---

## Middleware Stack Overview

FastAPI builds on Starlette’s ASGI middleware model. Middleware can be registered either via `app.add_middleware(...)` (class-based, wraps the entire request/response lifecycle) or `@app.middleware("http")` (function-based wrappers). Dependency injection (`Depends`) is preferred for per-route concerns such as authentication and authorization.

```
ASGI app entry
  ├─ Starlette middleware (registered with app.add_middleware)
  │    ├─ TrustedHostMiddleware
  │    ├─ GZipMiddleware
  │    └─ CORSMiddleware (registered first → outermost)
  ├─ Function middleware (@app.middleware("http"))
  │    └─ Audit logging wrapper
  ├─ FastAPI routing (APIRouter path operations)
  │    └─ Dependencies injected via Depends (auth, db session, services)
  └─ Exception handlers (registered after routers)
```

**Key rules**
- `app.add_middleware` composes a stack where the **last registered middleware runs first** on incoming requests.
- Function middleware executes in declaration order and is ideal for simple request/response wrappers.
- Middleware should not contain business logic; delegate to services or dependencies.

---

## Global Middleware Registration

Centralize global middleware configuration in `app/main.py`.

```python
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.middleware.request_context import RequestContextMiddleware


def configure_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://unifiedental.com", "https://portal.unifiedental.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["unifiedental.com", "portal.unifiedental.com", "localhost"],
    )
    app.add_middleware(RequestContextMiddleware)  # closest to handlers


configure_middleware(app)
```

Register middleware from outermost (CORS) to innermost (context) for clarity.

---

## Authentication & Authorization

FastAPI dependencies replace most Express auth middleware. The Supabase auth helpers live in `app/middleware/supabase_auth.py` and are injected per-route:

```python
@router.get("/admin", dependencies=[Depends(get_current_admin_user)])
async def admin_dashboard(...):
    ...
```

**When to use middleware classes instead of dependencies:**
- Request inspection that applies to **all** endpoints (e.g., security headers, request ID propagation).
- Compatibility with ASGI tooling (Sentry request handler, logging instrumentation).

Avoid storing request-specific state on the FastAPI app. Use dependency-scoped values (`Depends(get_current_user)`) or contextvars (see below).

---

## Request Context & Audit Trail

To replicate AsyncLocalStorage behavior, rely on ASGI middleware + `contextvars`. A minimal pattern lives in `app/middleware/request_context.py`:

```python
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware


request_context: ContextVar[dict[str, object]] = ContextVar("request_context", default={})


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        context = {
            "request_id": request.headers.get("x-request-id", str(uuid.uuid4())),
            "path": request.url.path,
        }
        token = request_context.set(context)
        try:
            response = await call_next(request)
        finally:
            request_context.reset(token)
        response.headers["X-Request-ID"] = context["request_id"]
        return response


def get_request_context() -> dict[str, object]:
    return request_context.get()
```

Services can call `get_request_context()` to retrieve the current audit context without threading values through every function.

---

## Error Handling

Exception handlers supersede Express-style error middleware. See `app/core/errors.py` for concrete implementations.

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    payload = ErrorResponse(
        message="Validation failed",
        validation_errors=[ErrorDetail.model_validate(err) for err in exc.errors()],
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload.model_dump())
```

**Guidance**
- Register exception handlers **after** routers to ensure they wrap the entire routing stack.
- Do not raise `HTTPException` inside middleware; raise domain-specific errors in services and translate in routers or global handlers.
- For Sentry, use middleware provided by the SDK (`sentry_sdk.init(FastApiIntegration())`) rather than custom wrappers.

---

## CORS, Compression & Security Headers

Centralize cross-cutting HTTP concerns:

| Concern | Middleware | Location |
|---------|------------|----------|
| CORS policy | `CORSMiddleware` | `configure_middleware` in `app/main.py` |
| Compression | `GZipMiddleware` | Enabled globally (watch out for streaming responses) |
| Trusted hosts | `TrustedHostMiddleware` | Blocks requests from unknown domains |
| Response headers | Custom `BaseHTTPMiddleware` | e.g., add `Strict-Transport-Security` |

Example security header middleware:

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        return response
```

Always register security middleware **after** CORS so headers apply to the final response.

---

## Instrumenting Requests

Leverage middleware for tracing/logging while keeping business logic elsewhere.

```python
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.bind(
            path=request.url.path,
            method=request.method,
            duration_ms=f"{duration_ms:.2f}",
        ).info("request.completed")
        response.headers["X-Process-Time"] = f"{duration_ms:.0f}ms"
        return response
```

Integrate with Sentry by enabling the FastAPI integration. For metrics, wrap `call_next` with additional logic to emit to Prometheus, DataDog, etc.

---

## Testing Middleware

Middleware should be tested at two levels:

1. **Unit tests** for custom middleware classes using Starlette’s `RequestFactory` and `ASGIApp` stubs.

```python
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient


def test_security_headers_middleware():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/")
    async def root():
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/")
    assert resp.headers["Strict-Transport-Security"].startswith("max-age")
```

2. **Integration tests** using httpx `AsyncClient` with dependency overrides to ensure middleware and routers cooperate correctly.

```python
@pytest.mark.asyncio
async def test_request_context_is_set(async_client: AsyncClient):
    response = await async_client.get("/api/users/me")
    assert "X-Request-ID" in response.headers
```

---

## Anti-Patterns

| Anti-Pattern | Why It Hurts | Fix |
|--------------|--------------|-----|
| Recreating AsyncSession inside middleware | Bypasses dependency injection, leaks connections | Use `Depends(get_db)` within routers/services |
| Performing business logic inside middleware | Blurs responsibility, hard to test | Move to services or dependencies |
| Using global mutable state instead of contextvars | Breaks concurrency, leaks data across requests | Use `ContextVar` or request-scoped dependencies |
| Registering error handlers as middleware | Starlette expects exception handlers via `app.add_exception_handler` | Use FastAPI exception handler APIs |
| Misordering middleware (security inside GZip, etc.) | Leads to missing headers or bypassed checks | Register in the documented order, closest to handlers last |

---

## Quick Reference

- Use `app.add_middleware` for ASGI-compatible classes (CORS, GZip, security headers).
- Use dependencies (`Depends`) for auth/authorization logic tied to specific routes.
- Prefer contextvars for request context; avoid thread-local or global state.
- Register exception handlers for validation, domain errors, and unhandled exceptions rather than error middleware.
- Test middleware with Starlette’s TestClient and httpx to guarantee behavior under the ASGI stack.

---

**Related Files:**
- backend/app/main.py
- backend/app/middleware/request_context.py
- backend/app/middleware/supabase_auth.py
- backend/app/core/errors.py
- docs/architecture/project-structure.md
