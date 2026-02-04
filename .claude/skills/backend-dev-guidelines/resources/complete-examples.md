<!-- v2.0 | 2025-10-30 -->
# Complete Examples - FastAPI Feature Blueprint

End-to-end implementation example for a production-ready FastAPI module. Use this as a template when building new features in the Unified Dental backend.

> Migration Note: This replaces the Express controller/service/repository example. The new blueprint demonstrates schemas → repository → service → router → tests with dependency injection and observability hooks.

## Table of Contents

- [Feature Overview](#feature-overview)
- [Schemas (`app/schemas/user.py`)](#schemas-appschemasuserpy)
- [Repository (`app/repositories/user_repository.py`)](#repository-apprepositoriesuser_repositorypy)
- [Service (`app/services/user_service.py`)](#service-appservicesuser_servicepy)
- [Router (`app/api/v1/users.py`)](#router-appapiv1userspy)
- [Tests (`app/tests/api/test_users.py`)](#tests-apptestsapitest_userspy)
- [Background Task Hook](#background-task-hook)
- [Checklist & Next Steps](#checklist--next-steps)

---

## Feature Overview

Goal: Expose CRUD endpoints for practice users sourced from Supabase. Requirements:

- Validate requests with Pydantic v2.
- Use a repository layer for SQLAlchemy access.
- Enforce business rules in the service layer.
- Secure routes using Supabase auth dependencies.
- Emit breadcrumbs/logs for observability.
- Provide pytest coverage (unit + integration).

Directory layout:

```
app/
├── api/v1/users.py
├── repositories/user_repository.py
├── schemas/user.py
├── services/user_service.py
└── tests/api/test_users.py
```

---

## Schemas (`app/schemas/user.py`)

```python
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict, computed_field


class UserCreate(BaseModel):
    supabase_id: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    department: str | None = None

    model_config = ConfigDict(extra="forbid")


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    department: str | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None = None
    department: str | None = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def display_name(self) -> str:
        return self.full_name or self.email.split("@", 1)[0]
```

- Request models forbid extra fields.
- Response model leverages `from_attributes=True` for ORM conversion.
- `display_name` demonstrates derived data.

---

## Repository (`app/repositories/user_repository.py`)

```python
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
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
            return None
        await self.session.commit()
        return record

    async def get(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, limit: int = 100) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars())
```

- Repositories only handle persistence; no business rules.
- All methods return ORM models; conversion to schemas happens upstream.

---

## Service (`app/services/user_service.py`)

```python
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class DuplicateEmailError(Exception):
    """Raised when attempting to create a user with an existing email."""


class UserNotFoundError(Exception):
    """Raised when a user lookup fails."""


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create(self, payload: UserCreate) -> UserResponse:
        if await self.repository.email_exists(payload.email):
            raise DuplicateEmailError("Email already registered")
        user = await self.repository.create(payload)
        return UserResponse.model_validate(user, from_attributes=True)

    async def update(self, user_id: str, payload: UserUpdate) -> UserResponse:
        updated = await self.repository.update(user_id, payload)
        if not updated:
            raise UserNotFoundError(user_id)
        return UserResponse.model_validate(updated, from_attributes=True)

    async def list(self) -> list[UserResponse]:
        users = await self.repository.list()
        return [UserResponse.model_validate(user, from_attributes=True) for user in users]
```

- Services return Pydantic responses for consistency.
- Domain errors are raised for routers to translate into HTTP responses.

---

## Router (`app/api/v1/users.py`)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.supabase_auth import get_current_admin_user
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import DuplicateEmailError, UserNotFoundError, UserService


router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    repository = UserRepository(session)
    return UserService(repository)


@router.get("/", response_model=list[UserResponse])
async def list_users(
    _: None = Depends(get_current_admin_user),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    return await service.list()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(
    payload: UserCreate,
    _: None = Depends(get_current_admin_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        return await service.create(payload)
    except DuplicateEmailError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    _: None = Depends(get_current_admin_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        return await service.update(user_id, payload)
    except UserNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
```

- Dependencies enforce admin-only access and provide request-scoped sessions.
- HTTP errors are raised in the router after translating domain exceptions.

---

## Tests (`app/tests/api/test_users.py`)

```python
import pytest
from httpx import AsyncClient

from app.api.v1.users import router
from app.main import app


@pytest.fixture
async def client(mocker):
    app.include_router(router, prefix="/api")
    mocker.patch("app.middleware.supabase_auth.get_current_admin_user", return_value=None)
    async with AsyncClient(app=app, base_url="http://testserver") as test_client:
        yield test_client
    app.router.routes.pop()  # remove test router inclusion if needed


@pytest.mark.asyncio
async def test_create_user_success(client, mocker):
    service = mocker.AsyncMock()
    service.create.return_value = {"id": "1", "email": "user@example.com"}
    app.dependency_overrides[get_user_service] = lambda: service

    response = await client.post(
        "/api/users",
        json={"email": "user@example.com", "supabase_id": "abc"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_user_not_found(client, mocker):
    service = mocker.AsyncMock()
    service.update.side_effect = UserNotFoundError("missing")
    app.dependency_overrides[get_user_service] = lambda: service

    response = await client.patch(
        "/api/users/missing",
        json={"full_name": "Dr. Admin"},
    )

    assert response.status_code == 404
    app.dependency_overrides.clear()
```

- Integration tests use dependency overrides to inject fakes.
- Use `AsyncClient` for request/response assertions.
- Include negative paths (404, 409) to ensure error translation is correct.

---

## Background Task Hook

If user creation triggers asynchronous email invites, leverage FastAPI background tasks:

```python
from fastapi import BackgroundTasks


@router.post("/invite", status_code=status.HTTP_202_ACCEPTED)
async def invite_user(
    payload: UserCreate,
    background: BackgroundTasks,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.create(payload)
    background.add_task(send_invite_email, user.email)
    return user
```

Remember to mock background tasks in tests by inspecting the `background.tasks` list or patching the task function.

---

## Checklist & Next Steps

- [ ] Create module folders (`api/`, `services/`, `repositories/`, `schemas/`, `tests/`).
- [ ] Add Sentry breadcrumbs/logging where meaningful.
- [ ] Update `app/api/v1/router.py` to include the new router.
- [ ] Provide fixtures for test data and dependency overrides.
- [ ] Document feature-specific environment variables (if any) in `configuration.md`.

This blueprint should be cloned and customized for each new business capability (training modules, task queues, reporting, etc.).

---

**Related Files:**
- backend/app/api/v1/users.py
- backend/app/services/user_service.py
- backend/app/repositories/user_repository.py
- backend/app/tests/
- docs/architecture/project-structure.md
