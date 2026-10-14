---
name: fin-guru-compliance-review
description: "Compliance review of a Finance Guru deliverable or a proposed position. Checks disclaimers, source citations, and risk disclosures, and runs the ITC market-implied risk check with decision rules DR-1 to DR-5. Use when an analysis or buy ticket is about to be final, or when the owner asks whether a position passes risk review. Not for scanning the repository for secrets or PII before a push (use compliance-scan)."
---

# Compliance Review Skill

Structured compliance review workflow for Finance Guru outputs.

## Capability probe

Before validating an externally sourced filing or issuer claim, follow the shared **[paid MCP capability probe](../_shared/PaidMcpCapabilityProbe.md)**. This workflow wants `financial-datasets` for normalized filing data. If it is absent, announce a primary-source regulator/issuer `WebSearch` fallback and the manual-validation caveat, or stop when the claim cannot be verified reliably.

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
uv run python -m src.analysis.itc_risk_cli TICKER --universe tradfi --output json

# Batch processing
uv run python -m src.analysis.itc_risk_cli TSLA AAPL MSTR --universe tradfi --output json

# Full risk band analysis
uv run python -m src.analysis.itc_risk_cli TICKER --universe tradfi --full-table --output json
```

## Risk Thresholds

| ITC Score | Band | Action |
|-----------|------|--------|
| 0.0-0.3 | LOW | APPROVE — Standard monitoring |
| 0.3-0.7 | MEDIUM | APPROVE WITH NOTE — Document in review |
| 0.7-1.0 | HIGH | ENHANCED REVIEW — Position limit review required |

## Decision Rules

[ITC divergence and decision rules](itc-divergence.md) holds the full rules, the worked example, the divergence scenarios, and the escalation matrix.

- DR-1: Low Risk Approval (ITC <0.3 AND VaR within limits)
- DR-2: Medium Risk Note (ITC 0.3-0.7)
- DR-3: High Risk Review (ITC 0.7-0.85)
- DR-4: Critical Risk Block (ITC >0.85 OR divergence >30%)
- DR-5: Unsupported Ticker (internal metrics only)

## Output

Return the [`fin-guru-output-contract`](../fin-guru-output-contract/SKILL.md) skill. The Bottom line is the verdict, one of PASS, CONDITIONAL PASS, or REVISIONS REQUIRED, with the decision rule that produced it. The Numbers table carries the ITC score and band for each supported ticker.

## Requirements

- Timestamp all compliance reviews with current date
- Document every final decision (pass, conditional, revisions required)
- Layer 2 variance of ±5-15% monthly is NORMAL — do not flag as compliance issue
- Only block RED FLAG scenarios (>30% sustained declines, NAV erosion, strategy changes)
