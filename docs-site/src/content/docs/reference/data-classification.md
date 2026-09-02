---
title: "Data classification"
description: "What may be written into a tracked file in the public Finance Guru repository."
sidebar:
  order: 5
---

The Finance Guru repository is public. Every file that is not gitignored is published to the internet the moment it is pushed. This page decides what may be written into a tracked file.

## The rule

Code and documentation describe behaviour. They never carry values.

Evidence in a document should be written as a shape rather than an amount, because the shape is what teaches the reader and the amount is what exposes the household. Percentages, ratios, multiples, counts, dates, and tickers all survive publication. They also age better, because a ratio stays true after the balance changes.

| Instead of | Write |
| --- | --- |
| an absolute equity figure and the corrected one | `as-synced equity understated the real figure by 8%` |
| a real total beside the inflated total reported | `inflated the review roughly 3x` |
| the true household spend total | `the true figure was 70% higher` |
| an income total across N payments | `30 payments, about 86% of the closed month` |
| a real employer inside a memo fixture | `DIRECT DEPOSIT ACME STAFFINGDIR DEP` |

## Classification table

| Class | Examples | Where it may live |
| --- | --- | --- |
| SECRET | API tokens, SnapTrade and SimpleFIN credentials, private keys | Secrets manager only. Never a file, not even gitignored. |
| PRIVATE | Account balances, equity, margin debt, income, spend totals, dividend amounts, account numbers and their last-four, provider account ids, employer names, payer names, household merchant names, share quantities, cost basis, addresses, phone numbers | Gitignored paths such as the local database and the instance directory. Never a tracked file. |
| INTERNAL | Strategy layer names, bucket structure, concentration limits as percentages, category taxonomies, workflow shapes | Tracked files are acceptable. These describe method, not position. |
| PUBLIC | Tickers, IRS bracket edges, published fund yields, library versions, round scenario values such as a `$50,000` portfolio or a `$500` contribution | Anywhere. |

The line between PRIVATE and PUBLIC for a currency amount is precision, not size. Documentation invents round numbers. Real money lands on arbitrary amounts and carries cents. `$50,000` is a scenario. An arbitrary six-figure amount, or any amount carrying cents, is a statement about a real household.

## Test fixtures

Fixtures assert on the shape of a memo, never on identity. A test proving that a direct-deposit memo tags as payroll works identically with a placeholder employer, so it uses one. A fixture that genuinely needs a real captured value goes in the scanner allowlist with a reason and an approval date.

## Enforcement

The compliance scanner flags precise currency amounts in tracked documentation and blocks a push at high severity. Two narrow escape hatches exist. Genuinely public reference data can be allowlisted by amount, and a whole path can carry an accepted exception. A household balance never belongs in either. Literal-matching layers only catch values that were enumerated, so the replacement list must name every household employer and payer as it appears.

_This page is built from `.claude/skills/compliance-scan/references/DataClassification.md` in the repository._
