# Private fixture pattern for tests that need real-shape PII

When a test uses a real account number, real CSV filename, real account value, etc., **don't hardcode the literal**. Use a private fixture loader.

## The problem

Some tests pass the actual production values around just to exercise a code path:

```python
# tests/python/test_margin_metrics.py — current
csv_path = tmp_path / "Balances_for_Account_Z05724592.csv"
```

The test doesn't care that the account is `Z05724592`. It cares that the filename matches `Balances_for_Account_<id>.csv`. But committing the literal puts the real account number on GitHub forever.

## The pattern (Python)

### 1. Commit a fixture loader with safe defaults

```python
# tests/python/fixtures/_private.py — committed

"""Test fixtures that may have private overrides.

Loads real values from tests/python/fixtures/private/values.yaml if present
(gitignored). Falls back to safe placeholders so CI works without secrets.
"""

from __future__ import annotations
from pathlib import Path
import yaml

_DEFAULTS = {
    "account_id": "Z00000000",
    "balance_filename": "Balances_for_Account_Z00000000.csv",
    "positions_filename": "Portfolio_Positions_Jan-01-2026.csv",
    "history_filename": "History_for_Account_Z00000000.csv",
    "total_account_value": 100000.00,
}

_private_yaml = Path(__file__).parent / "private" / "values.yaml"
if _private_yaml.exists():
    _values = {**_DEFAULTS, **yaml.safe_load(_private_yaml.read_text())}
else:
    _values = _DEFAULTS

ACCOUNT_ID: str = _values["account_id"]
BALANCE_FILENAME: str = _values["balance_filename"]
POSITIONS_FILENAME: str = _values["positions_filename"]
HISTORY_FILENAME: str = _values["history_filename"]
TOTAL_ACCOUNT_VALUE: float = _values["total_account_value"]
```

### 2. Gitignore the private values file

```
# .gitignore
tests/python/fixtures/private/
```

### 3. Drop the real values into the gitignored YAML on your machine

```yaml
# tests/python/fixtures/private/values.yaml — NOT committed
account_id: "Z05724592"
balance_filename: "Balances_for_Account_Z05724592.csv"
positions_filename: "Portfolio_Positions_Nov-05-2025.csv"
history_filename: "History_for_Account_Z05724592.csv"
total_account_value: 228809.41
```

### 4. Refactor tests to import constants instead of hardcoding

```python
# tests/python/test_margin_metrics.py — after
from tests.python.fixtures._private import BALANCE_FILENAME

csv_path = tmp_path / BALANCE_FILENAME
```

## The pattern (TypeScript / bun)

Same shape, different file:

```typescript
// tests/fixtures/_private.ts — committed
import { existsSync, readFileSync } from "fs";
import { join } from "path";

const DEFAULTS = {
  totalAccountValue: 100000.0,
  positionsFilename: "Portfolio_Positions_Jan-01-2026.csv",
};

const privatePath = join(__dirname, "private", "values.json");
const values = existsSync(privatePath)
  ? { ...DEFAULTS, ...JSON.parse(readFileSync(privatePath, "utf-8")) }
  : DEFAULTS;

export const TOTAL_ACCOUNT_VALUE: number = values.totalAccountValue;
export const POSITIONS_FILENAME: string = values.positionsFilename;
```

## The pattern (bash)

Source an env file:

```bash
# tests/integration/test_gitignore_protection.sh — after
PRIVATE_ENV="${BASH_SOURCE%/*}/private/values.env"
[[ -f "$PRIVATE_ENV" ]] && source "$PRIVATE_ENV"

POSITIONS_FILE="${TEST_POSITIONS_FILENAME:-Portfolio_Positions_Jan-01-2026.csv}"
ACCOUNT_ID="${TEST_ACCOUNT_ID:-Z00000000}"

# ... use $POSITIONS_FILE and $ACCOUNT_ID instead of literals
```

```bash
# tests/integration/private/values.env — NOT committed
export TEST_POSITIONS_FILENAME="Portfolio_Positions_Nov-05-2025.csv"
export TEST_ACCOUNT_ID="Z05724592"
```

## Migration checklist

1. Create `tests/<lang>/fixtures/_private.<ext>` with defaults.
2. Add `tests/<lang>/fixtures/private/` to `.gitignore`.
3. Create the private values file on your local machine with real data.
4. `git grep -nE 'Z0\d{7}|228809\.41|Portfolio_Positions_\w+-\d+-\d+'` to find every literal that needs replacing.
5. Replace, re-run tests (they should still pass with real values).
6. Run `compliance-scan --scope tree` — those findings should drop to zero.
7. Commit the refactor.

## What does NOT belong in private fixtures

- Mortgage balances/payments — {user_name} has marked these as "doesn't matter" (acceptable in tests). No need to refactor.
- Owner name — handled by the existing `test_no_hardcoded_references.py` ALLOWED_FILES allowlist.
- Employer string in `tests/python/fixtures/fidelity_history_golden_expected.json` — allowlisted in `compliance-scan/allowlist.json` (golden fixture, accepted).
