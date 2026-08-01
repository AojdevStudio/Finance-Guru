---
title: "Historical quarterly-review runbook"
description: "Status of the retired agent-orchestrated quarterly workflow"
category: runbook
---

# Historical quarterly-review runbook

The previous quarterly-review procedure depended on the transitional
agent/hook stack and retired file-export workflows. It is preserved only as a
historical reference and must not be treated as a current automated process.

For a current review, first refresh the configured local sources, inspect the
source statuses, then run only the analysis commands relevant to the question:

```bash
uv run python -m src.integrations.refresh_all
```

Use [the CLI reference](../reference/api.md) for supported analysis entry
points. Any future recurring review workflow needs an issue, explicit data
provenance, and a verification path before it can replace this archived page.
