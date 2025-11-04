# Async Patterns and Error Handling

Complete guide to async/await patterns and custom error handling.

## Table of Contents

- [Async/Await Best Practices](#asyncawait-best-practices)
- [Promise Error Handling](#promise-error-handling)
- [Custom Error Types](#custom-error-types)
- [asyncErrorWrapper Utility](#asyncerrorwrapper-utility)
- [Error Propagation](#error-propagation)
- [Common Async Pitfalls](#common-async-pitfalls)

---

## Async/Await Best Practices

### Always Use Try-Catch

```typescript
// ❌ NEVER: Unhandled async errors
async function fetchData() {
    const data = await database.query(); // If throws, unhandled!
    return data;
}

// ✅ ALWAYS: Wrap in try-catch
async function fetchData() {
    try {
        const data = await database.query();
        return data;
    } catch (error) {
        Sentry.captureException(error);
        throw error;
    }
}
```

### Avoid .then() Chains

```typescript
// ❌ AVOID: Promise chains
function processData() {
    return fetchData()
        .then(data => transform(data))
        .then(transformed => save(transformed))
        .catch(error => {
            console.error(error);
        });
}

// ✅ PREFER: Async/await
async function processData() {
    try {
        const data = await fetchData();
        const transformed = await transform(data);
        return await save(transformed);
    } catch (error) {
        Sentry.captureException(error);
        throw error;
    }
}
```

---

## Promise Error Handling

### Parallel Operations

```typescript
// ✅ Handle errors in Promise.all
try {
    const [users, profiles, settings] = await Promise.all([
        userService.getAll(),
        profileService.getAll(),
        settingsService.getAll(),
    ]);
} catch (error) {
    // One failure fails all
    Sentry.captureException(error);
    throw error;
}

// ✅ Handle errors individually with Promise.allSettled
const results = await Promise.allSettled([
    userService.getAll(),
    profileService.getAll(),
    settingsService.getAll(),
]);

results.forEach((result, index) => {
    if (result.status === 'rejected') {
        Sentry.captureException(result.reason, {
            tags: { operation: ['users', 'profiles', 'settings'][index] }
        });
    }
});
```

---

## Custom Error Types

### Define Custom Errors

```typescript
// Base error class
export class AppError extends Error {
    constructor(
        message: string,
        public code: string,
        public statusCode: number,
        public isOperational: boolean = true
    ) {
        super(message);
        this.name = this.constructor.name;
        Error.captureStackTrace(this, this.constructor);
    }
}

// Specific error types
export class ValidationError extends AppError {
    constructor(message: string) {
        super(message, 'VALIDATION_ERROR', 400);
    }
}

export class NotFoundError extends AppError {
    constructor(message: string) {
        super(message, 'NOT_FOUND', 404);
    }
}

export class ForbiddenError extends AppError {
    constructor(message: string) {
        super(message, 'FORBIDDEN', 403);
    }
}

export class ConflictError extends AppError {
    constructor(message: string) {
        super(message, 'CONFLICT', 409);
    }
}
```

### Usage

```typescript
// Throw specific errors
if (!user) {
    throw new NotFoundError('User not found');
}

if (user.age < 18) {
    throw new ValidationError('User must be 18+');
}

// Error boundary handles them
function errorBoundary(error, req, res, next) {
    if (error instanceof AppError) {
        return res.status(error.statusCode).json({
            error: {
                message: error.message,
                code: error.code
            }
        });
    }

    // Unknown error
    Sentry.captureException(error);
    res.status(500).json({ error: { message: 'Internal server error' } });
}
```

---

## asyncErrorWrapper Utility

### Pattern

```typescript
export function asyncErrorWrapper(
    handler: (req: Request, res: Response, next: NextFunction) => Promise<any>
) {
    return async (req: Request, res: Response, next: NextFunction) => {
        try {
            await handler(req, res, next);
        } catch (error) {
            next(error);
        }
    };
}
```

### Usage

```typescript
// Without wrapper - error can be unhandled
router.get('/users', async (req, res) => {
    const users = await userService.getAll(); // If throws, unhandled!
    res.json(users);
});

// With wrapper - errors caught
router.get('/users', asyncErrorWrapper(async (req, res) => {
    const users = await userService.getAll();
    res.json(users);
}));
```

---

## Error Propagation

### Proper Error Chains

```typescript
// ✅ Propagate errors up the stack
async function repositoryMethod() {
    try {
        return await PrismaService.main.user.findMany();
    } catch (error) {
        Sentry.captureException(error, { tags: { layer: 'repository' } });
        throw error; // Propagate to service
    }
}

async function serviceMethod() {
    try {
        return await repositoryMethod();
    } catch (error) {
        Sentry.captureException(error, { tags: { layer: 'service' } });
        throw error; // Propagate to controller
    }
}

async function controllerMethod(req, res) {
    try {
        const result = await serviceMethod();
        res.json(result);
    } catch (error) {
        this.handleError(error, res, 'controllerMethod'); // Final handler
    }
}
```

---

## Common Async Pitfalls

### Fire and Forget (Bad)

```typescript
// ❌ NEVER: Fire and forget
async function processRequest(req, res) {
    sendEmail(user.email); // Fires async, errors unhandled!
    res.json({ success: true });
}

// ✅ ALWAYS: Await or handle
async function processRequest(req, res) {
    try {
        await sendEmail(user.email);
        res.json({ success: true });
    } catch (error) {
        Sentry.captureException(error);
        res.status(500).json({ error: 'Failed to send email' });
    }
}

// ✅ OR: Intentional background task
async function processRequest(req, res) {
    sendEmail(user.email).catch(error => {
        Sentry.captureException(error);
    });
    res.json({ success: true });
}
```

### Unhandled Rejections

```typescript
// ✅ Global handler for unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
    Sentry.captureException(reason, {
        tags: { type: 'unhandled_rejection' }
    });
    console.error('Unhandled Rejection:', reason);
});

process.on('uncaughtException', (error) => {
    Sentry.captureException(error, {
        tags: { type: 'uncaught_exception' }
    });
    console.error('Uncaught Exception:', error);
    process.exit(1);
});
```

---

**Related Files:**
- [SKILL.md](SKILL.md)
- [sentry-and-monitoring.md](sentry-and-monitoring.md)
- [complete-examples.md](complete-examples.md)

# Async Patterns and Error Handling (Python/FastAPI)

Complete guide to `async/await` and robust error handling for FastAPI + Starlette with `asyncio`, `sentry_sdk`, and layered services.

## Table of Contents

- [Async/Await Best Practices](#asyncawait-best-practices)
- [Coroutine Error Handling](#coroutine-error-handling)
- [Custom Error Types](#custom-error-types)
- [async_error_wrapper Utility](#async_error_wrapper-utility)
- [Error Propagation](#error-propagation)
- [Common Async Pitfalls](#common-async-pitfalls)

---

## Async/Await Best Practices

### Always Use try/except

```python
# ❌ NEVER: Unhandled async errors
async def fetch_data():
    data = await database.query()  # If this raises, it's unhandled
    return data

# ✅ ALWAYS: Wrap in try/except and capture
import sentry_sdk

async def fetch_data():
    try:
        return await database.query()
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        raise
```

### Prefer async/await over callback-style chains

```python
# ❌ AVOID: Callback/then-style composition in Python
# (Not idiomatic; shown only for symmetry with JS)

# ✅ PREFER: Straight-line async/await
async def process_data():
    try:
        data = await fetch_data()
        transformed = await transform(data)
        return await save(transformed)
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        raise
```

---

## Coroutine Error Handling

### Parallel Operations

```python
import asyncio

# ✅ Fail-fast with asyncio.gather (default). One failure fails all.
try:
    users, profiles, settings = await asyncio.gather(
        user_service.get_all(),
        profile_service.get_all(),
        settings_service.get_all(),
    )
except Exception as exc:
    sentry_sdk.capture_exception(exc)
    raise

# ✅ Handle each result individually with return_exceptions=True
results = await asyncio.gather(
    user_service.get_all(),
    profile_service.get_all(),
    settings_service.get_all(),
    return_exceptions=True,
)
labels = ("users", "profiles", "settings")
for idx, res in enumerate(results):
    if isinstance(res, Exception):
        sentry_sdk.capture_exception(res)
        # Optionally log label: labels[idx]
```

---

## Custom Error Types

### Define Custom Errors

```python
# app/errors/exceptions.py
from typing import Optional

class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int, *, is_operational: bool = True):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.is_operational = is_operational

class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 400)

class NotFoundError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "NOT_FOUND", 404)

class ForbiddenError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "FORBIDDEN", 403)

class ConflictError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT", 409)
```

### Global Exception Handler (FastAPI)

```python
# app/errors/handlers.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sentry_sdk
from app.errors.exceptions import AppError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"message": exc.message, "code": exc.code}},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(_: Request, exc: Exception):
        sentry_sdk.capture_exception(exc)
        return JSONResponse(status_code=500, content={"error": {"message": "Internal server error"}})
```

---

## async_error_wrapper Utility

Although FastAPI has global exception handlers, a small decorator can standardize controller-level error forwarding.

```python
# app/utils/async_error_wrapper.py
from typing import Awaitable, Callable, TypeVar
from fastapi import HTTPException
import sentry_sdk

F = TypeVar("F", bound=Callable[..., Awaitable])

def async_error_wrapper(handler: F) -> F:  # type: ignore[misc]
    async def _inner(*args, **kwargs):
        try:
            return await handler(*args, **kwargs)
        except HTTPException:  # already mapped
            raise
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            raise
    return _inner  # type: ignore[return-value]
```

### Usage

```python
# app/routes/user_routes.py
from fastapi import APIRouter, Depends
from app.utils.async_error_wrapper import async_error_wrapper
from app.controllers.user_controller import UserController
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
controller = UserController()

@router.get("/users")
@async_error_wrapper
async def list_users(session: AsyncSession = Depends(get_session)):
    return await controller.list_users(session)
```

---

## Error Propagation

### Proper Error Chains Across Layers

```python
# app/repositories/user_repository.py
import sentry_sdk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_many(self):
        try:
            result = await self.session.execute(select(User))
            return result.scalars().all()
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            raise  # Propagate to service
```

```python
# app/services/user_service.py
import sentry_sdk
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def list_users(self):
        try:
            return await self.repo.find_many()
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            raise  # Propagate to controller
```

```python
# app/controllers/user_controller.py
from fastapi import HTTPException, status
import sentry_sdk

class UserController:
    async def list_users(self, session):
        try:
            from app.services.user_service import UserService
            service = UserService(session)
            users = await service.list_users()
            return users
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            # Let global handler catch; or map explicitly:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list users")
```

---

## Common Async Pitfalls

### Fire-and-Forget (Bad) vs Background Tasks

```python
# ❌ NEVER: Fire-and-forget without handling exceptions
async def process_request(user):
    send_email(user.email)  # not awaited; exceptions lost
    return {"success": True}

# ✅ ALWAYS: Await or handle exceptions
async def process_request(user):
    try:
        await send_email(user.email)
        return {"success": True}
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        return {"error": "Failed to send email"}

# ✅ INTENTIONAL background work with FastAPI BackgroundTasks
from fastapi import BackgroundTasks

async def process_request(user, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, user.email)
    return {"success": True}

# ✅ Or create an observed task
import asyncio

def safe_create_task(coro):
    task = asyncio.create_task(coro)
    task.add_done_callback(lambda t: sentry_sdk.capture_exception(t.exception()) if t.exception() else None)
    return task
```

### Unhandled Exceptions in AsyncIO

```python
# ✅ Set a global exception handler for the event loop (optional)
import asyncio, logging

logger = logging.getLogger(__name__)

def handle_async_exception(loop, context):
    exc = context.get("exception")
    if exc is not None:
        import sentry_sdk
        sentry_sdk.capture_exception(exc)
    logger.error("Unhandled asyncio exception: %s", context)

loop = asyncio.get_event_loop()
loop.set_exception_handler(handle_async_exception)
```

### FastAPI/Starlette Integration with Sentry (optional)

```python
# app/main.py
import sentry_sdk
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.errors.handlers import register_exception_handlers

sentry_sdk.init(dsn="<your_dsn>")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# include routers...
register_exception_handlers(app)
```

---

**Related Files:**
- [SKILL.md](SKILL.md)
- [sentry-and-monitoring.md](sentry-and-monitoring.md)
- [complete-examples.md](complete-examples.md)
