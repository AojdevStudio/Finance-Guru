<!-- v2.0 | 2025-10-30 -->
# Routing and Controllers - Best Practices

Complete guide to clean FastAPI route definitions and controller patterns in the Unified Dental backend.

> Migration Note: Former Express `Router` patterns have been replaced with FastAPI `APIRouter` modules that delegate to dependency-injected services and repositories. Update legacy routes to use the patterns in this document.

## Table of Contents

- [Routes: Path Operations Only](#routes-path-operations-only)
- [Dependency Injection Patterns](#dependency-injection-patterns)
- [Controller Strategies](#controller-strategies)
- [Good Examples](#good-examples)
- [Anti-Patterns](#anti-patterns)
- [Refactoring from Express](#refactoring-from-express)
- [Error Handling](#error-handling)
- [HTTP Status Codes](#http-status-codes)
- [Quick Checklist](#quick-checklist)

---

## Routes: Path Operations Only

### The Golden Rule

**Path operation functions should ONLY:**
- ✅ Declare HTTP method, path, tags, and metadata
- ✅ Compose authentication/authorization dependencies with `Depends`
- ✅ Call services (optionally via a thin controller helper)
- ✅ Return validated response models

**Path operation functions should NEVER:**
- ❌ Duplicate business logic already available in services
- ❌ Open database sessions directly or execute SQLAlchemy queries
- ❌ Perform manual JSON serialization (let Pydantic handle it)
- ❌ Call external APIs directly (delegate to services/helpers)
- ❌ Catch and swallow domain errors (translate to HTTP once)

### Clean APIRouter Pattern

```python
"""User routing module."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.supabase_auth import get_current_admin_user
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """Bind the request-scoped SQLAlchemy session to a repository."""
    return UserRepository(session)


def get_user_service(repository: UserRepository = Depends(get_user_repository)) -> UserService:
    """Compose the service used by route handlers (override-friendly in tests)."""
    return UserService(repository)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(
    payload: UserCreate,
    _: None = Depends(get_current_admin_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    created = await service.create(payload)
    return service.to_schema(created)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    _: None = Depends(get_current_admin_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    updated = await service.update(user_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return service.to_schema(updated)
```

**Key Points:**
- Dependencies are declared close to the handler for readability.
- Business logic lives in `UserService`; repositories hide SQL.
- `response_model` emits Pydantic schemas automatically.
- Authorization is handled by dependencies sourced from `app/middleware/supabase_auth.py`.

---

## Dependency Injection Patterns

FastAPI ships with dependency injection baked in via `Depends`. Treat dependencies as the unit of reuse and override.

### Composition Order

1. **Infrastructure providers** (database session, Supabase clients, Redis connections)
2. **Repositories** (wrap infrastructure; pure data access)
3. **Services** (consume repositories and other providers)
4. **Controller helpers** (optional; translate services to responses)

### Example Dependency Tree

```python
from fastapi import Depends

def get_db_session() -> AsyncSession:
    return Depends(get_db)  # Provided by app.core.database


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)
```

### Testing Overrides

During tests, override dependencies at the router or app level:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_create_user(mocker):
    fake_service = mocker.AsyncMock()
    fake_service.create.return_value = mocker.sentinel.user

    app.dependency_overrides[get_user_service] = lambda: fake_service

    with TestClient(app) as client:
        response = client.post("/api/users", json={"email": "user@example.com", "role": "admin"})
    assert response.status_code == 201
    app.dependency_overrides.clear()
```

This approach keeps handlers simple while making integration tests stable and fast.

---

## Controller Strategies

FastAPI favors function-based handlers, but controller abstractions can still help when coordinating complex responses.

### Option 1: Function-Based Handlers (Default)
- Small modules under `app/api/v1` with cohesive functions.
- Best for CRUD endpoints and lightweight aggregation.
- Works seamlessly with dependency overrides.

### Option 2: Controller Classes (Advanced)
Use dataclasses to bundle shared dependencies without storing request state.

```python
from dataclasses import dataclass
from fastapi import Depends


@dataclass
class UserController:
    service: UserService = Depends(get_user_service)

    async def get_user(self, user_id: str) -> UserResponse:
        user = await self.service.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return self.service.to_schema(user)


controller = UserController()


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(user_id: str, controller: UserController = Depends(UserController)) -> UserResponse:
    return await controller.get_user(user_id)
```

**Guidance:** Start with function-based handlers. Introduce controller classes only when you need grouped behavior, shared caching, or granular instrumentation.

---

## Good Examples

### Aggregating Routers (`app/api/v1/router.py`)

```python
"""Main API router for version 1 endpoints."""

from fastapi import APIRouter

from app.api.v1 import auth, users

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
```

### Background Tasks

```python
from fastapi import BackgroundTasks


@router.post("/invite", status_code=202)
async def invite_user(
    payload: InviteUserRequest,
    background: BackgroundTasks,
    service: UserService = Depends(get_user_service),
):
    user = await service.create(payload)
    background.add_task(service.send_invite_email, user.id)
    return service.to_schema(user)
```

- Leverage `BackgroundTasks` for fire-and-forget work (eventually replace with Celery if heavy).
- Keep the HTTP response independent from background execution success.

---

## Anti-Patterns

| Anti-Pattern | Why it Hurts | Refactor To |
|--------------|--------------|-------------|
| Direct database access inside route handler | Couples HTTP layer to persistence, hard to test | Move queries to repositories, inject via service |
| Manual JSON serialization | Bypasses Pydantic, loses validation | Return Pydantic models or dicts from services |
| Catch-all `Exception` in handlers | Masks real errors, breaks global handlers | Let exceptions bubble or raise domain-specific errors |
| Instantiate services manually per call | Duplicates dependency logic, complicates tests | Use dependency providers | 
| Multiple endpoints in same function | Hard to trace behavior | One handler per HTTP verb + path |

### Example: What NOT to do

```python
@router.post("/users")
async def bad_create_user(payload: dict, session: AsyncSession = Depends(get_db)):
    # ❌ Validation missing, schema ignored
    result = await session.execute(select(User).where(User.email == payload["email"]))
    if result.scalar_one_or_none():
        return JSONResponse(status_code=400, content={"detail": "Email exists"})

    user = User(**payload)
    session.add(user)
    await session.commit()
    return user  # ❌ No serialization guarantees
```

Refactor by introducing a Pydantic schema, repository logic, and a dedicated service method.

---

## Refactoring from Express

| Express (Old) | FastAPI (New) |
|---------------|---------------|
| `router.get('/users/:id', auth, ctrl.getUser)` | `@router.get("/users/{user_id}", dependencies=[Depends(get_current_user)])` |
| `req.params.id`, `req.query`, `req.body` | Typed parameters (`user_id: str`, `payload: UserCreate`) |
| `res.status(200).json(data)` | Return Pydantic models; FastAPI serializes |
| Middleware with `app.use()` | Dependencies (`Depends`), `app.add_middleware()` |
| BaseController for success/error helpers | Global exception handlers (`app.add_exception_handler`) |

### Migration Steps
1. Create a new module under `app/api/v1/{feature}.py`.
2. Define `APIRouter` with prefixes and tags.
3. Declare dependency providers for repositories/services.
4. Replace Express controller methods with async functions returning schemas.
5. Update aggregator router (`app/api/v1/router.py`) to include the module.
6. Delete legacy Express code and remove Prisma dependencies (per "Out-with-the-old" policy).

---

## Error Handling

- Controllers should raise domain-specific exceptions (`DuplicateEmailError`, `PermissionDeniedError`).
- Route handlers translate domain errors to HTTP via `HTTPException` **once**.
- Register global handlers in `app/main.py` for recurring scenarios (validation errors, authentication failures).

```python
from fastapi import HTTPException


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
):
    try:
        await service.deactivate(user_id)
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PermissionDeniedError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
```

If you observe repeated translation logic, add a custom exception handler:

```python
@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(_: Request, exc: UserNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})
```

---

## HTTP Status Codes

| Scenario | Status | Notes |
|----------|--------|-------|
| Resource created | `201 Created` | Include `Location` header when appropriate |
| Successful fetch/update | `200 OK` | Use `response_model` for typed responses |
| No content (delete/toggle) | `204 No Content` | Return `None` |
| Client error (validation) | `400 Bad Request` | Prefer Pydantic validation errors |
| Unauthorized | `401 Unauthorized` | Use Supabase auth dependency to raise |
| Forbidden | `403 Forbidden` | Authorization failure |
| Not found | `404 Not Found` | Use domain errors + handlers |
| Conflict | `409 Conflict` | Duplicate records, version conflicts |
| Unprocessable entity | `422 Unprocessable Entity` | Automatic for schema validation failures |

Always set `status_code=` explicitly in decorators so readers know expected behavior immediately.

---

## Quick Checklist

- [ ] APIRouter declared with prefix and tags
- [ ] Dependencies defined for DB session → repository → service
- [ ] Request/response models use Pydantic v2 (see `validation-patterns.md`)
- [ ] Handlers contain zero business logic (service handles it)
- [ ] Domain errors mapped to HTTP once (controller or global handler)
- [ ] All endpoints included in `app/api/v1/router.py`
- [ ] Auth dependencies enforce Supabase policy (admin/user scopes)
- [ ] Tests override dependencies instead of monkeypatching globals

---

**Related Files:**
- backend/app/api/v1/users.py
- backend/app/api/v1/router.py
- backend/app/services/user_service.py
- backend/app/middleware/supabase_auth.py
