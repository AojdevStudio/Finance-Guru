---
title: Observability
description: Structured logging, PII scrubbing, and feature flags for Finance Guru
last-reviewed: 2026-04-17
---

# Observability

Finance Guru ships with a small, opinionated observability layer. Two modules live under `src/utils/`:

| Module | Purpose |
|--------|---------|
| `src/utils/logging.py` | Structured logging via _structlog_ with built-in PII scrubbing |
| `src/utils/feature_flags.py` | Env-var-driven feature flag system |

## Structured logging

Replace `print()` in any CLI tool or long-running script with the structured logger:

```python
from src.utils.logging import get_logger

log = get_logger(__name__)
log.info("analysis_started", ticker="TSLA", days=90, benchmark="SPY")
log.warning("coverage_below_threshold", coverage=1.8, threshold=2.0)
```

Output adapts to the runtime:

- _Interactive TTY_ — colorized, human-friendly console format
- _CI / piped stderr_ — newline-delimited JSON suitable for log aggregators

## PII scrubbing

The logger runs every string value through a PII scrubber before rendering. The following patterns are redacted:

| Pattern | Redacted to |
|---------|-------------|
| SSN (`NNN-NN-NNNN`) | `***-**-****` |
| 13-19 digit sequences (credit cards) | `****` |
| API tokens (`sk-`, `pk-`, `ghp_`, `ghs_` prefixes) | first 4 chars + `***` |
| Email addresses | `***@domain.tld` (local part only) |

Need to redact something else? Extend `src/utils/logging.py:ScrubPIIProcessor` — add a regex and unit-test it under `tests/python/test_logging.py`.

## Feature flags

Gate experimental code paths without a full flag platform:

```python
from src.utils.feature_flags import flags

if flags.enabled("NEW_HEDGING_MODEL"):
    run_experimental_path()
else:
    run_stable_path()
```

Flags are read from environment variables prefixed `FG_FLAG_`. Truthy values are `1`, `true`, `yes`, `on` (case-insensitive).

```bash
export FG_FLAG_NEW_HEDGING_MODEL=true
uv run python src/analysis/hedge_sizer_cli.py --portfolio-value 200000
```

`flags.all_enabled()` returns a snapshot of every flag currently set in the environment — useful at startup for logging the active feature set.

## When to use which

| Need | Use |
|------|-----|
| Debug a single CLI run | `print()` is fine |
| Emit structured events for later analysis | `get_logger()` |
| Audit who changed what and when | `get_logger()` + `structlog.contextvars.bind_contextvars` |
| A/B a new calculation | `flags.enabled()` |
| Remote config, percentage rollout, user targeting | Graduate to LaunchDarkly, Statsig, or Unleash |

## Related

- `.github/workflows/quality-gates.yml` — tech-debt, dead-code, and duplicate scanning
- `docs/runbooks/` — operational procedures that benefit from structured logs
