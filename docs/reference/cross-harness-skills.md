---
title: Cross-Harness Skills
description: How Finance Guru skills work across Claude Code, pi-coding-agent, and any Agent Skills-compatible harness
last-reviewed: 2026-04-17
---

# Cross-Harness Skills

Finance Guru skills are portable. The same `SKILL.md` files work in Claude Code, pi-coding-agent, and any harness that follows the [Agent Skills standard](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/sdk.md). This is enabled by a **multi-path symlink fanout** from a single source of truth.

## Directory layout

```
family-office/
├── .claude/skills/              # real skill files (where they have lived since day one)
│   ├── fin-core/SKILL.md
│   ├── margin-management/SKILL.md
│   ├── MonteCarlo/SKILL.md
│   └── … (19 Finance Guru skills total)
│
├── .agents/skills/              # shared / cross-harness view
│   ├── fin-core -> ../../.claude/skills/fin-core            (symlink)
│   ├── margin-management -> ../../.claude/skills/margin-management
│   ├── MonteCarlo -> ../../.claude/skills/MonteCarlo
│   └── opentui, readiness-report, …                         (native to .agents/)
│
└── .pi/skills -> ../.agents/skills                           (single top-level symlink)
```

## Why this works

Each supported harness reads skills from a path already in the tree:

| Harness | Path it reads | Resolves to |
|---------|---------------|-------------|
| Claude Code | `.claude/skills/` | Real files |
| pi-coding-agent | `.pi/skills/` | `.pi/skills → .agents/skills → (each symlink) → .claude/skills/` |
| pi-coding-agent (fallback) | `.agents/skills/` (searched upward from cwd) | Direct |
| Anything following Agent Skills standard | `.agents/skills/` | Direct |
| User global | `~/.agents/skills/` or `~/.pi/agent/skills/` | Out of scope — user-level config |

## Adding a new skill

1. Create the skill under `.claude/skills/<name>/SKILL.md` (follows Claude Code conventions)
2. Add the symlink:
   ```bash
   cd .agents/skills
   ln -s ../../.claude/skills/<name> <name>
   ```
3. Verify:
   ```bash
   [ -f .agents/skills/<name>/SKILL.md ] && echo "OK" || echo "broken"
   [ -f .pi/skills/<name>/SKILL.md ] && echo "OK" || echo "broken"
   ```
4. Commit the symlink. Git tracks it as a symlink ref — portable across Unix-like systems.

## SKILL.md format (harness-neutral)

Every `SKILL.md` uses the same Markdown frontmatter + body structure:

```markdown
---
name: my-skill
description: One-sentence description. USE WHEN user mentions X OR Y OR Z.
triggers:
  - keyword one
  - keyword two
---

# My Skill

Use this skill when the user wants to do X.

## Workflow

1. Step one
2. Step two
3. Step three
```

Claude Code reads `description` + `triggers` for auto-activation routing.
pi-coding-agent reads `description` for its `/skill:<name>` autocomplete and the body as the prompt to inject when the skill is activated.
Both treat the file as Markdown — no JSON schema enforced.

## Harness-specific extensions

If a skill needs a harness-specific integration point (e.g., Claude Code hooks, pi-coding-agent extension TypeScript), keep that code next to the skill under an explicitly named subdirectory:

```
.claude/skills/my-skill/
├── SKILL.md                       # harness-neutral
├── claude-code/
│   └── hooks.ts                   # Claude Code-specific
└── pi/
    └── extension.ts               # pi-coding-agent-specific
```

Each harness only loads the subdirectory relevant to it. The shared `SKILL.md` stays portable.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `.agents/skills/<name>/SKILL.md` fails to read | Check the symlink with `readlink .agents/skills/<name>`; recreate with correct relative path |
| Claude Code sees the skill, pi-coding-agent does not | Confirm pi is running from inside the repo (pi searches parent dirs upward for `.pi/skills/` and `.agents/skills/`) |
| A skill works in pi but not Claude Code | Claude Code reads `triggers:` frontmatter — make sure the frontmatter is valid YAML |
| Symlink committed but not resolving on a teammate's clone | Git preserves symlinks on Linux / macOS. On Windows, enable `core.symlinks=true` globally |

## Related

- `.claude/skills/` — primary skill files
- `.agents/skills/` — shared view, searched by any Agent-Skills-compatible harness
- `.pi/skills/` — pi-coding-agent native path (top-level symlink)
- [pi-mono skill docs](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/README.md)
- [Agent Skills standard reference](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/sdk.md)
