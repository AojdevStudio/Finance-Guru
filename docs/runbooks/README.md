---
title: "Finance Guru runbooks"
description: "Current and historical operational procedures"
category: runbook
---

# Finance Guru runbooks

Runbooks document a repeatable procedure with explicit inputs, side effects,
and verification. The current repository has no supported automated weekly or
monthly personal-finance cadence.

## Current procedure

| Procedure | Status | Verification |
| --- | --- | --- |
| Refresh and review local data | Manual, owner-configured | Run the all-source command and inspect each source status. |

Start a local-data review with:

```bash
uv run python -m src.integrations.refresh_all --show
```

Omit `--show` only when the owner intends to request fresh provider data. A
non-zero exit status means at least one source failed; do not treat partial
success as your current portfolio snapshot.

## Historical material

[Quarterly Review](quarterly-review.md) is an archived description of the
retired agent-orchestrated workflow. It does not establish a current cadence or
an automated recommendation process.

## Adding a runbook

Before adding a recurring procedure, create an issue that names its owner,
inputs, external effects, data provenance, recovery path, and observable
success condition. A runbook must never infer a financial action from a stale
or partial data refresh.
