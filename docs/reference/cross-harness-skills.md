---
title: Legacy agent-harness material
description: Status of the transitional Claude Code skills and hooks
category: reference
---

# Legacy agent-harness material

The checked-in `.claude/` skills, commands, and hooks are transitional
implementation material. They are not part of the supported public setup path
and are not a cross-harness distribution mechanism.

In particular, this repository does not contain tracked `.agents/skills/` or
`.pi/skills/` symlink trees. Do not create those paths by following older
documentation. A harness-specific integration belongs in an issue while the
standalone-app transition described in [the vision](../VISION.md) is underway.

The stable public surfaces are the Python analysis engine, its documented
commands, tests, and operational repository documentation. See
[Contributing](../CONTRIBUTING.md) for the current contribution boundaries.
