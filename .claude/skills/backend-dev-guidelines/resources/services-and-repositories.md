<!-- v2.0 | 2025-10-30 -->
# Services and Repositories - Business Logic Layer

Complete guide to structuring business logic with FastAPI services and async SQLAlchemy repositories.

> Migration Note: Replace all legacy Prisma/TypeScript service patterns with the FastAPI + SQLAlchemy architecture documented here. Services own business rules; repositories encapsulate async database access against Supabase PostgreSQL.

## Table of Contents

- [Service Layer Overview](#service-layer-overview)
- [Dependency Injection Pattern](#dependency-injection-pattern)
- [Repository Pattern](#repository-pattern)
- [Transaction Management](#transaction-management)
- [Service Design Principles](#service-design-principles)
- [Caching Strategies](#caching-strategies)
- [Testing Services](#testing-services)
- [Anti-Patterns](#anti-patterns)
- [Quick Reference](#quick-reference)

---

## Service Layer Overview

**Services answer business questions**. Controllers ask “should this happen?”; services decide “yes/no, and here’s how”. Repositories execute the data operations that make it real.

**Responsibilities:**
- ✅ Enforce business rules and invariants (e.g., Supabase role policies)
- ✅ Coordinate repositories, external APIs (Supabase, Redis, Celery) and domain events
- ✅ Own transaction and retry boundaries
- ✅ Translate domain errors (`DuplicateEmailError`, `PermissionDeniedError`)

**Out of scope:**
- ❌ HTTP shapes (`Request`, `Response`, query/body parsing)
- ❌ Raw SQLAlchemy session management (handled by dependency providers)
- ❌ JSON serialization (Pydantic response models do that)

### Example Service (`backend/app/services/user_service.py` blueprint)

```python
"""Business rules for user management."""

from __future__ import annotations

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class DuplicateEmailError(Exception):
    """Raised when attempting to create a user with an existing email address."""


class UserNotFoundError(Exception):
    """Raised when a user lookup fails."""


class UserService:
    """Coordinates repository operations with Unified Dental business rules."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create(self, payload: UserCreate) -> User:
        if await self.repository.email_exists(payload.email):
            raise DuplicateEmailError("Email already registered")

        return await self.repository.create(payload)

    async def update(self, user_id: str, payload: UserUpdate) -> User:
        user = await self.repository.update(user_id, payload)
        if not user:
            raise UserNotFoundError(user_id)
        return user

    async def deactivate(self, user_id: str) -> None:
        deleted = await self.repository.soft_delete(user_id)
        if not deleted:
            raise UserNotFoundError(user_id)

    def to_schema(self, user: User) -> UserResponse:
        """Utility helper so routers can emit Pydantic responses effortlessly."""

        return UserResponse.model_validate(user, from_attributes=True)
```

The service returns Pydantic models for consistency with the routing layer but never imports FastAPI. Domain errors bubble up for translation to HTTP status codes by routers or global handlers.

---

## Dependency Injection Pattern

FastAPI’s dependency system builds the service stack one layer at a time. Compose dependencies from infrastructure → repository → service.

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


def get_session() -> AsyncSession:
    return Depends(get_db)  # request-scoped AsyncSession


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)
```

### Using Services in Routers

```python
from fastapi import APIRouter, Depends, HTTPException, status

from app.middleware.supabase_auth import get_current_admin_user
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(
    payload: UserCreate,
    _: None = Depends(get_current_admin_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        user = await service.create(payload)
    except DuplicateEmailError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return service.to_schema(user)
```

Testing uses `app.dependency_overrides[get_user_service]` to inject fakes without patching internals.

---

## Repository Pattern

Repositories abstract SQLAlchemy operations so services stay ORM-agnostic. They receive a request-scoped `AsyncSession` and expose targeted async methods.

```python
"""Async repository for user operations."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """Wraps AsyncSession calls for user persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def email_exists(self, email: str) -> bool:
        stmt = select(User.id).where(User.email == email)
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    async def create(self, payload: UserCreate) -> User:
        user = User(**payload.model_dump())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: str, payload: UserUpdate) -> User | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**payload.model_dump(exclude_unset=True))
            .returning(User)
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            await self.session.rollback()
        else:
            await self.session.commit()
        return record

    async def soft_delete(self, user_id: str) -> bool:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
            .returning(User.id)
        )
        result = await self.session.execute(stmt)
        if result.scalar_one_or_none() is None:
            await self.session.rollback()
            return False
        await self.session.commit()
        return True
```

**Repository Guidelines:**
- Keep methods laser-focused (no business rules)
- Use typed payloads (`UserCreate`, `UserUpdate`) instead of raw dicts
- Commit inside repositories unless the service orchestrates multi-repository transactions (see below)
- Use `.scalar_one_or_none()` to avoid row proxies leaking to services

---

## Transaction Management

Services should start transactions when orchestrating multiple repositories or external side-effects.

```python
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transactional_session(session: AsyncSession):
    try:
        async with session.begin():  # emits BEGIN/COMMIT
            yield
    except Exception:
        await session.rollback()
        raise


class BillingService:
    def __init__(self, session: AsyncSession, invoice_repo: InvoiceRepository, payment_repo: PaymentRepository):
        self.session = session
        self.invoice_repo = invoice_repo
        self.payment_repo = payment_repo

    async def settle_invoice(self, invoice_id: str) -> None:
        async with transactional_session(self.session):
            invoice = await self.invoice_repo.mark_paid(invoice_id)
            await self.payment_repo.capture(invoice)
```

Rules of thumb:
- Prefer `async with session.begin()` to ensure commit/rollback symmetry.
- When mixing repositories within a transaction, share the same `AsyncSession` instance.
- External side-effects (emails, Celery tasks) should happen **after** commits to avoid orphaned records.

---

## Service Design Principles

1. **Single Responsibility** – one bounded context per service.
2. **Explicit Inputs/Outputs** – type every parameter and return value.
3. **Raise Domain Errors** – never return sentinel values for exceptional cases.
4. **Composition Over Inheritance** – inject collaborators instead of subclassing.

```python
class WorkflowService:
    def __init__(self, *, workflow_repo: WorkflowRepository, audit_service: AuditService, notification_service: NotificationService) -> None:
        self.workflow_repo = workflow_repo
        self.audit_service = audit_service
        self.notification_service = notification_service

    async def start(self, payload: WorkflowStart) -> WorkflowSummary:
        workflow = await self.workflow_repo.create(payload)
        await self.audit_service.record_start(workflow.id)
        await self.notification_service.notify_manager(workflow.id)
        return workflow
```

Avoid god services that manipulate repositories, send emails, and log audits inline. Delegate to collaborators.

---

## Caching Strategies

Use caching sparingly and centralize invalidation rules.

### In-Memory TTL Cache

```python
import time
from collections.abc import Callable


class PreferenceService:
    """Caches Supabase profile preferences with a short TTL."""

    def __init__(self, repository: PreferenceRepository, ttl_seconds: int = 300) -> None:
        self.repository = repository
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[float, Preference]] = {}

    async def get_preferences(self, user_id: str) -> Preference:
        cached = self._cache.get(user_id)
        if cached and (time.time() - cached[0]) < self.ttl_seconds:
            return cached[1]

        preference = await self.repository.fetch(user_id)
        self._cache[user_id] = (time.time(), preference)
        return preference

    def invalidate(self, user_id: str) -> None:
        self._cache.pop(user_id, None)
```

### Redis / Shared Cache

When multiple workers need the same cache, wrap Redis interactions in a repository-like class and inject it into services. Keep TTLs short to respect Supabase data freshness.

---

## Testing Services

Testing relies on `pytest`, `pytest-asyncio`, and `AsyncMock`.

```python
import pytest
from unittest.mock import AsyncMock

from app.schemas.user import UserCreate
from app.services.user_service import DuplicateEmailError, UserService


@pytest.mark.asyncio
async def test_create_user_happy_path():
    repo = AsyncMock()
    repo.email_exists.return_value = False
    repo.create.return_value = {"id": "abc", "email": "admin@unifiedental.com", "is_active": True}

    service = UserService(repository=repo)

    payload = UserCreate(email="admin@unifiedental.com", role="admin")
    response = await service.create(payload)

    repo.email_exists.assert_awaited_once_with("admin@unifiedental.com")
    repo.create.assert_awaited_once()
    assert response.email == "admin@unifiedental.com"


@pytest.mark.asyncio
async def test_create_user_duplicate_email():
    repo = AsyncMock()
    repo.email_exists.return_value = True

    service = UserService(repository=repo)

    payload = UserCreate(email="admin@unifiedental.com", role="admin")
    with pytest.raises(DuplicateEmailError):
        await service.create(payload)
```

Integration tests override dependencies in FastAPI:

```python
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user_endpoint(app, async_client: AsyncClient, fake_service: UserService):
    app.dependency_overrides[get_user_service] = lambda: fake_service
    response = await async_client.post("/api/users", json={"email": "admin@unifiedental.com", "role": "admin"})
    assert response.status_code == 201
    app.dependency_overrides.clear()
```

---

## Anti-Patterns

| Anti-Pattern | Why It Hurts | Fix |
|--------------|-------------|-----|
| Service imports FastAPI models | Couples business logic to transport layer | Accept Pydantic schemas or domain DTOs instead |
| Repository returns raw row tuples | Leaks SQLAlchemy internals to services | Return ORM objects or typed DTOs |
| Service manages its own AsyncSession | Breaks dependency overrides and tests | Inject session via repository or helper |
| Broad `except Exception: pass` | Hides Supabase/SQL errors, corrupts state | Catch specific domain errors, re-raise |
| Shared mutable state without synchronization | Causes cache incoherence across workers | Use Redis or per-request scope |

---

## Quick Reference

- Services = business rules, repositories = data access.
- Compose dependencies: `AsyncSession` → repository → service → router.
- Prefer transactions when updating multiple tables.
- Raise domain-specific exceptions; translate to HTTP once.
- Use pytest + `AsyncMock` for unit tests; override dependencies for integration tests.

---

**Related Files:**
- backend/app/services/user_service.py
- backend/app/api/v1/users.py
- backend/app/core/database.py
- docs/architecture/project-structure.md
