# Critical Patterns — Required Reading

These patterns represent lessons learned from real issues. All agents should review these before generating code or configuration that touches the affected areas.

---

## 1. Claude Code Skills Must Use Flat Directory Paths (ALWAYS REQUIRED)

### ❌ WRONG (Skills may not be discovered)
```
.claude/skills/category/subcategory/my-skill/SKILL.md
.claude/skills/fin-guru/actions/fin-guru-create-doc/SKILL.md
```

### ✅ CORRECT
```
.claude/skills/my-skill/SKILL.md
.claude/skills/fin-guru-create-doc/SKILL.md
```

**Why:** Claude Code discovers skills by scanning `.claude/skills/{directory-name}/SKILL.md` at depth 2. Nested intermediate directories (e.g., `category/subcategory/`) are not guaranteed to be traversed during discovery. Use name prefixes (e.g., `fin-guru-`) for logical grouping instead of subdirectories.

**Placement/Context:** When creating new Claude Code skills or porting agent capabilities into the skills architecture. Always check existing convention with `ls .claude/skills/` before creating new skills.

**Documented in:** `docs/solutions/workflow-issues/nested-skill-path-not-discoverable-ClaudeCodeSkills-20260217.md`
