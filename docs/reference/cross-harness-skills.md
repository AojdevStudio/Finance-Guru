---
title: Skills across harnesses
description: Where skills live and how Claude Code and Codex reach them
category: reference
---

# Skills across harnesses

Finance skills live in one place, `.claude/skills/<name>/SKILL.md`, and ship in the plugin. [Claude Code](https://code.claude.com/) discovers them from the plugin or from the checkout instance's local `.claude/skills` link. [Codex](https://github.com/openai/codex) reaches the same files through the `.agents` symlink that `src.cli.instance_init` points at the local runtime view. A Codex session started from the instance discovers skills under `./.agents/skills`. A plugin-mode instance omits the discovery link because the installed plugin is the source of skills.

Repository PR tools live under `.dev/pr-kit`, outside the finance skill tree.
The repository's instructions name their `SKILL.md` files explicitly. They are
developer workflows, outside the plugin manifest and instance discovery paths.
Instance settings run only the product session hook and do not inherit the
repository's developer hooks or instructions.

This repository tracks no `.agents/` or `.pi/` tree. Do not create one. A harness that needs a different discovery path gets an issue, not a second copy of the skills.

A delegated subagent preloads a skill when its frontmatter lists the skill's directory name under `skills:`. Claude Code injects the full `SKILL.md` for that subagent, which requires the skill to stay model-invocable (`disable-model-invocation` stays unset). Claude Code 2.1.289 does not inject `skills:` when you start that agent as the main session with `--agent`. `fin-guru-output-contract` stays on every agent's `skills:` list for delegation, and each Return section also carries the six-part contract so the main-session prompt has it. Codex reads the same file through the `.agents` symlink when the agent names the skill.

See [AGENTS.md](../../AGENTS.md) for the operating rules every harness follows.
