---
name: fin-guru-strategize
description: "Turn research and quantitative results into a portfolio strategy with allocation changes, entry timing, position sizing, margin and dividend tactics, and an implementation plan with triggers. Use when the owner asks what to buy, sell, trim, or rotate, how much to put into a position, or how to deploy monthly income across portfolio layers. Not for raw risk numbers (use fin-guru-quant-analysis) or a margin dashboard update (use margin-management)."
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

- Load `{project-root}/fin-guru/checklists/margin-strategy.md` for margin tactics
- Load `{project-root}/fin-guru/checklists/dividend-framework.md` for income strategies
- Load `{project-root}/fin-guru/checklists/cashflow-policy.md` for cash flow optimization
- Load `{project-root}/fin-guru/data/modern-income-vehicles.md` for Layer 2 evaluation criteria

## Risk Validation Tools

```bash
# Pre-trade risk validation
uv run python -m src.analysis.risk_metrics_cli TICKER --days 252 --benchmark SPY --output json

# Entry timing analysis
uv run python -m src.utils.momentum_cli TICKER --days 90 --output json

# Volatility-based position sizing
uv run python -m src.utils.volatility_cli TICKER --days 90 --output json

# Portfolio optimization
uv run python -m src.strategies.optimizer_cli TICKERS --method max_sharpe --output json
```

## Output

Return the [`fin-guru-output-contract`](../fin-guru-output-contract/SKILL.md) skill. The Numbers table carries Sharpe, Sortino, and max drawdown for every position the strategy adds or changes. A recommendation without those three numbers is incomplete. Add an implementation plan after the Numbers table, with the amount, the entry trigger, and the exit trigger for each change.

## Requirements

- ALL strategic recommendations MUST include risk-adjusted metrics (Sharpe, Sortino, Max Drawdown)
- Distribution variance of ±5-15% monthly is NORMAL for options-based funds — do not flag
- Evaluate Layer 2 holdings on trailing 12-month yield, not monthly distribution changes
- Only recommend selling on RED FLAGS (>30% sustained decline, NAV erosion, strategy changes)
- Verify all market assumptions are based on current date conditions
