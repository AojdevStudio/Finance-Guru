# ITC risk validation and divergence guidance

Reference for the `fin-guru-compliance-review` skill and the compliance officer agent. It holds the ITC risk validation workflow, the decision rules DR-1 to DR-5, a worked example, and the guidance for when ITC market-implied risk and internal metrics disagree.

## Supported tickers

Read the lists from the CLI.

- TradFi: `uv run python -m src.analysis.itc_risk_cli --list-supported tradfi`
- Crypto: `uv run python -m src.analysis.itc_risk_cli --list-supported crypto`

For an unsupported ticker, record "ITC: N/A - internal metrics only".

## When to use ITC in a compliance review

- Position limit reviews: validate risk levels before approving a concentration increase.
- Strategy approval: assess market-implied risk for a new trading strategy.
- Margin compliance: monitor risk scores for leveraged positions.
- Red flag detection: identify positions with elevated market-implied risk (above 0.7).
- Audit documentation: include ITC risk levels in compliance review records.

## Risk thresholds

| ITC score | Band | Action |
| --- | --- | --- |
| 0.0-0.3 | LOW | APPROVE. Standard monitoring. |
| 0.3-0.7 | MEDIUM | APPROVE WITH NOTE. Document in review. |
| 0.7-1.0 | HIGH | ENHANCED REVIEW. Requires position limit review and risk disclosure. |

Include ITC risk scores in every compliance review for positions in supported tickers.

## ITC risk validation workflow

### Triggers

Run the workflow when:

- A new position is added to the portfolio (pre-approval check).
- A position size increase is requested (concentration review).
- The weekly compliance scan runs (all ITC-supported tickers).
- A market volatility spike is detected (a move above 2 standard deviations).
- The Strategy Advisor requests risk clearance.
- The owner asks for ITC validation.

### Steps

1. Find which positions have ITC coverage with `uv run python -m src.analysis.itc_risk_cli --list-supported tradfi`. Cross-reference the list with current holdings in `family_office.db`.
2. For each supported position, run `uv run python -m src.analysis.itc_risk_cli TICKER --universe tradfi --output json`. Use `--universe crypto` for crypto positions. Record each result with the `{current_date}` timestamp.
3. Run the internal risk analysis: `uv run python -m src.analysis.risk_metrics_cli TICKER --days 90 --benchmark SPY --output json`. Compare VaR and volatility with the ITC market-implied level.
4. Evaluate each position against the decision rules below and set an action for each.
5. Create a compliance record with the position ticker and current value, the ITC risk score and band, internal VaR and CVaR, the recommended action (APPROVE, MONITOR, REVIEW, or BLOCK), reviewer notes, and the timestamp.
6. Notify by band. HIGH (above 0.7): notify the Strategy Advisor and the owner immediately. MEDIUM: include in the weekly compliance summary. LOW: standard documentation only.

## Decision rules

### DR-1: Low risk approval

- Condition: ITC risk score 0.0-0.3 and internal VaR within limits.
- Action: APPROVE. Standard monitoring applies.
- Documentation: log the approval with the risk score in the compliance record.

### DR-2: Medium risk note

- Condition: ITC risk score 0.3-0.7, or elevated but manageable volatility.
- Action: APPROVE WITH NOTE. Enhanced monitoring recommended.
- Documentation: document the elevated risk and set a 30-day review reminder.

### DR-3: High risk review

- Condition: ITC risk score 0.7-0.85.
- Action: ENHANCED REVIEW. Position limit review required.
- Documentation: full risk disclosure, notify the owner, consider position reduction.

### DR-4: Critical risk block

- Condition: ITC risk score above 0.85, or divergence above 30% between ITC and internal metrics.
- Action: BLOCK. Immediate attention required.
- Documentation: escalate to the owner and recommend a position reduction or hedge.

### DR-5: Unsupported ticker

- Condition: the ticker is not in the ITC supported list.
- Action: INTERNAL ONLY. Use internal metrics exclusively.
- Documentation: note "ITC: N/A" and rely on `risk_metrics_cli` output.

## Example: TSLA position review

Context: the owner requests a $5,000 increase to the TSLA position.

1. Coverage: TSLA is ITC-supported (tradfi universe). Current holding: 13.42% of the portfolio.
2. ITC: `uv run python -m src.analysis.itc_risk_cli TSLA --universe tradfi` returns an ITC risk score of 0.52 (MEDIUM band).
3. Internal: `uv run python -m src.analysis.risk_metrics_cli TSLA --days 90 --benchmark SPY` returns daily VaR (95%) of -3.8%, volatility of 48%, and beta of 1.9.
4. Evaluation:

   ```text
   ITC Score: 0.52 → MEDIUM band
   Internal VaR: Within policy limits (max 5%)
   Concentration after increase: 15.5% (below 20% single-position limit)
   Decision Rule Applied: DR-2 (Medium Risk Note)
   ```

5. Compliance record:

   ```text
   Date: {current_date}
   Position: TSLA
   Request: Increase position by $5,000
   ITC Risk Score: 0.52 (MEDIUM)
   Internal VaR (95%): -3.8%
   Post-increase concentration: 15.5%
   Decision: APPROVE WITH NOTE
   Action: Approve position increase with 30-day review reminder
   Reviewer: Marcus Allen (Compliance Officer)
   ```

6. Notification:

```text
Risk level MEDIUM - No immediate notification required.
Added to weekly compliance summary.
Set calendar reminder for 30-day re-assessment.
```

## Divergence between ITC and internal metrics

When ITC risk scores and internal VaR or volatility metrics disagree significantly, the disagreement signals possible model risk or a market dislocation. Divergence occurs when ITC market-implied risk and internal calculated risk give conflicting signals about a position's risk level.

### Calculation

```text
Divergence % = |ITC Risk Score - Normalized Internal Risk Score| × 100

Where Normalized Internal Risk Score is:
- VaR-based: Daily VaR / 5% max threshold
- Volatility-based: Annualized Vol / 80% baseline
- Combined: Average of VaR and Volatility normalizations
```

### Thresholds

| Divergence | Severity | Meaning |
| --- | --- | --- |
| 0-15% | LOW | Normal variance. Metrics generally aligned. |
| 15-30% | MODERATE | Notable divergence. Requires documentation. |
| 30-50% | HIGH | Significant divergence. Enhanced review required. |
| Above 50% | CRITICAL | Extreme divergence. Potential model failure or market dislocation. |

### Scenario DIV-1: ITC high, internal low

ITC shows elevated market-implied risk (above 0.7), but internal VaR and volatility indicate lower risk.

Possible causes:

- The market anticipates future volatility not yet in historical data.
- The options market prices in event risk (earnings, regulatory).
- A sector-wide sentiment shift is not captured by ticker-specific metrics.
- The ITC model captures cross-asset correlations the internal tools miss.

Compliance action, severity HIGH:

1. Document the divergence with specific values in the compliance record.
2. Trust ITC in this scenario. Forward-looking market data is more current.
3. Apply enhanced monitoring per DR-3 (High Risk Review).
4. Recommend a position size reduction until the divergence resolves.
5. Set a 7-day re-assessment reminder.

### Scenario DIV-2: ITC low, internal high

ITC shows low market-implied risk (below 0.3), but internal metrics show elevated VaR or volatility.

Possible causes:

- A recent idiosyncratic price movement is not yet reflected in the ITC model.
- A thin options market gives a less accurate implied risk.
- Internal metrics capture leverage or concentration risk that ITC does not model.
- The ITC model update is delayed after a major price move.

Compliance action, severity MEDIUM:

1. Document the divergence in the compliance record.
2. Trust the internal metrics in this scenario. Idiosyncratic risk is real.
3. Maintain position limits based on internal VaR calculations.
4. Flag for Strategy Advisor review of position sizing.
5. Set a 14-day re-assessment reminder.

### Scenario DIV-3: both high, different magnitude

Both ITC and internal metrics show elevated risk, but the magnitudes differ significantly (for example ITC 0.85, internal equivalent 0.55).

Possible causes:

- Each model captures different risk factors.
- Time horizons differ (ITC forward-looking, internal historical).
- Model calibration differs under stress conditions.

Compliance action, severity HIGH:

1. Use the higher of the two risk assessments for compliance decisions.
2. Document both metrics and apply the most conservative interpretation.
3. Apply DR-3 or DR-4 based on the higher reading.
4. Recommend that the owner consider a hedge.
5. Set a mandatory 7-day re-assessment.

### Scenario DIV-4: rapid divergence shift

The divergence between ITC and internal metrics has changed by more than 20 percentage points within 7 days.

Possible causes:

- A market regime change is in progress.
- A major news event affects forward expectations.
- One side's model was recalibrated.
- A liquidity event affects option-implied measures.

Compliance action, severity CRITICAL:

1. Immediate review. Escalate to the owner within 24 hours.
2. Document both the current and the previous divergence values.
3. Temporarily apply the most conservative position limits.
4. Request a Quant Analyst root cause analysis.
5. No new position increases until the divergence stabilizes.

### Documentation format

```text
## Divergence Analysis - {TICKER}
**Date**: {current_date}
**ITC Risk Score**: X.XX (BAND)
**Internal VaR (95%)**: -X.X%
**Internal Volatility**: XX%
**Normalized Internal Risk**: X.XX
**Divergence**: XX% (SEVERITY)
**Scenario Applied**: DIV-X
**Action Taken**: [Specific action per guidance]
**Next Review**: {date}
**Reviewer**: Marcus Allen (Compliance Officer)
```

### Escalation matrix

| Divergence | Escalation |
| --- | --- |
| Below 15% | Log only. No escalation required. |
| 15-30% | Include in the weekly compliance summary. |
| 30-50% | Notify the owner within 48 hours and flag for the Strategy Advisor. |
| Above 50% | Notify the owner immediately and recommend a position action. |

### Key principles

1. When in doubt, apply the more conservative risk assessment.
2. Divergence itself is a risk signal. Treat significant divergence as elevated risk.
3. ITC is better for forward-looking, market-implied risk.
4. Internal metrics are better for position-specific, leverage, and concentration risk.
5. Rapid divergence changes always warrant enhanced scrutiny.
