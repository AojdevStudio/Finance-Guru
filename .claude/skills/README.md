# Skills

Each directory holds one skill as `<name>/SKILL.md`. Claude Code and Codex pick a skill from the `description` in its frontmatter, so the description is the routing rule. No hook or rules file routes prompts to skills.

## Write a description that routes

- Start with what the skill does, in plain words.
- Add a "Use when" sentence with the phrases an owner actually types.
- Add a "Not for" sentence that names the neighbouring skill to use instead.

`tests/python/test_skill_contract.py` checks these parts for the routed `fin-guru-*` skills. The sync skills carry "Use when" phrases but no test holds them yet.

## Shared patterns

`_shared/` holds patterns that several skills link to instead of restating, such as the sync-first database read and the paid MCP capability probe.

The analysis answer shape is the `fin-guru-output-contract` skill. It is model-invocable, and every agent preloads it by listing `fin-guru-output-contract` under `skills:` in its frontmatter. Claude Code injects the full skill at startup. Each Return section adds only that role's rules.
