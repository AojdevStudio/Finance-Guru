---
title: "The privacy model"
description: "How Finance Guru keeps household financial data local while running in a public repository."
sidebar:
  order: 3
---

Finance Guru handles the most sensitive data a household has, inside a repository anyone can read. The privacy model resolves that tension with three ideas. Data stays local. The public tree describes behaviour, never values. Machines, not habits, enforce the boundary.

## Data stays local

All financial data stays on the owner's machine. There is no telemetry, no remote analytics, and no third-party data sharing. Positions, balances, transactions, and dividend events land in the local, gitignored SQLite database. The profile and every generated artifact live in the instance directory, which has its own local git repository with no remote.

Data leaves the machine in only three ways. Broker and bank reads go outbound to SnapTrade and SimpleFIN, both read-only against your own accounts. Market-data providers see which tickers you query, but not your position sizes. An agent-harness session sees whatever you paste into it, so treat it like a privileged assistant and do not paste what you would not email your accountant.

## The tree describes behaviour, never values

Gitignore rules protect files, but a number can leak through prose. A commit once carried real equity, spending, and employer names through a clean scan, because the scanner had never been told that a number can be private because of what it means. The answer is the classification policy. Evidence is written as shapes, such as ratios and percentages, rather than amounts. The full rule and its enforcement live in the [data classification reference](../../reference/data-classification/).

## Machines enforce the boundary

The compliance scanner runs before a push and fails closed. It layers literal matching for known credentials and names, pattern matching for tokens and account numbers, and a financial-figure layer that blocks precise currency amounts in tracked documentation. The structured logger scrubs personally identifying patterns before they reach any log. The instance split removes the strongest temptation, because private files no longer live where a commit could reach them.

## What this means for you

Run your instance outside the checkout. Keep credentials in the local environment file. Let the scanner gate your pushes. Inspect diffs before committing anyway, because the scanner's literal layers only catch what has been enumerated.

## Important notice

Finance Guru provides educational analysis only. It is not investment, tax, or legal advice. Financial markets involve risk, including loss of principal. Consult appropriately licensed professionals for decisions about your assets.

_This page is built from `PRIVACY.md` and `.claude/skills/compliance-scan/references/DataClassification.md` in the repository._
