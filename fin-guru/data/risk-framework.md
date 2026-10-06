<!-- Finance Guru(tm) Risk Framework | v1.0 | 2026-10-06 -->

# Risk Framework

## Disclaimer

This document is for _educational purposes only_ and does not constitute investment advice. Portfolio limits below are the published methodology the specialists apply. They are not a guarantee against loss. Consult a licensed financial advisor before acting. Past performance does not guarantee future results.

Personal dollar thresholds, concentration exceptions, and account-specific buffers live in the instance directory, not in this file.

---

## Portfolio-level limits

A position increase uses the 20% clearance limit below. The 10% target and the 30% deployment cap govern different decisions.

| Limit | Rule | What it governs |
| --- | --- | --- |
| Single-position monitoring target | 10% of the total portfolio | A balanced-book watch level. Weight above 10% is a note on the review. |
| Single-position clearance limit | 20% of the total portfolio | A position increase. Approve it on concentration grounds when the post-increase weight is at or under 20%. |
| Deployment cap | 30% of pre-borrow equity NAV | A new buy-ticket deployment. Weight from 20% to 30% still fails a position-increase clearance. |
| Portfolio 1-day VaR | 2% of portfolio value at 95% confidence | The whole portfolio. A single name's daily VaR uses the 5% threshold in the ITC workflow. |
| Maximum drawdown | 15% peak to trough | The portfolio. |
| Leverage | 2:1 maximum for a conservative strategy | Gross leverage. |

The worked increase in `.claude/skills/fin-guru-compliance-review/itc-divergence.md` finishes at 15.5%. That weight is inside the 20% clearance limit and above the 10% monitoring target, so the record notes the target and the verdict stays APPROVE WITH NOTE under DR-2.

An instance file may name a tighter cap or a named exception. Cite that record in the compliance record. This file does not list those names or amounts. With no citation, the 20% clearance limit stands. A cited exception is the approval path for an increase whose post-increase weight is above 20%.

## Asset-class ranges

| Sleeve | Range |
| --- | --- |
| Equity | 60–80% for a balanced strategy |
| Fixed income | 20–40% |
| Alternatives | 20% maximum |
| Cash and equivalents | 5% minimum, for liquidity |
| Sector concentration | 25% maximum |

## Escalation

Measure a hard gate against its own limit. Hard gates are the 20% clearance limit, the 30% deployment cap, portfolio VaR, maximum drawdown, and the leverage limit.

| Level | Utilization | Action |
| --- | --- | --- |
| 1 — Alert | 75% of a hard gate, or any weight above the 10% monitoring target | Name the limit and the metric. Increase monitoring. |
| 2 — Warning | 90% of a hard gate | Stop adding exposure that consumes that gate until the review is done. |
| 3 — Breach | 100% of a hard gate | Immediate corrective action. Do not wait for the next review. |

Weight above the 10% monitoring target is a level 1 note. It stays a note while the post-increase weight is at or under the 20% clearance limit and the ITC rule is DR-1 or DR-2.

An emergency is a systematic loss that threatens the portfolio's ability to meet its liquidity floor. Preserve cash, reduce the position that breached, and record the hedge decision separately under `hedging-strategies.md`.

## What a risk number must include

Quote calculator output. A risk statement without a source command is incomplete.

- Value at Risk and Expected Shortfall, with the confidence level and the window.
- Maximum drawdown over that window.
- A stress view: at least one historical shock (2008, 2020) or a stated volatility spike. Say which one.
- Liquidity: average daily volume against the position size when the question is about exiting.

Volatility-based sizing, correlation spikes, and regime changes tighten these limits. They do not loosen them.
