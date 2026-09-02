---
name: fin-guru-strategize
description: Develop comprehensive portfolio strategies from quantitative analysis. Integrates margin, dividend, and cash-flow tactics into actionable wealth-building plans.
---

# Strategy Integration Skill

Convert quantitative analysis into actionable strategic recommendations.

## Capability probe

Before adding current external assumptions, follow the shared **[paid MCP capability probe](../_shared/PaidMcpCapabilityProbe.md)**. This workflow wants `exa` for broad current-market discovery and `financial-datasets` for normalized company fundamentals. Announce any primary-source `WebSearch` fallback and its quality limits; stop if the requested strategy depends on data the fallback cannot verify.

## Workflow Steps

1. **Review Analysis** — Ingest quantitative outputs (risk metrics, momentum, correlations)
2. **Objective Alignment** — Confirm client goals, risk tolerance, and policy constraints
3. **Strategy Development** — Map analytical insights to actionable recommendations
4. **Risk Validation** — Validate proposed positions using `risk_metrics_cli.py` and `momentum_cli.py`
5. **Implementation Plan** — Create detailed execution roadmap with timing and triggers
6. **Monitoring Framework** — Establish performance tracking and alert systems

## Integration Points

- Load `margin-strategy.md` for margin tactics
- Load `dividend-framework.md` for income strategies
- Load `cashflow-policy.md` for cash flow optimization
- Load `modern-income-vehicles.md` for Layer 2 evaluation criteria

## Risk Validation Tools

```bash
# Pre-trade risk validation
uv run python -m src.analysis.risk_metrics_cli TICKER --days 252 --benchmark SPY

# Entry timing analysis
uv run python -m src.utils.momentum_cli TICKER --days 90

# Volatility-based position sizing
uv run python -m src.utils.volatility_cli TICKER --days 90

# Portfolio optimization
uv run python -m src.strategies.optimizer_cli TICKERS --method max_sharpe
```

## Requirements

- ALL strategic recommendations MUST include risk-adjusted metrics (Sharpe, Sortino, Max Drawdown)
- Distribution variance of ±5-15% monthly is NORMAL for options-based funds — do not flag
- Evaluate Layer 2 holdings on trailing 12-month yield, not monthly distribution changes
- Only recommend selling on RED FLAGS (>30% sustained decline, NAV erosion, strategy changes)
- Verify all market assumptions are based on current date conditions
