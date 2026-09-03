---
title: Skills across harnesses
description: Where skills live and how Claude Code and Codex reach them
category: reference
---

# Skills across harnesses

Skills live in one place, `.claude/skills/<name>/SKILL.md`, and ship in the plugin. [Claude Code](https://code.claude.com/) discovers them from the plugin or from the checkout's `.claude` tree. [Codex](https://github.com/openai/codex) reaches the same files through the `.agents` symlink that `src.cli.instance_init` creates in a checkout-mode instance, so a Codex session started from the instance discovers skills under `./.agents/skills`. A plugin-mode instance omits the symlink because the installed plugin is the source of skills.

This repository tracks no `.agents/` or `.pi/` tree. Do not create one. A harness that needs a different discovery path gets an issue, not a second copy of the skills.

See [AGENTS.md](../../AGENTS.md) for the operating rules every harness follows.
