# Data Classification

`AojdevStudio/Finance-Guru` is a **public** repository. Finance Guru is a private
family office running on it. Every file that is not gitignored is published to
the internet the moment it is pushed.

This page decides what may be written into a tracked file. It exists because on
2026-08-31 a clean compliance scan passed a commit carrying account equity,
monthly household spending, dividend income, and five employer names into a
public pull request. Nothing in the scanner was broken. It had simply never been
told that a number can be private because of what it means.

## The rule

**Code and documentation describe behaviour. They never carry values.**

A skill document explaining a sync bug is better with evidence, and that
evidence is what leaks. The fix is not to drop the evidence. It is to write the
evidence as a shape rather than an amount, because the shape is what teaches the
reader and the amount is what exposes the household.

| Instead of | Write |
| --- | --- |
| an absolute equity figure and the corrected one | `as-synced equity understated the real figure by 8%` |
| a real total beside the inflated total reported | `inflated the review roughly 3x` |
| the true household spend total | `the true figure was 70% higher` |
| an income total across N payments | `30 payments, about 86% of the closed month` |
| a real employer inside a memo fixture | `DIRECT DEPOSIT ACME STAFFINGDIR DEP` |

The left column names shapes instead of showing values, because an example of
a leak is still a leak. The right column is the whole lesson.

Percentages, ratios, multiples, counts, dates, and tickers all survive
publication. They also age better, because a ratio stays true after the balance
changes.

## Classification table

| Class | Examples | Where it may live |
| --- | --- | --- |
| **SECRET** | API tokens, `BWS_ACCESS_TOKEN`, SnapTrade and SimpleFIN credentials, private keys | BWS only. Never a file, not even gitignored. |
| **PRIVATE** | Account balances, equity, margin debt, income, spend totals, dividend amounts, account numbers and their last-four, SnapTrade or SimpleFIN account ids, employer names, payer names, merchant names tied to the household, share quantities, cost basis, addresses, phone numbers | `family_office.db`, `fin-guru-private/`, `notebooks/`, and other gitignored paths. Never a tracked file. |
| **INTERNAL** | Strategy layer names, bucket structure, concentration limits as percentages, category taxonomies, workflow shapes | Tracked files are acceptable. These describe method, not position. |
| **PUBLIC** | Tickers, IRS bracket edges, published fund yields, library versions, round scenario values (`$50,000` portfolio, `$500` contribution) | Anywhere. |

The line between PRIVATE and PUBLIC for a currency amount is precision, not
size. Documentation invents round numbers. Real money lands on arbitrary amounts
and carries cents. `$50,000` is a scenario. An arbitrary six-figure amount, or
any amount carrying cents, is a statement about a real household.

## Test fixtures

Fixtures assert on the **shape** of a memo, never on identity. A test proving
that `DIRECT DEPOSIT ...DIR DEP` tags as payroll works identically with a
placeholder employer, so it uses one. If a fixture genuinely needs a real
captured value, it goes in `allowlist.json` with a reason and an approval date.

## How this is enforced

Prose alone does not hold. Layer 7 of `scripts/scan.py`
(`scan_layer7_financial_figures`) flags precise currency amounts in tracked
documentation under `.claude/skills/`, `.claude/commands/`, `.dev/`, `.memory/`,
and `docs/`. It fires at HIGH, which blocks a push.

Two escape hatches, both deliberate and both narrow. Genuinely public reference
data goes in `allowed_amounts` in `allowlist.json`. A whole path with an
accepted exception goes in `allow`. A household balance never belongs in either.

Layers 3 and 4 match known literals, so they only catch a value someone already
enumerated. That is why `pii-replacements.txt` must list every household
employer and payer name as it appears. A name absent from that file is invisible
to the scanner regardless of how sensitive it is.
