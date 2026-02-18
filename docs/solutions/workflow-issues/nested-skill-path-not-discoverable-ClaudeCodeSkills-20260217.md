---
module: Claude Code Skills
date: 2026-02-17
problem_type: workflow_issue
component: tooling
symptoms:
  - "Skills nested at .claude/skills/fin-guru/actions/{name}/SKILL.md may not be discovered"
  - "All 12 existing project skills use flat .claude/skills/{name}/SKILL.md pattern"
  - "Nested directory intermediate path fin-guru/actions/ doesn't match project convention"
root_cause: config_error
resolution_type: config_change
severity: medium
tags: [claude-code, skills, discovery, directory-structure, convention]
---

# Troubleshooting: Claude Code Skills Not Discoverable Due to Nested Directory Path

## Problem

Seven Finance Guru skills were created at a deeply nested path (`.claude/skills/fin-guru/actions/{skill-name}/SKILL.md`) following an architectural plan that organized skills under category subdirectories. This didn't match the project's existing flat convention and risked skills not being discoverable by Claude Code's skill system.

## Environment

- Module: Claude Code Skills Architecture
- Affected Component: `.claude/skills/` directory structure
- Date: 2026-02-17

## Symptoms

- Skills created at `.claude/skills/fin-guru/actions/{name}/SKILL.md` (depth 4) while all 12 existing working skills used `.claude/skills/{name}/SKILL.md` (depth 2)
- The `claude-code-guide` agent confirmed nested discovery is primarily designed for monorepo subdirectory scanning (`packages/frontend/.claude/skills/`), not arbitrary intermediate directories
- Plan specified `fin-guru/actions/` as an organizational grouping layer, but Claude Code's skill discovery doesn't guarantee resolution through arbitrary intermediate paths

## What Didn't Work

**Direct solution:** The problem was identified during a post-implementation review and fixed on the first attempt by flattening the directory structure.

## Solution

**Commands run:**
```bash
# Move all 7 skill directories from nested to flat path
for skill in fin-guru-create-doc fin-guru-checklist fin-guru-research \
  fin-guru-quant-analysis fin-guru-strategize fin-guru-compliance-review \
  fin-guru-learner-profile; do
  mv ".claude/skills/fin-guru/actions/$skill" ".claude/skills/$skill"
done

# Remove empty parent directories
rm -rf .claude/skills/fin-guru/actions
rmdir .claude/skills/fin-guru
```

**Before (risky):**
```
.claude/skills/fin-guru/actions/fin-guru-create-doc/SKILL.md
.claude/skills/fin-guru/actions/fin-guru-checklist/SKILL.md
.claude/skills/fin-guru/actions/fin-guru-research/SKILL.md
... (7 skills at depth 4)
```

**After (correct):**
```
.claude/skills/fin-guru-create-doc/SKILL.md
.claude/skills/fin-guru-checklist/SKILL.md
.claude/skills/fin-guru-research/SKILL.md
... (7 skills at depth 2, matching project convention)
```

## Why This Works

1. **ROOT CAUSE**: The plan designed a nested directory hierarchy (`fin-guru/actions/`) for organizational grouping, but Claude Code's skill discovery uses a flat scan pattern at `.claude/skills/{directory-name}/SKILL.md`. While nested discovery exists for monorepo workspace scanning, arbitrary intermediate directories (`fin-guru/actions/`) aren't guaranteed to be traversed.

2. **Why the solution works**: Moving skill directories to the flat pattern (`.claude/skills/fin-guru-{name}/SKILL.md`) matches how Claude Code natively discovers skills. The system immediately confirmed discovery — the skill list showed all 7 skills right after the move.

3. **Underlying issue**: The organizational grouping intent (grouping Finance Guru skills together) was solved at the wrong level. Instead of using subdirectories for grouping, the skill _names_ themselves carry the grouping via the `fin-guru-` prefix. This achieves the same organizational clarity without breaking discovery.

## Prevention

- Always match existing project skill conventions — check `ls .claude/skills/` for the established pattern before creating new skills
- Use name prefixes (e.g., `fin-guru-`) for logical grouping instead of subdirectories
- The canonical Claude Code skill path is: `.claude/skills/{skill-name}/SKILL.md` — one level deep from the skills directory
- When porting agent architectures, verify skill discoverability by checking the system's skill list after creation
- Agent YAML frontmatter `skills:` references use directory names, not full paths — keeping skills flat ensures name-based resolution works reliably

## Related Issues

- Promoted to Required Reading: [Critical Pattern #1](../patterns/critical-patterns.md#1-claude-code-skills-must-use-flat-directory-paths-always-required)
