<!-- v2.0 | 2025-10-30 -->
# Architecture Overview - Backend Services

Complete guide to the layered architecture pattern used in backend microservices built with FastAPI, async SQLAlchemy, and Pydantic v2.

> Migration Note: The architecture guidance now standardizes on the FastAPI + Supabase PostgreSQL stack. Update feature scaffolding to use `APIRouter` handlers that delegate to dependency-injected services and repositories.

## Table of Contents

- [Layered Architecture Pattern](#layered-architecture-pattern)
- [Request Lifecycle](#request-lifecycle)
- [Service Comparison](#service-comparison)
- [Directory Structure Rationale](#directory-structure-rationale)
- [Module Organization](#module-organization)
- [Separation of Concerns](#separation-of-concerns)

---

## Layered Architecture Pattern

### The Four Layers

```
┌─────────────────────────────────────┐
│           ASGI Request              │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 1: ROUTERS (APIRouter)       │
│  - Route definitions only           │
│  - Dependency wiring (Depends)      │
│  - Delegate to controllers/handlers │
│  - NO business logic                │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 2: CONTROLLERS (Handlers)    │
│  - Request/response handling        │
│  - Pydantic validation              │
│  - Call services                    │
│  - Format responses                 │
│  - Error translation (HTTPException)│
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 3: SERVICES                  │
│  - Business logic & orchestration   │
│  - Transaction boundaries           │
│  - Call repositories                │
│  - No HTTP or framework types       │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 4: REPOSITORIES              │
│  - Async SQLAlchemy operations      │
│  - Query optimization               │
│  - Caching integration              │
│  - Database abstraction             │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│   Database (Supabase PostgreSQL)    │
└─────────────────────────────────────┘
```

### Why This Architecture?

**Testability:**
- Each layer can be unit-tested in isolation with FastAPI dependency overrides
- Async SQLAlchemy sessions are easily mocked via `async_sessionmaker`
- Clear contract boundaries encourage predictable fixtures

**Maintainability:**
- Business logic sits in services instead of FastAPI handlers
- HTTP concerns remain isolated to `APIRouter` modules
- Repository layer hides SQLAlchemy details and query tuning

**Reusability:**
- Services can be reused by background tasks, Celery jobs, and schedulers
- Repositories expose consistent async APIs irrespective of the underlying engine
- Controllers focus on translating between HTTP requests and service contracts

**Scalability:**
- New endpoints compose existing dependencies via `Depends`
- Standardized layering accelerates onboarding and code reviews
- Async stack supports high concurrency without blocking the event loop

---

## Request Lifecycle

### Complete Flow Example

```python
1. HTTP POST /api/v1/users
   ↓
2. FastAPI resolves route in app/api/v1/users.py (APIRouter)
   ↓
3. Dependency graph executes:
   - get_db() -> AsyncSession
   - get_user_service() -> UserService (injects repository)
   ↓
4. Route handler (controller) validates request with Pydantic models
   ↓
5. Service enforces business rules & orchestrates repositories
   ↓
6. Repository performs async SQLAlchemy operations
   ↓
7. Response surfaces back through service → controller → FastAPI → client
```

**Controller Example (`app/api/v1/users.py`):**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    """Provide a repository bound to the current request-scoped session."""
    return UserRepository(session)


def get_user_service(repository: UserRepository = Depends(get_user_repository)) -> UserService:
    """Dependency override hook for unit tests."""
    return UserService(repository)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.create(payload)
    return service.to_schema(user)
```

**Service Example (`app/services/user_service.py` with repository injection):**

```python
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    """Business rules and orchestration for user operations."""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create(self, payload: UserCreate):
        if await self.repository.email_exists(payload.email):
            raise DuplicateEmailError()
        return await self.repository.create(payload)
```

**Repository Example (`app/repositories/user_repository.py`):**

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    """Async data-access layer for user entities."""

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
```

### Middleware Execution Order

**Critical:** Starlette executes middleware in reverse registration order (last registered = first to run).

```python
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware


def configure_middlewares(app: FastAPI) -> None:
    app.add_middleware(  # 1. Registered first → outermost wrapper
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware)             # 2. Registered second → runs before CORS
    app.add_middleware(                            # 3. Registered last → runs closest to handlers
        TrustedHostMiddleware,
        allowed_hosts=["unifiedental.com", "*.unifiedental.com"],
    )


app = FastAPI()
configure_middlewares(app)


@app.middleware("http")
async def audit_trail(request, call_next):  # 4. Custom audit wrapper
    ...
```

- `app.add_middleware(...)` builds a stack—the last middleware registered processes the request first and the response last.
- Function-style `@app.middleware("http")` executes in declaration order and wraps the remainder of the stack.
- Always register exception handlers **after** routers just like in `app/main.py`.

---

## Service Comparison

### User Management Module (Mature Pattern ✅)

**Strengths:**
- `app/api/v1/users.py` keeps handlers slim and leverages dependency-injected services
- `UserService` encapsulates Supabase sync logic and schema conversion helpers
- Strong separation between Pydantic schemas and SQLAlchemy models
- Endpoints rely on reusable authentication dependencies in `app/middleware/supabase_auth.py`

**Example Structure:**
```
app/
├── api/v1/users.py            ✅ Focused APIRouter
├── services/user_service.py   ✅ Business logic + orchestration
├── models/user.py             ✅ SQLAlchemy model
└── schemas/user.py            ✅ Pydantic validation layer
```

**Use as template** when introducing new feature modules.

### Auth Module (Transitioning ⚠️)

**Strengths:**
- Routing scaffold exists in `app/api/v1/auth.py`
- Dependencies (`get_db`) already wired for future work
- Shares middleware-based authentication patterns

**Weaknesses:**
- Endpoints still return placeholder responses
- Service and repository layers not yet extracted
- Missing validation schemas for login/register flows
- No explicit error handling or Supabase integration

**Next Steps:** Extract `AuthService` with Supabase client orchestration, introduce repositories for credential storage, and create request/response schemas.

---

## Directory Structure Rationale

### API Routers & Controllers (`backend/app/api`)

**Purpose:** Organize FastAPI routers and controller functions per version (e.g., `v1`).

**Contents:**
- `router.py` aggregates feature routers
- `{feature}.py` defines APIRouter instances and endpoint functions

**Naming:** snake_case filenames ending in the feature (`users.py`, `auth.py`).

**Responsibilities:**
- Declare endpoints, docstrings, and HTTP status codes
- Compose middleware/authorization dependencies via `Depends`
- Map transport-level errors to `HTTPException`

### Services Directory (`backend/app/services`)

**Purpose:** Contain business logic that can be reused across transports.

**Contents:**
- `{feature}_service.py` modules exposing service classes or functions

**Responsibilities:**
- Enforce business rules and invariants
- Coordinate multiple repositories and external APIs (Supabase, Redis)
- Remain unaware of FastAPI request/response types

### Repositories Directory (`backend/app/repositories`)

**Purpose:** Abstract async SQLAlchemy persistence.

**Contents:**
- `{entity}_repository.py` modules (to be expanded—currently user operations live inside services)

**Responsibilities:**
- Encapsulate common query patterns
- Manage transactions and session lifecycle expectations
- Provide a single place for caching or Supabase-to-Postgres synchronization

**Current Gap:** Extract dedicated repository modules; migrate direct session usage from services into repositories to achieve full separation.

### Models Directory (`backend/app/models`)

**Purpose:** Define SQLAlchemy ORM models that map to Supabase PostgreSQL tables.

**Responsibilities:**
- Contain column definitions, relationships, and table metadata
- Avoid business logic—limit to model-level helpers when unavoidable

### Schemas Directory (`backend/app/schemas`)

**Purpose:** Host Pydantic v2 request/response DTOs and validation schemas.

**Responsibilities:**
- Enforce data shape at the API boundary
- Provide `.model_validate()` helpers for ORM integration (`from_attributes=True`)
- Support both inbound (request) and outbound (response) data contracts

### Middleware Directory (`backend/app/middleware`)

**Purpose:** Cross-cutting concerns for authentication, CORS, and request context.

**Responsibilities:**
- Register reusable `Depends` providers (Supabase auth helpers)
- Configure CORS, logging, rate limiting, etc.
- Contain Starlette-compatible middleware classes when stateful behavior is required

### Core Directory (`backend/app/core`)

**Purpose:** Centralized configuration, infrastructure clients, and startup/shutdown helpers.

**Responsibilities:**
- Provide typed settings via `config.py`
- Expose database/redis connectors (`database.py`, `redis.py`)
- Register exception handlers and logging configuration

### Tasks Directory (`backend/app/tasks`)

**Purpose:** Scheduled jobs and Celery task definitions that reuse service/repository layers.

**Responsibilities:**
- Implement APScheduler setup (`scheduler.py`)
- Provide background workers with the same dependency graph as HTTP requests

---

## Module Organization

### Feature-Based Organization

For complex domains, co-locate API, service, repository, schemas, and tests under a feature namespace:

```
app/users/
├── __init__.py
├── api.py               # APIRouter + handlers
├── service.py           # Business logic
├── repository.py        # SQLAlchemy data access
├── schemas.py           # Pydantic DTOs
├── models.py            # SQLAlchemy models (optional override)
└── tests/               # Feature-specific tests
```

**Use when:**
- The feature spans 5+ files or requires dedicated subdomains
- Coordinating tasks, HTTP endpoints, and background jobs benefits from proximity
- You need clear ownership boundaries for squads

### Flat Organization

For simple features, remain within the shared directories:

```
app/
├── api/v1/notifications.py
├── services/notification_service.py
├── repositories/notification_repository.py
└── schemas/notification.py
```

**Use when:**
- Feature scope is small (< 5 files)
- Shared infrastructure already covers most needs
- Additional nesting would reduce clarity

---

## Separation of Concerns

### What Goes Where

**Routers Layer (`APIRouter`):**
- ✅ Endpoint definitions and metadata
- ✅ Dependency wiring (`Depends`, security scopes)
- ✅ Controller delegation
- ❌ Business logic
- ❌ Direct database access

**Controllers Layer (Handler functions/classes):**
- ✅ Parse query/path/body parameters via Pydantic models
- ✅ Call services and translate domain errors to HTTP responses
- ✅ Choose appropriate status codes and response models
- ❌ Contain business rules
- ❌ Instantiate SQLAlchemy sessions directly

**Services Layer:**
- ✅ Implement business invariants and orchestration
- ✅ Handle multi-repository transactions
- ✅ Integrate third-party providers (Supabase, Redis, external APIs)
- ❌ Raise `HTTPException` (instead raise domain errors)
- ❌ Import FastAPI request/response objects

**Repositories Layer:**
- ✅ Encapsulate async SQLAlchemy queries and persistence
- ✅ Manage session usage patterns (commit, refresh)
- ✅ Provide targeted data access helpers for services
- ❌ Contain domain decisions
- ❌ Know about HTTP or dependency injection

### Example: User Creation

**Router:**

```python
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.create(payload)
    return service.to_schema(user)
```

**Controller Logic (within handler):**

```python
try:
    user = await service.create(payload)
except DuplicateEmailError as error:
    raise HTTPException(status_code=409, detail=str(error)) from error
```

**Service:**

```python
class UserService:
    async def create(self, payload: UserCreate) -> User:
        if await self.repository.email_exists(payload.email):
            raise DuplicateEmailError("Email already registered")
        return await self.repository.create(payload)
```

**Repository:**

```python
class UserRepository:
    async def create(self, payload: UserCreate) -> User:
        user = User(**payload.model_dump())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
```

**Notice:** Each layer keeps a single responsibility, making async workflows predictable and testable.

---

**Related Files:**
- backend/app/main.py
- backend/app/api/v1/router.py
- backend/app/services/user_service.py
- docs/architecture/project-structure.md
