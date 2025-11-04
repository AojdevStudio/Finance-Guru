<!-- v2.0 | 2025-10-30 -->
# Database Patterns - SQLAlchemy 2.0 (Async)

Complete guide to modeling and querying Supabase PostgreSQL using SQLAlchemy 2.0’s async ORM within the Unified Dental backend.

> Migration Note: All Prisma patterns have been replaced with SQLAlchemy 2.0 best practices. Follow these patterns when adding models, queries, and migrations in `backend/app`.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Model Definition Patterns](#model-definition-patterns)
- [Relationships & Declarative Mapping](#relationships--declarative-mapping)
- [Async Query Patterns](#async-query-patterns)
- [Transactions & Unit of Work](#transactions--unit-of-work)
- [Migration Workflow (Alembic)](#migration-workflow-alembic)
- [Performance & Optimization](#performance--optimization)
- [Testing ORM Code](#testing-orm-code)
- [Anti-Patterns](#anti-patterns)
- [Quick Reference](#quick-reference)

---

## Architecture Overview

```
Supabase PostgreSQL
        ↑
AsyncEngine (SQLAlchemy)  ← settings.DATABASE_URL (postgresql+asyncpg)
        ↑
AsyncSession (dependency) ← `get_db()` in app/core/database.py
        ↑
Repositories            ← thin wrappers around AsyncSession
        ↑
Services                ← business logic orchestrating repositories
        ↑
FastAPI Routers         ← request/response handling
```

Key modules:
- `backend/app/core/database.py` – engine & session factories, `Base` declarative registry
- `backend/app/models/` – SQLAlchemy models (inherit from `BaseModel`)
- `backend/app/repositories/` – async query helpers using injected sessions
- `backend/alembic/` – migrations and revision scripts

---

## Model Definition Patterns

### Base Model

```python
"""Base model with UUID primary keys and timestamps."""

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative registry shared across all models."""


class TimestampedUUIDModel(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

**Guidelines**
- Store models in feature-focused files (e.g., `user.py`, `training_module.py`).
- Use PostgreSQL-native types: `JSONB`, `ARRAY`, `UUID`, `INET` to leverage Supabase capabilities.
- Always add indexes for lookup columns (`index=True`) and unique constraints where applicable.

### Example Model (`backend/app/models/user.py`)

```python
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB


class User(TimestampedUUIDModel):
    __tablename__ = "users"

    supabase_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(String, default="authenticated", nullable=False)
    last_sign_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    profile_metadata: Mapped[dict[str, object] | None] = mapped_column(JSONB)
```

---

## Relationships & Declarative Mapping

### One-to-Many

```python
class TrainingModule(TimestampedUUIDModel):
    __tablename__ = "training_modules"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sections: Mapped[list[ModuleSection]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ModuleSection(TimestampedUUIDModel):
    __tablename__ = "module_sections"

    module_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_modules.id"), index=True)
    module: Mapped[TrainingModule] = relationship(back_populates="sections")
```

**Best Practices**
- Set `lazy="selectin"` for collections to avoid N+1 queries.
- Add `cascade="all, delete-orphan"` for dependent child rows.
- Use `back_populates` over `backref` for clarity and type checking.

### Many-to-Many via Association Table

```python
enrollment_table = Table(
    "module_enrollments",
    Base.metadata,
    Column("module_id", ForeignKey("training_modules.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)


class TrainingModule(TimestampedUUIDModel):
    participants: Mapped[list[User]] = relationship(
        secondary=enrollment_table,
        back_populates="enrolled_modules",
    )


class User(TimestampedUUIDModel):
    enrolled_modules: Mapped[list[TrainingModule]] = relationship(
        secondary=enrollment_table,
        back_populates="participants",
    )
```

### JSONB Fields

Store flexible data from Supabase or external APIs in `JSONB`, but validate via Pydantic before persisting.

```python
class QuizQuestion(TimestampedUUIDModel):
    metadata: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
```

---

## Async Query Patterns

### Injected Session (`AsyncSession`)

Repositories receive the session from FastAPI dependencies.

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class ModuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_modules(self, limit: int = 50) -> list[TrainingModule]:
        stmt = select(TrainingModule).order_by(TrainingModule.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def get_with_sections(self, module_id: uuid.UUID) -> TrainingModule | None:
        stmt = (
            select(TrainingModule)
            .where(TrainingModule.id == module_id)
            .options(selectinload(TrainingModule.sections))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, payload: TrainingModuleCreate) -> TrainingModule:
        module = TrainingModule(**payload.model_dump())
        self.session.add(module)
        await self.session.commit()
        await self.session.refresh(module)
        return module
```

### Filtering & Pagination

```python
from sqlalchemy import select


stmt = (
    select(User)
    .where(User.is_active.is_(True))
    .where(User.department.in_(departments))
    .order_by(User.created_at.desc())
    .offset(page * page_size)
    .limit(page_size)
)
result = await session.execute(stmt)
users = result.scalars().all()
```

Use method chaining for readability; avoid building raw SQL manually.

### Bulk Operations

```python
from sqlalchemy import update


await session.execute(
    update(User)
    .where(User.id.in_(user_ids))
    .values(is_active=False)
)
await session.commit()
```

Prefer `update()`/`delete()` for set-based changes; wrap in service-level transactions when combined with business logic.

---

## Transactions & Unit of Work

SQLAlchemy’s `AsyncSession` manages transactions via context managers.

```python
from contextlib import asynccontextmanager


@asynccontextmanager
async def unit_of_work(session: AsyncSession):
    try:
        async with session.begin():
            yield
    except Exception:
        await session.rollback()
        raise


class EnrollmentService:
    def __init__(self, session: AsyncSession, module_repo: ModuleRepository):
        self.session = session
        self.module_repo = module_repo

    async def enroll(self, module_id: uuid.UUID, user_id: uuid.UUID) -> None:
        async with unit_of_work(self.session):
            module = await self.module_repo.get_with_sections(module_id)
            if module is None:
                raise ModuleNotFoundError(module_id)
            module.participants.append(await self.session.get(User, user_id))
```

**Tips**
- Use `session.begin()` for multi-step operations requiring commit/rollback.
- Stick to a single `AsyncSession` per request to keep transactions scoped.
- Delay external side-effects until after commit to avoid ghost operations.

---

## Migration Workflow (Alembic)

Fast path for creating a new table:

1. Update or add models in `backend/app/models/`.
2. Generate migration: `cd backend && uv run alembic revision --autogenerate -m "add training module"`
3. Review the generated script (`backend/alembic/versions/*.py`) for correctness:
   - Ensure UUID defaults use `sa.text('gen_random_uuid()')`.
   - Confirm indexes, foreign keys, and cascades match the model.
4. Apply migration locally: `uv run alembic upgrade head`
5. Run tests (including migrations if required).

**Autogenerate Tips**
- Alembic detects column/property changes when models import `Base` from `app.core.database`.
- For JSONB or computed columns, double-check the autogen script (Alembic may not infer everything).
- Store reusable constraints (like enums) as `sa.Enum(..., name="...", create_type=False)` when referencing existing DB enums.

---

## Performance & Optimization

- **Indexes:** Use `.create_index()` or `index=True` on frequently queried columns (`supabase_id`, `email`).
- **`selectinload`:** Default to `lazy="selectin"` for relationships to prevent N+1 issues while preserving lazy loading semantics.
- **Batch Queries:** Instead of looping with `.get()`, fetch in bulk using `in_` filters.
- **Connection Pooling:** Async engine defaults suffice; override `pool_size`, `max_overflow` in `create_async_engine` if necessary.
- **JSONB Queries:** When querying JSONB fields, use PostgreSQL operators via `User.profile_metadata["department"].astext == "Claims"`.
- **Materialized Views:** For complex reporting, create views/mat views via migrations and query with SQLAlchemy text constructs.

---

## Testing ORM Code

### Unit Tests (Repositories)

```python
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.fixture
async def test_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session


@pytest.mark.asyncio
async def test_module_repository_create(test_session: AsyncSession):
    repo = ModuleRepository(test_session)
    module = await repo.create(TrainingModuleCreate(title="New Hire"))
    assert module.title == "New Hire"
```

### Integration Tests

- Use the real `get_db` dependency override to supply the test session.
- Run Alembic migrations against ephemeral Supabase branches or local Postgres when validating schema changes.

---

## Anti-Patterns

| Anti-Pattern | Why It Hurts | Fix |
|--------------|-------------|-----|
| Instantiating a new engine/session per request | Exhausts connection pool, slow startup | Use shared async engine in `app/core/database.py` |
| Mixing sync SQLAlchemy APIs with async sessions | Deadlocks event loop | Always import from `sqlalchemy.ext.asyncio` and use async primitives |
| Returning raw row tuples | Leaks low-level structures | Use `.scalars()` or Pydantic DTOs |
| Executing raw SQL strings for simple queries | Loses safety, no type checks | Build queries with SQLAlchemy select/update/delete |
| Forgetting to commit/rollback | Leaves transactions open, locks tables | Use service-level transactions or repository commits |

---

## Quick Reference

- Inherit models from `TimestampedUUIDModel` for consistent IDs/timestamps.
- Use `mapped_column`, `Mapped[...]`, and type annotations for SQLAlchemy 2.0 style.
- Prefer `selectinload` for relationships; avoid eager `.options(joinedload(...))` unless necessary.
- Always commit inside repositories **or** wrap multi-step workflows in service-level `session.begin()` contexts.
- Generate and review Alembic migrations whenever models change.
- Validate data with Pydantic before persisting JSONB fields.

---

**Related Files:**
- backend/app/models/
- backend/app/core/database.py
- backend/app/repositories/
- backend/alembic/
- docs/architecture/project-structure.md
