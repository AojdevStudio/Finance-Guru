<!-- v2.0 | 2025-10-30 -->
# Testing Guide - pytest + httpx Strategy

Complete guide to testing the Unified Dental FastAPI backend using pytest, pytest-asyncio, and httpx.

> Migration Note: Jest/Supertest patterns have been replaced by Python-native tooling. Follow this guide when authoring new tests or migrating existing coverage.

## Table of Contents

- [Test Stack Overview](#test-stack-overview)
- [Project Commands](#project-commands)
- [Unit Testing Patterns](#unit-testing-patterns)
- [Integration & API Tests](#integration--api-tests)
- [Mocking & Fixtures](#mocking--fixtures)
- [Database Strategies](#database-strategies)
- [Testing Authenticated Routes](#testing-authenticated-routes)
- [Coverage Targets](#coverage-targets)
- [Anti-Patterns](#anti-patterns)
- [Quick Reference](#quick-reference)

---

## Test Stack Overview

| Concern | Tool |
|---------|------|
| Test runner | `pytest` |
| Async support | `pytest-asyncio` |
| HTTP client | `httpx.AsyncClient` (with `ASGITransport`) |
| Mocking | `pytest-mock` (`mocker` fixture), `unittest.mock.AsyncMock` |
| Factories/fixtures | Pytest fixtures (`conftest.py`) |

Tests live under `backend/app/tests/` mirroring the app structure.

---

## Project Commands

```bash
# Run entire suite
cd backend
uv run pytest

# Run with markers (e.g., integration)
uv run pytest -m integration

# Run with coverage
uv run pytest --cov=app --cov-report=term-missing
```

Add new dependencies to `pyproject.toml` (`[tool.uv]` section) if fixtures require additional packages.

---

## Unit Testing Patterns

Unit tests focus on service logic and utilities without touching FastAPI routing.

```python
import pytest
from unittest.mock import AsyncMock

from app.services.user_service import DuplicateEmailError, UserService


@pytest.mark.asyncio
async def test_create_user_rejects_duplicates():
    repo = AsyncMock()
    repo.email_exists.return_value = True
    service = UserService(repository=repo)

    with pytest.raises(DuplicateEmailError):
        await service.create(UserCreate(email="user@example.com", supabase_id="abc"))


@pytest.mark.asyncio
async def test_create_user_persists_record():
    repo = AsyncMock()
    repo.email_exists.return_value = False
    repo.create.return_value = {"id": "123"}

    service = UserService(repository=repo)
    result = await service.create(UserCreate(email="user@example.com", supabase_id="abc"))

    repo.create.assert_awaited_once()
    assert result["id"] == "123"
```

- Prefer `AsyncMock` for async collaborators.
- Use fixtures to construct services with shared defaults.

---

## Integration & API Tests

API tests exercise FastAPI routes with dependency overrides.

```python
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_get_current_user(test_client: AsyncClient, mocker):
    mock_user = User(id="123", email="user@example.com")
    mocker.patch("app.middleware.supabase_auth.get_current_user", return_value=mock_user)

    response = await test_client.get("/api/users/me")
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"
```

- Use `app.dependency_overrides` to supply fake services or sessions during tests.
- Mark heavier scenarios with `@pytest.mark.integration` for selective execution.

### Example dependency override

```python
@pytest.fixture
def override_user_service(mocker):
    fake_service = mocker.AsyncMock()
    fake_service.create.return_value = {"id": "1", "email": "user@example.com"}
    app.dependency_overrides[get_user_service] = lambda: fake_service
    yield fake_service
    app.dependency_overrides.clear()
```

---

## Mocking & Fixtures

- Use the built-in `mocker` fixture (pytest-mock) for patching modules.
- For contextvars or request-scoped state, create helper fixtures that set up the context before exercising code.
- Group shared fixtures in `backend/app/tests/conftest.py`.

Example fixture for database session:

```python
@pytest.fixture
async def test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session
```

---

## Database Strategies

- **Unit tests**: prefer mocks; do not hit the real database.
- **Integration tests**: use in-memory SQLite or a dedicated Postgres schema.
- Wrap tests in transactions and roll back between cases when using Postgres.
- Seed data via fixtures; avoid brittle global state.

Example transactional pattern:

```python
@pytest.fixture
async def transactional_session(test_session):
    async with test_session.begin():
        yield test_session
        await test_session.rollback()
```

---

## Testing Authenticated Routes

- Override Supabase auth dependencies to simulate authenticated users.
- Set request headers using httpx `.get(..., headers={"Authorization": "Bearer test"})` if middleware inspects headers.
- For token verification logic, parameterize fixtures with valid/invalid JWT payloads.

```python
@pytest.fixture
def mock_admin_user(mocker):
    mock_user = User(id="admin", email="user@example.com", role="admin")
    mocker.patch("app.middleware.supabase_auth.get_current_admin_user", return_value=mock_user)
```

---

## Coverage Targets

- **Unit tests**: ≥ 70% statements for service modules.
- **Integration tests**: cover critical API paths (users, auth, Supabase sync flows).
- **Background jobs**: at least one test per Celery task or scheduler callback.

Run coverage:

```bash
uv run pytest --cov=app --cov-report=term-missing
```

Ensure coverage thresholds are enforced in CI before merging.

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|--------------|--------------|-----|
| Hitting external APIs in tests | Flaky, slow | Mock with `mocker.patch` / httpx MockTransport |
| Instantiating FastAPI app per test | Expensive, inconsistent | Import the shared `app` instance |
| Sharing mutable fixture state | Tests bleed data | Use fresh fixtures or deepcopy payloads |
| Skipping async markers | Tests run sync, never await | Apply `@pytest.mark.asyncio` or `pytest_asyncio.fixture` |
| Hard-coding Supabase tokens | Security risk, brittle | Mock auth dependencies and payloads |

---

## Quick Reference

- Tests execute via `uv run pytest` from `backend/`.
- Use `pytest-asyncio` markers for async code; rely on `httpx.AsyncClient` for API tests.
- Mock services/repositories with `AsyncMock` or dependency overrides.
- Prefer fixtures in `conftest.py` for shared setup (sessions, clients, fake users).
- Keep coverage high on business-critical paths; run `--cov` locally and in CI.

---

**Related Files:**
- backend/app/tests/
- backend/app/main.py
- backend/app/services/
- docs/architecture/project-structure.md
