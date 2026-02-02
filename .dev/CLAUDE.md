# .dev/ Directory Guide

The `.dev/` directory is the development planning workspace for specifications and technical designs.

## Structure

- `specs/backlog/` - Planned and in-progress specifications
- `specs/backlog/diagrams/` - Visual assets (Mermaid, PNG, SVG) for specs
- `specs/archive/` - Completed or abandoned specifications

## Specification Requirements

Every spec MUST include YAML frontmatter with ALL of the following fields. No field is optional.

```yaml
---
title: "Human-readable spec title"
status: backlog                    # backlog | in-progress | implemented | abandoned
created: 2026-02-01               # ISO date, set once at creation
updated: 2026-02-01               # ISO date, update on every edit
author: "Name"                     # Who wrote/owns this spec
spec_id: kebab-case-id            # Unique ID (matches filename without .md)
version: "1.0.0"                  # Semver - bump on significant changes
description: "One-liner"          # Brief purpose statement
tags:                             # For filtering and discovery
  - tag1
  - tag2
references:                       # Related specs or docs (relative paths)
  - path/to/related-spec.md
supersedes: []                    # Specs this replaces (empty array if none)
diagrams:                         # Visual assets (empty strings if none yet)
  human: ""                       # Path relative to spec location
  machine: ""                     # Path relative to spec location
---
```

### Frontmatter Rules

| Rule | Detail |
|------|--------|
| **ALL fields REQUIRED** | Every spec must have every field above. No exceptions. |
| **`spec_id` matches filename** | The `spec_id` value must match the filename without the `.md` extension. |
| **`diagrams` paths are relative** | Paths are relative from the spec file's location (e.g., `diagrams/my-spec-arch.png`). |
| **Diagram files location** | Diagram files live in the `diagrams/` subdirectory alongside specs. |
| **Diagram filenames** | Format: `{spec-slug}-{descriptor}.{ext}` (e.g., `facebook-livestream-scheduler-arch.mmd`). |
| **Empty collections** | `references` and `supersedes` use `[]` when empty, never omitted. |
| **Empty diagram paths** | `diagrams.human` and `diagrams.machine` use `""` when no diagram exists yet. |
| **`updated` field** | Must be updated to today's date on every edit to the spec. |
| **`version` bumping** | Bump the patch version for small changes, minor for structural changes, major for rewrites. |

## Status-Based Organization

| Status | Location |
|--------|----------|
| `backlog` | `specs/backlog/` |
| `in-progress` | `specs/backlog/` |
| `implemented` | `specs/archive/` |
| `abandoned` | `specs/archive/` |

## Naming Convention

Format: `{kebab-case-project}-{descriptor}.md`

Examples: `dental-analytics-api-architecture.md`, `shell-config-sync-spec.md`

## Creating New Specs

1. Always place in `specs/backlog/`
2. Populate ALL frontmatter fields (see template above)
3. Follow kebab-case naming convention
4. Ensure `spec_id` matches the filename (without `.md`)
5. Move to `specs/archive/` when status changes to `implemented` or `abandoned`
