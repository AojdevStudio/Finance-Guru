# src/ — Python Codebase Guide

## Architecture

3-layer pattern for all financial analysis tools:

```
Layer 1: Pydantic Models (src/models/)     → Data validation
Layer 2: Calculator Classes (src/analysis/, src/strategies/, src/utils/) → Business logic
Layer 3: CLI Interfaces (*_cli.py files)   → Agent/user integration
```

**Reference implementation**: `src/analysis/risk_metrics.py` + `src/models/risk_inputs.py` + `src/analysis/risk_metrics_cli.py`

## Directory Structure

```
src/
├── models/              # Pydantic input/output models (one per tool)
├── analysis/            # Risk metrics, correlation, ITC risk (calculators + CLIs)
├── strategies/          # Backtester, portfolio optimizer (calculators + CLIs)
├── utils/               # Market data, momentum, volatility, moving averages
├── ui/                  # Streamlit dashboard (app.py, services/, widgets/)
├── cli/                 # Additional CLI utilities
├── data/                # Data processing modules
├── reports/             # Report generation
└── config.py            # Project-wide configuration
```

## Adding New Tools

1. Create Pydantic models in `src/models/{tool}_inputs.py`
2. Create calculator class in appropriate directory (analysis/strategies/utils)
3. Create CLI in same directory as `{tool}_cli.py`
4. Export models from `src/models/__init__.py`
5. Write tests in `tests/python/test_{tool}.py`
6. Update root `CLAUDE.md` tool reference table

## Key Conventions

- **Pydantic models**: Set `arbitrary_types_allowed = True` for pandas/numpy types
- **Calculator classes**: Accept Pydantic models in constructor, return them from `calculate_all()`
- **CLI scripts**: Use `argparse`, support `--output json` and `--output text`, exit code 1 on error
- **Imports**: stdlib → third-party → local
- **Naming**: `PascalCase` classes, `snake_case` functions, `UPPER_SNAKE_CASE` constants, `_leading_underscore` private
- **Type hints**: Required on all function signatures
- **Docstrings**: Google-style

## Gotchas

1. **Pandas + Pydantic**: Always add `class Config: arbitrary_types_allowed = True`
2. **Returns vs Prices**: Be explicit — name params `prices` or `returns`, never `data`
3. **Annualization**: Use `TRADING_DAYS_PER_YEAR = 252` constant
4. **Division by zero**: Guard `std_dev > 0` before computing ratios
5. **No business logic in CLI**: CLI handles I/O only; calculations live in Layer 2

## Testing

```bash
uv run pytest                                    # All tests
uv run pytest tests/python/test_risk_metrics.py  # Specific file
uv run pytest -m "not integration"               # Skip API tests
uv run pytest --cov=src --cov-report=html        # With coverage
```

Mark API/network tests with `@pytest.mark.integration`.
