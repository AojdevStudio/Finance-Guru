<!-- v2.0 | 2025-10-30 -->
# Validation Patterns - Pydantic v2 + FastAPI

Complete guide to data validation and serialization using Pydantic v2 within the Unified Dental FastAPI backend.

> Migration Note: All Zod- and Joi-based validation has been replaced with Pydantic v2 models. Use the patterns in this document when creating request/response DTOs, service-layer validators, and repository adapters.

## Table of Contents

- [Why Pydantic v2?](#why-pydantic-v2)
- [Core Modeling Patterns](#core-modeling-patterns)
- [Request/Response DTO Architecture](#requestresponse-dto-architecture)
- [Field & Model Validation](#field--model-validation)
- [Advanced Types & Adapters](#advanced-types--adapters)
- [Working with SQLAlchemy](#working-with-sqlalchemy)
- [Error Handling & Messaging](#error-handling--messaging)
- [Testing Validation](#testing-validation)
- [Anti-Patterns](#anti-patterns)
- [Quick Reference](#quick-reference)

---

## Why Pydantic v2?

Pydantic v2 is the native validation layer for FastAPI and offers significant benefits over legacy Zod/Joi stacks:

**Type-Driven Design**
- ✅ Python type hints drive runtime validation and editor autocomplete
- ✅ `ConfigDict` and `Annotated` enable strict modes per model/field
- ✅ Automatic JSON schema generation powers FastAPI OpenAPI docs

**Performance & Ergonomics**
- ✅ Rust-powered core delivers fast validation even for nested models
- ✅ `.model_validate()` and `.model_dump()` unify ORM → DTO transformations
- ✅ Built-in support for computed fields, custom serializers, and context-aware validators

**Integration**
- ✅ First-class integration with FastAPI response models and dependency system
- ✅ Works seamlessly with async SQLAlchemy via `from_attributes=True`
- ✅ Validation errors emit structured payloads that our `app/core/errors.py` normalizes

---

## Core Modeling Patterns

### BaseModel + `Field`

```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class InviteUser(BaseModel):
    """Incoming payload for inviting new team members."""

    email: EmailStr = Field(..., description="Employee inbox")
    role: str = Field(..., pattern=r"^(admin|operations|staff)$")
    send_welcome: bool = Field(default=True)

    model_config = ConfigDict(extra="forbid", validate_assignment=True)
```

- Provide descriptive docstrings for docs and code readers.
- Set `extra="forbid"` to reject unexpected fields by default.
- Use rich types (e.g., `EmailStr`, `HttpUrl`) instead of raw strings.

### Optional, Nullable, and Defaults

```python
class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    department: str | None = Field(default=None)
    phone: str | None = Field(default=None, pattern=r"^[0-9\-\(\)\s]+$")
```

Use `| None` (PEP 604) for optionality. Avoid `Optional[...]` unless you need `typing.Optional` compatibility.

### Enumerations & Literals

```python
from enum import Enum


class TicketPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


class CreateTicket(BaseModel):
    priority: TicketPriority = Field(default=TicketPriority.normal)
```

Prefer `Enum` subclasses when values are reused across schemas, services, and repositories.

---

## Request/Response DTO Architecture

Follow the “Create / Update / Response” pattern used in `backend/app/schemas/user.py`.

```python
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict, computed_field


class UserCreate(BaseModel):
    supabase_id: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    department: str | None = None

    @classmethod
    def from_supabase(cls, metadata: dict[str, object]) -> "UserCreate":
        return cls.model_validate(metadata)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None
    department: str | None = None

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None = None
    department: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def display_name(self) -> str:
        return self.full_name or self.email.split("@", 1)[0]
```

**Guidelines**
- Request models (`Create`, `Update`) set `extra="forbid"` to catch typos.
- Response models (`Response`, `Summary`) set `from_attributes=True` for ORM integration.
- Use `computed_field` for derived data (e.g., `profile_complete`, `account_age_days`).

### Router Usage

```python
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.create(payload)
    return service.to_schema(user)
```

FastAPI automatically validates `payload` against `UserCreate` and serializes responses using `UserResponse`—no manual try/except required for validation failures.

---

## Field & Model Validation

Leverage Pydantic v2’s decorators to express business invariants.

### Field Validators

```python
from pydantic import field_validator


class SupabaseUserData(BaseModel):
    role: str
    metadata: dict[str, object] = Field(default_factory=dict)

    @field_validator("role")
    @classmethod
    def ensure_supported_role(cls, value: str) -> str:
        allowed = {"authenticated", "admin", "manager"}
        if value not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(sorted(allowed))}")
        return value

    @field_validator("metadata", mode="after")
    @classmethod
    def enforce_metadata_size(cls, value: dict[str, object]) -> dict[str, object]:
        if len(str(value)) > 1_000:
            raise ValueError("Metadata too large (max 1000 characters)")
        return value
```

### Model Validators

```python
from pydantic import model_validator


class SupabaseUserData(BaseModel):
    role: str
    email_confirmed: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def ensure_consistent_state(self) -> "SupabaseUserData":
        if self.role == "admin" and not self.email_confirmed:
            raise ValueError("Admin users must have confirmed email addresses")
        if self.role == "manager" and "department" not in self.metadata:
            raise ValueError("Managers must include department metadata")
        return self
```

Model validators run after field validators, making them ideal for cross-field rules.

### Serializers & Computed Fields

```python
from pydantic import field_serializer


class AuditEntry(BaseModel):
    created_at: datetime

    @field_serializer("created_at")
    def serialize_timestamp(self, value: datetime) -> str:
        return value.isoformat()
```

Serializers ensure consistent API shape (ISO-8601 timestamps, masked secrets, etc.).

---

## Advanced Types & Adapters

### Annotated Constraints

```python
from typing import Annotated
from pydantic import AfterValidator


PositiveInt = Annotated[int, AfterValidator(lambda value: value if value > 0 else ValueError("must be > 0"))]


class Pagination(BaseModel):
    page: PositiveInt = 1
    page_size: PositiveInt = 25
```

Use `Annotated` with `BeforeValidator`/`AfterValidator` for reusable constraints.

### TypeAdapter for Bulk Validation

```python
from pydantic import TypeAdapter


UserListAdapter = TypeAdapter(list[UserResponse])


def validate_users(raw: object) -> list[UserResponse]:
    return UserListAdapter.validate_python(raw)
```

Type adapters are useful when validating data outside FastAPI handlers (e.g., Celery tasks).

### Discriminated Unions

```python
from typing import Literal


class SMSChannel(BaseModel):
    kind: Literal["sms"]
    phone_number: str


class EmailChannel(BaseModel):
    kind: Literal["email"]
    email: EmailStr


ChannelConfig = Annotated[SMSChannel | EmailChannel, Field(discriminator="kind")]
```

Discriminated unions allow you to represent branching logic cleanly (notifications, workflows, etc.).

---

## Working with SQLAlchemy

Use `from_attributes=True` to bridge ORM models to DTOs without manual `dict` conversions.

```python
class AppointmentResponse(BaseModel):
    id: str
    patient_id: str
    scheduled_for: datetime
    provider: str

    model_config = ConfigDict(from_attributes=True)


appointment = await appointment_repo.get(appt_id)
return AppointmentResponse.model_validate(appointment)
```

### Dumping Back to Primitives

```python
payload = user_update.model_dump(exclude_unset=True)
await user_repository.update(user_id, payload)
```

`exclude_unset=True` prevents overwriting values when partial updates are submitted.

### Transactions & Validation

- Validate incoming payloads before entering transactional blocks.
- Use services to convert raw dictionaries to Pydantic models before persisting.

---

## Error Handling & Messaging

FastAPI automatically raises `RequestValidationError` for invalid payloads. Our global handlers in `app/core/errors.py` convert these into `ErrorResponse` structures.

```python
@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = ErrorResponse(
        message="Validation failed",
        validation_errors=[ErrorDetail.model_validate(error) for error in exc.errors()],
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=details.model_dump())
```

**Best Practices**
- Raise custom domain errors (e.g., `DuplicateEmailError`) from services; map to HTTP in routers.
- Avoid catching `ValidationError` inside routers—let FastAPI bubble it up.
- Provide precise error messages; they surface directly in API clients and logs.

---

## Testing Validation

### Direct Model Tests

```python
import pytest
from pydantic import ValidationError


def test_user_create_requires_valid_email():
    with pytest.raises(ValidationError):
        UserCreate.model_validate({"supabase_id": "123", "email": "not-an-email"})


def test_user_update_normalizes_name():
    payload = UserUpdate.model_validate({"full_name": "  angelA  "})
    assert payload.full_name == "Angela"
```

### Router Tests (httpx + pytest-asyncio)

```python
@pytest.mark.asyncio
async def test_create_user_validation(async_client: AsyncClient):
    response = await async_client.post(
        "/api/users",
        json={"email": "invalid", "supabase_id": "123"},
    )
    assert response.status_code == 422
    assert response.json()["error"] is True
```

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|--------------|--------------|-----|
| Using plain dicts in services | Loses validation & type safety | Convert to `BaseModel` early (`UserCreate.model_validate(data)`) |
| Allowing extra fields | Hides typos; Supabase payloads drift silently | Set `extra="forbid"` in request models |
| Manual JSON parsing in routers | Duplicates FastAPI functionality | Accept `BaseModel` params and let FastAPI validate |
| Returning SQLAlchemy models directly | Exposes SQLAlchemy internals | Use response DTOs with `from_attributes=True` |
| Catching and suppressing `ValidationError` | Masks client issues | Allow FastAPI to emit 422 responses |

---

## Quick Reference

- Define Create/Update/Response DTOs per feature in `backend/app/schemas/`.
- Enable strict modes (`extra="forbid"`, `validate_assignment=True`) on inbound payloads.
- Utilize `field_validator`, `model_validator`, `computed_field`, and `field_serializer` for business rules.
- Use `model_validate()` + `model_dump()` to move between services, repositories, and routers.
- Lean on FastAPI’s automatic validation and global error handlers for consistent messaging.

---

**Related Files:**
- backend/app/schemas/user.py
- backend/app/core/errors.py
- backend/app/api/v1/users.py
