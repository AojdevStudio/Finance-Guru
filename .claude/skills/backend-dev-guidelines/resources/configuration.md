<!-- v2.0 | 2025-10-30 -->
# Configuration Management - Pydantic Settings

Complete guide to managing backend configuration in the Unified Dental FastAPI stack using `pydantic-settings`.

> Migration Note: Replace all usages of `config.ini`, dotenv parsing, and ad-hoc `process.env` reads with the Pydantic settings architecture described here. The authoritative implementation lives in `backend/app/core/config.py`.

## Table of Contents

- [Why Pydantic Settings?](#why-pydantic-settings)
- [Settings Architecture](#settings-architecture)
- [Environment Loading Flow](#environment-loading-flow)
- [Runtime Usage](#runtime-usage)
- [Overriding for Tests](#overriding-for-tests)
- [Secrets Management](#secrets-management)
- [Migration Checklist](#migration-checklist)
- [Anti-Patterns](#anti-patterns)
- [Quick Reference](#quick-reference)

---

## Why Pydantic Settings?

Legacy Node services relied on `process.env` + INI files, leading to unvalidated configuration and runtime surprises. Pydantic settings provides:

- ✅ Type safety: every config value has an explicit type
- ✅ Validation at import time (fail fast on missing or invalid values)
- ✅ Nested models, defaults, and transformations via validators
- ✅ Convenient `.env` loading for local development
- ✅ Easy overrides for tests, scripts, and CLI tooling

---

## Settings Architecture

All backend configuration flows through `backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    APP_NAME: str = "Unified Dental Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str
    FROM_NAME: str = "Unified Dental"

    CORS_ORIGINS: list[str] = ["http://localhost:8080", "http://localhost:5173"]
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_PER_MINUTE: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
```

**Key points**
- Inherit from `BaseSettings` to gain automatic env variable parsing.
- Document every variable with a comment or docstring near the definition.
- Provide sane defaults for local development (e.g., `redis://localhost:6379/0`).
- Use validators to normalize free-form inputs (CORS origins, comma-delimited lists).

---

## Environment Loading Flow

Loading precedence mirrors Supabase infrastructure expectations:

1. **Environment variables** – injected via deployment platform (Railway, Fly.io, etc.).
2. **`.env` file** – for local development only (git-ignored).
3. **Defaults** – defined directly on the `Settings` class for non-secret values.

No `config.ini` or JSON files are used; any static configuration should be embedded as defaults or pulled from environment variables.

### `.env` Example (local only)

```
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/unifiedental
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=anon-key
SUPABASE_SERVICE_KEY=service-role-key
SMTP_USER=admin@unifiedental.com
SMTP_PASSWORD=dev-password
FROM_EMAIL=admin@unifiedental.com
```

> 🔒 **Security**: Never commit `.env`. `.gitignore` already excludes it.

---

## Runtime Usage

- Import the singleton `settings` wherever configuration is required.
- Avoid instantiating new `Settings()` instances outside of tests.

```python
from app.core.config import settings

DATABASE_URL = settings.DATABASE_URL
if settings.DEBUG:
    logger.info("Running in debug mode")

engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG)
```

**Never** read environment variables directly (`os.getenv`, `os.environ`). Centralization ensures validation and makes testing straightforward.

---

## Overriding for Tests

Pydantic settings provide `model_copy(update={...})` for scoped overrides:

```python
from app.core.config import Settings, settings


def test_custom_rate_limit(monkeypatch):
    override = settings.model_copy(update={"RATE_LIMIT_PER_MINUTE": 5})
    monkeypatch.setattr("app.core.config.settings", override)

    assert settings.RATE_LIMIT_PER_MINUTE == 5
```

Alternatively, fixtures can patch environment variables before importing the module:

```python
@pytest.fixture(autouse=True)
def load_test_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db")
    # Reload settings if necessary
    from importlib import reload
    from app.core import config
    reload(config)
```

Avoid direct reassignment of `settings = Settings(...)` in application code; use dependency overrides or environment manipulation in tests.

---

## Secrets Management

- Production secrets live exclusively in environment variables (managed by platform secret stores).
- Do not commit `.env` or embed secrets in code.
- For local development, `dotenv`-style secrets are acceptable if they remain git-ignored.
- Rotate Supabase service keys and SMTP credentials periodically; configuration changes should be documented in release notes.

### Optional Secret Files

If a service requires certificate files (e.g., `service-account.json`), store them outside the repo and load paths via environment variables. Do **not** extend settings to read arbitrary files from disk unless absolutely necessary.

---

## Migration Checklist

1. **Search for direct env usage**
    ```bash
    rg "os\.getenv" backend/app
    rg "os\.environ" backend/app
    ```
2. **Replace with `settings`**
    ```python
    # Before
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # After
    from app.core.config import settings
    redis_url = settings.REDIS_URL
    ```
3. **Add missing fields** to `Settings` with appropriate defaults and documentation.
4. **Update `.env.example`** (if maintained) to reflect new variables.
5. **Regenerate documentation** (this file) when the settings structure changes.

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|--------------|--------------|-----|
| `os.getenv` scattered in code | No validation, difficult to test | Import `settings` and use typed fields |
| Instantiating `Settings()` in multiple modules | Bypasses overrides, inconsistent state | Use the shared `settings` instance |
| Loading INI/JSON config files | Adds complexity, duplicates env management | Stick to environment variables + defaults |
| Embedding secrets in code/defaults | Security risk | Use environment variables and secret stores |
| Mutating `settings` at runtime | Breaks import-time guarantees | Adjust environment before import or use monkeypatch in tests |

---

## Quick Reference

- Configuration lives in `app/core/config.py`; import `settings` everywhere.
- Defaults exist for developer ergonomics; production depends on env vars.
- Validators normalize complex fields (CORS origins, lists, comma-separated strings).
- Override settings for tests via environment variables or `model_copy(update=...)`.
- Document new config keys in this guide and keep `.env.example` (if used) in sync.

---

**Related Files:**
- backend/app/core/config.py
- backend/app/core/database.py
- backend/app/core/redis.py
- docs/architecture/project-structure.md
