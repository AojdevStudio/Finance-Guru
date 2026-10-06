<!-- Finance Guru(tm) Risk Framework | v1.0 | 2026-10-06 -->

# Risk Framework

## Disclaimer

This document is for _educational purposes only_ and does not constitute investment advice. Portfolio limits below are the published methodology the specialists apply. They are not a guarantee against loss. Consult a licensed financial advisor before acting. Past performance does not guarantee future results.

Personal dollar thresholds, concentration exceptions, and account-specific buffers live in the instance directory, not in this file.

---

## Portfolio-level limits

Apply these to a balanced portfolio unless the instance records a tighter cap.

| Limit | Rule |
| --- | --- |
| Maximum 1-day VaR | 2% of portfolio value at 95% confidence |
| Maximum drawdown | 15% peak to trough |
| Single position | 10% of the total portfolio |
| Leverage | 2:1 maximum for a conservative strategy |

A deployment cap of 30% on one position, and any approved exception to it, is an instance rule. This framework's general cap stays at 10%.

## Asset-class ranges

| Sleeve | Range |
| --- | --- |
| Equity | 60–80% for a balanced strategy |
| Fixed income | 20–40% |
| Alternatives | 20% maximum |
| Cash and equivalents | 5% minimum, for liquidity |
| Sector concentration | 25% maximum |

## Escalation

Measure utilization against the limit above, not against a private dollar target.

| Level | Utilization | Action |
| --- | --- | --- |
| 1 — Alert | 75% of the limit | Name the limit and the metric. Increase monitoring. |
| 2 — Warning | 90% of the limit | Stop adding exposure that consumes the same limit. |
| 3 — Breach | 100% of the limit | Immediate corrective action. Do not wait for the next review. |

An emergency is a systematic loss that threatens the portfolio's ability to meet its liquidity floor. Preserve cash, reduce the position that breached, and record the hedge decision separately under `hedging-strategies.md`.

## What a risk number must include

Quote calculator output. A risk statement without a source command is incomplete.

- Value at Risk and Expected Shortfall, with the confidence level and the window.
- Maximum drawdown over that window.
- A stress view: at least one historical shock (2008, 2020) or a stated volatility spike. Say which one.
- Liquidity: average daily volume against the position size when the question is about exiting.

Volatility-based sizing, correlation spikes, and regime changes tighten these limits. They do not loosen them.
