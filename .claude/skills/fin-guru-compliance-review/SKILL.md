---
name: fin-guru-compliance-review
description: Execute comprehensive compliance reviews for Finance Guru deliverables. Validates disclaimers, data handling, risk disclosures, and regulatory positioning.
---

# Compliance Review Skill

Structured compliance review workflow for Finance Guru outputs.

## Review Scope

1. **Disclaimer Verification** — Educational-only positioning present and correct
2. **Source Citation** — All data sources cited with timestamps and sensitivity notes
3. **Risk Disclosure** — Appropriate risk warnings and disclosures included
4. **Data Handling** — Proper data validation and audit trail requirements met
5. **Regulatory Currency** — All cited regulations current as of review date
6. **ITC Risk Integration** — Market-implied risk scores included for supported tickers

## ITC Risk Validation Workflow

For portfolio positions with ITC coverage:

```bash
# Single ticker check
uv run python src/analysis/itc_risk_cli.py TICKER --universe tradfi

# Batch processing
uv run python src/analysis/itc_risk_cli.py TSLA AAPL MSTR --universe tradfi

# Full risk band analysis
uv run python src/analysis/itc_risk_cli.py TICKER --universe tradfi --full-table
```

## Risk Thresholds

| ITC Score | Band | Action |
|-----------|------|--------|
| 0.0-0.3 | LOW | APPROVE — Standard monitoring |
| 0.3-0.7 | MEDIUM | APPROVE WITH NOTE — Document in review |
| 0.7-1.0 | HIGH | ENHANCED REVIEW — Position limit review required |

## Decision Rules

- DR-1: Low Risk Approval (ITC <0.3 AND VaR within limits)
- DR-2: Medium Risk Note (ITC 0.3-0.7)
- DR-3: High Risk Review (ITC 0.7-0.85)
- DR-4: Critical Risk Block (ITC >0.85 OR divergence >30%)
- DR-5: Unsupported Ticker (internal metrics only)

## Requirements

- Timestamp all compliance reviews with current date
- Document every final decision (pass, conditional, revisions required)
- Layer 2 variance of ±5-15% monthly is NORMAL — do not flag as compliance issue
- Only block RED FLAG scenarios (>30% sustained declines, NAV erosion, strategy changes)
