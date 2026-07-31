---
title: "Transitional hooks"
description: "Status of the legacy Claude Code hook implementation"
category: reference
---

# Transitional hooks

The `.claude/hooks/` implementation is transitional and not a supported public
setup dependency. It may be useful to maintainers investigating the legacy
agent stack, but it does not define the stable analysis-engine contract.

Do not add or configure hooks based on older examples without first checking
the checked-in hook configuration and opening an issue. The public, durable
surfaces are the Python analysis engine, local database integrations, tests,
and the documentation linked from [the repository documentation hub](../index.md).

The standalone-app direction intentionally removes the Claude Code dependency;
see [the vision](../VISION.md).
