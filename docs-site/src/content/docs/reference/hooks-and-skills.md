---
title: "Hooks and skills"
description: "Status of the transitional agent-harness hooks and skills."
sidebar:
  order: 4
---

The checked-in `.claude/` skills, commands, and hooks are transitional implementation material. They are not part of the supported public setup path and are not a cross-harness distribution mechanism.

## Hooks

The `.claude/hooks/` implementation is transitional and not a supported public setup dependency. It may be useful to maintainers investigating the legacy agent stack, but it does not define the stable analysis-engine contract. Do not add or configure hooks based on older examples without first checking the checked-in hook configuration and opening an issue.

The public, durable surfaces are the Python analysis engine, local database integrations, tests, and repository documentation. The standalone-app direction intentionally removes the [Claude Code](https://code.claude.com/) dependency.

## Skills

The repository ships specialist skills under `.claude/skills/`, including portfolio syncing, transaction syncing, dividend tracking, margin management, report generation, and the compliance scanner. They remain usable inside an agent harness but sit on the transitional side of the product boundary.

This repository does not contain tracked `.agents/skills/` or `.pi/skills/` symlink trees. Do not create those paths by following older documentation. A harness-specific integration belongs in an issue while the standalone-app transition is underway.

## Planned plugin packaging

An installable Claude Code and [Codex](https://github.com/openai/codex) plugin surface is planned but not on the default branch. It will package the skills and agents with capability probes for the workflows that currently hard-require personal paid MCP integrations. Until it lands, treat any plugin-install instructions as planned, not shipped. See [the open-core position](../../explanation/open-core/) for the surrounding decisions.

_This page is built from `docs/reference/hooks.md` and `docs/reference/cross-harness-skills.md` in the repository._
