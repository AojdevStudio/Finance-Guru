<!-- v2.0 | 2025-10-30 -->
# Sentry & Observability - FastAPI + Loguru

Complete guide to error tracking, performance monitoring, and logging for the Unified Dental backend using `sentry-sdk` and Loguru.

> Migration Note: Replace all Node-specific `@sentry/node` patterns with the Python SDK demonstrated here. Bootstrapping lives in `backend/app/main.py` and `backend/app/core/logging.py`.

## Table of Contents

- [Why Observability Matters](#why-observability-matters)
- [Sentry Initialization](#sentry-initialization)
- [Capturing Errors](#capturing-errors)
- [Performance & Tracing](#performance--tracing)
- [Background Jobs & Cron Tasks](#background-jobs--cron-tasks)
- [Loguru Integration](#loguru-integration)
- [Context & PII Hygiene](#context--pii-hygiene)
- [Testing & Local Verification](#testing--local-verification)
- [Anti-Patterns](#anti-patterns)
- [Quick Reference](#quick-reference)

---

## Why Observability Matters

- **Single source of truth**: All production exceptions must flow into Sentry.
- **Faster triage**: Breadcrumbs, request metadata, and tags accelerate root-cause analysis.
- **Compliance**: Structured logging via Loguru and PII scrubbing in Sentry ensures HIPAA-adjacent hygiene.

Every new service, job, or script must initialize Sentry **before** importing modules that may raise errors.

---

## Sentry Initialization

Place initialization inside `app/main.py` (before router inclusion):

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.core.config import settings


def init_sentry() -> None:
    if settings.APP_ENV == "development" or not settings.SENTRY_DSN:
        return

    sentry_logging = LoggingIntegration(
        level=settings.LOG_LEVEL,
        event_level="ERROR",
    )

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.APP_ENV,
        release=settings.API_VERSION,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        integrations=[
            FastApiIntegration(transaction_style="url"),
            SqlalchemyIntegration(),
            sentry_logging,
        ],
        before_send=mask_sensitive_data,
    )


def mask_sensitive_data(event, hint):
    request = event.get("request") or {}
    headers = request.get("headers") or {}
    headers.pop("authorization", None)
    headers.pop("cookie", None)
    request["headers"] = headers
    event["request"] = request

    if user := event.get("user"):
        email = user.get("email")
        if email:
            user["email"] = email[:2] + "***" + email.split("@", 1)[-1]
        event["user"] = user
    return event
```

Call `init_sentry()` inside the FastAPI lifespan startup **before** scheduling background tasks.

### Settings Additions

Extend `Settings` with:

```python
SENTRY_DSN: str | None = None
SENTRY_TRACES_SAMPLE_RATE: float = 0.1
SENTRY_PROFILES_SAMPLE_RATE: float = 0.05
```

Set DSN in production and optionally in staging; leave unset in development to disable Sentry.

---

## Capturing Errors

- **FastAPI handlers**: rely on global exception handlers (see `app/core/errors.py`). Sentry automatically records unhandled exceptions.
- **Services**: raise domain errors; routers translate to HTTP responses while Sentry captures via exception handlers.
- **Manual capture**: useful when logging a non-fatal event.

```python
from sentry_sdk import capture_exception, push_scope


def log_business_error(error: Exception, *, user_id: str, context: dict[str, object]) -> None:
    with push_scope() as scope:
        scope.set_tag("feature", "supabase-sync")
        scope.set_extra("business_context", context)
        scope.user = {"id": user_id}
        capture_exception(error)
```

Avoid wrapping every `try`/`except` with `capture_exception`; rely on centralized handlers unless extra metadata is necessary.

---

## Performance & Tracing

Sentry’s FastAPI integration automatically creates transactions per request. Add custom spans for critical workflows:

```python
from sentry_sdk import start_span


async def reconcile_supabase_user(user_id: str) -> None:
    with start_span(op="sync.reconcile", description="Supabase user sync") as span:
        span.set_tag("user.id", user_id)
        profile = await fetch_profile(user_id)
        await update_local_state(profile)
```

- Use spans for DB-heavy operations, external API calls, or complex business logic.
- Leverage `SqlalchemyIntegration` for automatic query breadcrumbs and slow query detection.

---

## Background Jobs & Cron Tasks

For Celery workers, run Sentry initialization at process start (inside `celery.py`). Example:

```python
from celery import Celery

celery_app = Celery("unifiedental")


@celery_app.on_after_configure.connect
def configure_sentry(sender, **kwargs):
    init_sentry()
```

For standalone scripts or cron tasks:

```python
#!/usr/bin/env python
from app.main import init_sentry


def main() -> None:
    init_sentry()
    with start_span(op="cron.job", description="nightly-sync"):
        run_sync()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        capture_exception(exc)
        raise
```

Ensure DSN and environment variables are available to worker containers.

---

## Loguru Integration

`app/core/logging.py` configures Loguru to write structured logs and forward errors to Sentry:

```python
from loguru import logger


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        backtrace=settings.DEBUG,
        diagnose=settings.DEBUG,
        format="{time} | {level} | {message} | {extra}",
    )
```

Use `logger.bind()` to attach context without leaking PII:

```python
logger.bind(user_id=user.id, path=request.url.path).info("request.completed")
```

Loguru output complements Sentry breadcrumbs; keep logging levels consistent so the LoggingIntegration can translate log records into Sentry events.

---

## Context & PII Hygiene

- Always scrub secrets (tokens, passwords) before logging.
- Use Sentry `before_send` hook to sanitize headers and mask emails.
- Tag Sentry events with `service`, `environment`, and `feature` for dashboards.
- Add breadcrumbs sparingly to avoid noise; use categories like `db`, `external_api`, `business`.

Example PII-safe breadcrumb:

```python
from sentry_sdk import add_breadcrumb

add_breadcrumb(
    category="supabase",
    message="Sync triggered",
    level="info",
    data={"table": "profiles", "records": len(records)},
)
```

---

## Testing & Local Verification

1. **Local smoke test**: set `SENTRY_DSN` to a test project and hit `/api/health`. Confirm event appears in Sentry.
2. **Unit test**: monkeypatch `sentry_sdk.capture_exception` to assert it is called.

```python
def test_capture_exception_called(mocker):
    capture = mocker.patch("sentry_sdk.capture_exception")
    try:
        raise ValueError("boom")
    except ValueError as exc:
        log_business_error(exc, user_id="123", context={})
    capture.assert_called_once()
```

3. **Integration test**: use `httpx.AsyncClient` to trigger a handler that raises and verify a 500 response with `X-Request-ID` header (ensuring middleware executed).

---

## Anti-Patterns

| Anti-Pattern | Why It Hurts | Fix |
|--------------|--------------|-----|
| Initializing Sentry after importing app modules | Misses startup errors | Call `init_sentry()` before other imports in scripts/workers |
| Capturing every exception manually | Duplicates events, noisy | Rely on global handlers; add scope only when extra context is required |
| Logging secrets or raw tokens | Security liability | Scrub via `before_send`, avoid logging secrets entirely |
| Disabling Sentry in staging | Missing regressions | Keep DSN configured; adjust sample rates instead |
| Creating multiple Sentry clients | Fragmented traces | Use module-level initialization once per process |

---

## Quick Reference

- Initialize Sentry in `init_sentry()`, call during app startup and worker bootstrap.
- Configure DSN and sample rates via Pydantic settings (`SENTRY_*` fields).
- Use Loguru for structured logs; integrate with Sentry via `LoggingIntegration`.
- Leverage spans for long-running operations and add breadcrumbs for business context.
- Sanitize PII via `before_send` and disciplined logging practices.

---

**Related Files:**
- backend/app/main.py
- backend/app/core/config.py
- backend/app/core/logging.py
- backend/app/core/errors.py
- docs/architecture/project-structure.md
