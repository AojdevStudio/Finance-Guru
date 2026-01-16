# src/ Developer Guide

This guide provides context for AI agents and developers working on the Finance Guru™ Python codebase in the `src/` directory.

## Architecture Overview

Finance Guru™ uses a strict 3-layer architecture for all financial analysis tools:

```
Layer 1: Pydantic Models (src/models/)
    ↓
Layer 2: Calculator Classes (src/analysis/, src/strategies/, src/utils/)
    ↓
Layer 3: CLI Interfaces (*_cli.py files)
```

### Why This Architecture?

1. **Type Safety**: Pydantic models validate all inputs/outputs
2. **Testability**: Each layer can be tested independently
3. **Reusability**: Calculator classes can be used by CLI, UI, or agents
4. **Maintainability**: Business logic separated from I/O concerns

## Directory Structure

```
src/
├── models/              # Layer 1: Pydantic models for all data structures
│   ├── __init__.py      # Exports all models
│   ├── risk_inputs.py   # Risk calculation models
│   ├── momentum_inputs.py
│   ├── volatility_inputs.py
│   ├── correlation_inputs.py
│   ├── backtest_inputs.py
│   ├── moving_avg_inputs.py
│   ├── portfolio_inputs.py
│   └── itc_risk_inputs.py
│
├── analysis/            # Layer 2: Core analysis calculators
│   ├── risk_metrics.py  # RiskCalculator class
│   ├── risk_metrics_cli.py  # Layer 3: CLI interface
│   ├── correlation.py   # CorrelationCalculator class
│   ├── correlation_cli.py
│   ├── itc_risk.py      # ITCRiskClient class
│   └── itc_risk_cli.py
│
├── strategies/          # Layer 2: Strategy calculators
│   ├── backtester.py    # BacktestEngine class
│   ├── backtester_cli.py
│   ├── optimizer.py     # PortfolioOptimizer class
│   └── optimizer_cli.py
│
├── utils/               # Layer 2: Utility calculators
│   ├── market_data.py   # Data fetching utilities
│   ├── momentum.py      # MomentumCalculator class
│   ├── momentum_cli.py
│   ├── volatility.py    # VolatilityCalculator class
│   ├── volatility_cli.py
│   ├── moving_averages.py
│   └── moving_averages_cli.py
│
├── ui/                  # Streamlit dashboard (separate from 3-layer arch)
│   ├── app.py
│   ├── services/
│   └── widgets/
│
└── config.py            # Project-wide configuration
```

## Layer 1: Pydantic Models

All data structures use Pydantic for validation and type safety.

### Model Patterns

```python
# src/models/risk_inputs.py
from pydantic import BaseModel, Field, validator
import pandas as pd

class PriceDataInput(BaseModel):
    """Input data for risk calculations."""
    ticker: str
    prices: pd.Series
    benchmark_prices: pd.Series | None = None

    class Config:
        arbitrary_types_allowed = True  # For pandas types

class RiskMetricsOutput(BaseModel):
    """Output from risk calculations."""
    var_95: float = Field(..., description="95% Value at Risk")
    cvar_95: float = Field(..., description="95% Conditional VaR")
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    annual_volatility: float
    beta: float | None = None
    alpha: float | None = None

    @validator('var_95', 'cvar_95')
    def validate_negative(cls, v):
        """VaR/CVaR should be negative."""
        if v > 0:
            raise ValueError(f"Expected negative value, got {v}")
        return v
```

### Key Principles

1. **Descriptive Field Names**: Use full names, not abbreviations
2. **Field Descriptions**: Add `description` for complex metrics
3. **Validators**: Add `@validator` for business logic constraints
4. **Optional Fields**: Use `| None` for optional fields
5. **Config**: Set `arbitrary_types_allowed = True` for pandas/numpy types

## Layer 2: Calculator Classes

Business logic lives in calculator classes that operate on Pydantic models.

### Calculator Patterns

```python
# src/analysis/risk_metrics.py
from src.models.risk_inputs import (
    PriceDataInput,
    RiskCalculationConfig,
    RiskMetricsOutput,
)
import pandas as pd
import numpy as np

class RiskCalculator:
    """
    Calculate comprehensive risk metrics.

    ARCHITECTURE NOTE:
    This is Layer 2 of our 3-layer architecture:
        Layer 1: Pydantic Models - Data validation (risk_inputs.py)
        Layer 2: Calculator Classes (THIS FILE) - Business logic
        Layer 3: CLI Interface - Agent integration

    Attributes:
        data: Validated input data
        config: Calculation configuration
    """

    def __init__(
        self,
        data: PriceDataInput,
        config: RiskCalculationConfig | None = None,
    ):
        """Initialize calculator with validated data."""
        self.data = data
        self.config = config or RiskCalculationConfig()
        self._returns = self._calculate_returns()

    def _calculate_returns(self) -> pd.Series:
        """Calculate daily returns from prices."""
        return self.data.prices.pct_change().dropna()

    def calculate_var(self, confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk using historical method.

        VaR represents the maximum expected loss over a given time period
        at a specified confidence level.

        Args:
            confidence: Confidence level (0.95 = 95%)

        Returns:
            VaR as a negative percentage (e.g., -0.034 for -3.4%)
        """
        return np.percentile(self._returns, (1 - confidence) * 100)

    def calculate_all(self) -> RiskMetricsOutput:
        """
        Calculate all risk metrics.

        Returns:
            Validated RiskMetricsOutput model
        """
        return RiskMetricsOutput(
            var_95=self.calculate_var(0.95),
            cvar_95=self.calculate_cvar(0.95),
            sharpe_ratio=self.calculate_sharpe(),
            sortino_ratio=self.calculate_sortino(),
            max_drawdown=self.calculate_max_drawdown(),
            calmar_ratio=self.calculate_calmar(),
            annual_volatility=self.calculate_volatility(),
            beta=self.calculate_beta() if self.data.benchmark_prices is not None else None,
            alpha=self.calculate_alpha() if self.data.benchmark_prices is not None else None,
        )
```

### Key Principles

1. **Accept Pydantic Models**: Constructor takes validated models as input
2. **Return Pydantic Models**: `calculate_all()` returns validated output model
3. **Private Helpers**: Use `_method_name` for internal calculations
4. **Docstrings**: Include WHAT, WHY, HOW for each calculation
5. **Type Hints**: Always use type hints for parameters and returns
6. **No Side Effects**: Calculator methods should be pure (no I/O, no state mutation)

## Layer 3: CLI Interfaces

CLI scripts provide command-line access to calculators.

### CLI Patterns

```python
# src/analysis/risk_metrics_cli.py
"""
Risk Metrics CLI for Finance Guru™

Usage:
    uv run python src/analysis/risk_metrics_cli.py TICKER [options]

Examples:
    uv run python src/analysis/risk_metrics_cli.py TSLA --days 90
    uv run python src/analysis/risk_metrics_cli.py SPY --output json
    uv run python src/analysis/risk_metrics_cli.py NVDA --benchmark SPY
"""
import argparse
import sys
from src.utils.market_data import fetch_prices
from src.models.risk_inputs import PriceDataInput, RiskCalculationConfig
from src.analysis.risk_metrics import RiskCalculator

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Calculate comprehensive risk metrics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('ticker', help='Stock ticker symbol')
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Number of days of data (default: 90)'
    )
    parser.add_argument(
        '--benchmark',
        default='SPY',
        help='Benchmark ticker for beta/alpha (default: SPY)'
    )
    parser.add_argument(
        '--output',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '--save-to',
        help='Save JSON output to file'
    )
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()

    try:
        # Layer 1: Fetch and validate data
        prices = fetch_prices(args.ticker, days=args.days)
        benchmark_prices = fetch_prices(args.benchmark, days=args.days)

        data = PriceDataInput(
            ticker=args.ticker,
            prices=prices,
            benchmark_prices=benchmark_prices,
        )

        # Layer 2: Calculate
        calculator = RiskCalculator(data)
        result = calculator.calculate_all()

        # Layer 3: Format output
        if args.output == 'json':
            output = result.model_dump_json(indent=2)
            print(output)

            if args.save_to:
                with open(args.save_to, 'w') as f:
                    f.write(output)
        else:
            print(f"\n{'='*60}")
            print(f"Risk Metrics for {args.ticker}")
            print(f"{'='*60}")
            print(f"Value at Risk (95%):     {result.var_95:.2%}")
            print(f"Conditional VaR (95%):   {result.cvar_95:.2%}")
            print(f"Sharpe Ratio:            {result.sharpe_ratio:.2f}")
            print(f"Sortino Ratio:           {result.sortino_ratio:.2f}")
            print(f"Maximum Drawdown:        {result.max_drawdown:.2%}")
            print(f"Calmar Ratio:            {result.calmar_ratio:.2f}")
            print(f"Annual Volatility:       {result.annual_volatility:.2%}")
            if result.beta is not None:
                print(f"Beta (vs {args.benchmark}):       {result.beta:.2f}")
            if result.alpha is not None:
                print(f"Alpha (vs {args.benchmark}):      {result.alpha:.2%}")
            print(f"{'='*60}\n")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### Key Principles

1. **Argparse**: Use `argparse` for all CLI argument parsing
2. **Help Text**: Include docstring with usage examples
3. **Error Handling**: Catch exceptions and exit with code 1
4. **Multiple Formats**: Support both text and JSON output
5. **Sensible Defaults**: Provide defaults for all optional arguments
6. **No Business Logic**: CLI should only handle I/O, not calculations

## Common Patterns

### Fetching Market Data

```python
from src.utils.market_data import fetch_prices

# Single ticker
prices = fetch_prices('TSLA', days=90)

# Multiple tickers
tickers = ['TSLA', 'PLTR', 'NVDA']
portfolio_prices = {
    ticker: fetch_prices(ticker, days=90)
    for ticker in tickers
}
```

### Working with Pydantic Models

```python
# Create model
from src.models.risk_inputs import PriceDataInput

data = PriceDataInput(
    ticker='TSLA',
    prices=prices,
    benchmark_prices=benchmark_prices,
)

# Access fields
print(data.ticker)  # 'TSLA'
print(data.prices.mean())

# Serialize to JSON
json_str = data.model_dump_json(indent=2)

# Serialize to dict
data_dict = data.model_dump()
```

### Testing Calculators

```python
# tests/python/test_risk_metrics.py
import pytest
import pandas as pd
import numpy as np
from src.models.risk_inputs import PriceDataInput
from src.analysis.risk_metrics import RiskCalculator

def test_var_calculation():
    """Test VaR calculation with known data."""
    # Create synthetic price data
    np.random.seed(42)
    prices = pd.Series(100 * (1 + np.random.randn(100) * 0.02).cumprod())

    data = PriceDataInput(
        ticker='TEST',
        prices=prices,
    )

    calculator = RiskCalculator(data)
    var_95 = calculator.calculate_var(0.95)

    # VaR should be negative
    assert var_95 < 0
    # VaR should be reasonable for this volatility
    assert -0.10 < var_95 < -0.01

def test_sharpe_ratio():
    """Test Sharpe ratio calculation."""
    # Create upward trending prices
    prices = pd.Series(range(100, 200))

    data = PriceDataInput(ticker='TEST', prices=prices)
    calculator = RiskCalculator(data)

    sharpe = calculator.calculate_sharpe()

    # Upward trend should have positive Sharpe
    assert sharpe > 0
```

## Adding New Tools

Follow this checklist when adding a new financial analysis tool:

### 1. Create Pydantic Models

File: `src/models/my_tool_inputs.py`

```python
from pydantic import BaseModel, Field

class MyToolDataInput(BaseModel):
    """Input data for my tool."""
    ticker: str
    prices: pd.Series

    class Config:
        arbitrary_types_allowed = True

class MyToolOutput(BaseModel):
    """Output from my tool calculations."""
    metric_1: float = Field(..., description="First metric")
    metric_2: float = Field(..., description="Second metric")
```

### 2. Create Calculator Class

File: `src/analysis/my_tool.py` (or `src/strategies/` or `src/utils/`)

```python
from src.models.my_tool_inputs import MyToolDataInput, MyToolOutput

class MyToolCalculator:
    """
    Calculate metrics for my tool.

    ARCHITECTURE NOTE:
    This is Layer 2 of our 3-layer architecture.
    """

    def __init__(self, data: MyToolDataInput):
        self.data = data

    def calculate_metric_1(self) -> float:
        """Calculate first metric."""
        # Implementation
        pass

    def calculate_all(self) -> MyToolOutput:
        """Calculate all metrics."""
        return MyToolOutput(
            metric_1=self.calculate_metric_1(),
            metric_2=self.calculate_metric_2(),
        )
```

### 3. Create CLI Interface

File: `src/analysis/my_tool_cli.py`

```python
"""
My Tool CLI for Finance Guru™

Usage:
    uv run python src/analysis/my_tool_cli.py TICKER [options]
"""
import argparse
from src.utils.market_data import fetch_prices
from src.models.my_tool_inputs import MyToolDataInput
from src.analysis.my_tool import MyToolCalculator

def main():
    parser = argparse.ArgumentParser(description='My tool')
    parser.add_argument('ticker', help='Stock ticker')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--output', choices=['text', 'json'], default='text')
    args = parser.parse_args()

    # Fetch data
    prices = fetch_prices(args.ticker, days=args.days)
    data = MyToolDataInput(ticker=args.ticker, prices=prices)

    # Calculate
    calculator = MyToolCalculator(data)
    result = calculator.calculate_all()

    # Output
    if args.output == 'json':
        print(result.model_dump_json(indent=2))
    else:
        print(f"Metric 1: {result.metric_1:.2f}")
        print(f"Metric 2: {result.metric_2:.2f}")

if __name__ == '__main__':
    main()
```

### 4. Export Models

Add to `src/models/__init__.py`:

```python
from src.models.my_tool_inputs import (
    MyToolDataInput,
    MyToolOutput,
)

__all__ = [
    # ... existing exports ...
    "MyToolDataInput",
    "MyToolOutput",
]
```

### 5. Write Tests

File: `tests/python/test_my_tool.py`

```python
import pytest
from src.models.my_tool_inputs import MyToolDataInput
from src.analysis.my_tool import MyToolCalculator

def test_calculation():
    """Test basic calculation."""
    # Implementation
    pass
```

### 6. Update Documentation

1. Add to root `CLAUDE.md` tool reference table
2. Add to `docs/api.md` CLI usage examples
3. Update `docs/tools.md` if needed

## Code Style Guidelines

### Type Hints

Always use type hints:

```python
# Good
def calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    pass

# Bad
def calculate_sharpe(returns, risk_free_rate=0.0):
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Calculate Value at Risk using historical method.

    VaR represents the maximum expected loss over a given time period
    at a specified confidence level.

    Args:
        returns: Daily returns series
        confidence: Confidence level (0.95 = 95%)

    Returns:
        VaR as a negative percentage (e.g., -0.034 for -3.4%)

    Raises:
        ValueError: If confidence is not between 0 and 1
    """
    if not 0 < confidence < 1:
        raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")

    return np.percentile(returns, (1 - confidence) * 100)
```

### Imports

Group imports in this order:

```python
# Standard library
import argparse
import sys
from typing import Tuple

# Third-party
import numpy as np
import pandas as pd
from scipy import stats

# Local
from src.models.risk_inputs import PriceDataInput
from src.utils.market_data import fetch_prices
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `RiskCalculator`)
- **Functions**: `snake_case` (e.g., `calculate_var`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `TRADING_DAYS_PER_YEAR`)
- **Private methods**: `_leading_underscore` (e.g., `_calculate_returns`)

## Testing

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/python/test_risk_metrics.py

# Specific test function
uv run pytest tests/python/test_risk_metrics.py::test_var_calculation

# With coverage
uv run pytest --cov=src --cov-report=html
```

### Test Organization

```
tests/python/
├── test_risk_metrics.py      # Unit tests for risk_metrics.py
├── test_momentum.py           # Unit tests for momentum.py
├── test_volatility.py
└── test_backtester.py
```

### Integration Tests

Mark tests that require API keys or network access:

```python
import pytest

@pytest.mark.integration
def test_fetch_real_data():
    """Test fetching real market data from yfinance."""
    prices = fetch_prices('SPY', days=30)
    assert len(prices) > 0
```

Run only unit tests (skip integration):

```bash
uv run pytest -m "not integration"
```

## Common Gotchas

### 1. Pandas Arbitrary Types

Always set `arbitrary_types_allowed = True` in Pydantic models that use pandas:

```python
class MyModel(BaseModel):
    prices: pd.Series

    class Config:
        arbitrary_types_allowed = True
```

### 2. Returns vs Prices

Be explicit about whether data is prices or returns:

```python
# Good
def calculate_from_prices(prices: pd.Series) -> float:
    returns = prices.pct_change().dropna()
    # ...

# Bad (ambiguous)
def calculate(data: pd.Series) -> float:
    # Is this prices or returns?
    pass
```

### 3. Annualization

Use constants for annualization:

```python
TRADING_DAYS_PER_YEAR = 252

annual_volatility = daily_volatility * np.sqrt(TRADING_DAYS_PER_YEAR)
```

### 4. Division by Zero

Handle edge cases:

```python
# Good
if std_dev > 0:
    sharpe = mean / std_dev
else:
    sharpe = 0.0

# Bad
sharpe = mean / std_dev  # Can crash
```

## Performance Considerations

### Use Vectorized Operations

```python
# Good (vectorized)
returns = prices.pct_change()

# Bad (loop)
returns = []
for i in range(1, len(prices)):
    returns.append((prices[i] - prices[i-1]) / prices[i-1])
```

### Avoid Redundant Calculations

```python
# Good (calculate once)
def __init__(self, data: PriceDataInput):
    self.data = data
    self._returns = self._calculate_returns()  # Cache

def calculate_sharpe(self) -> float:
    return self._returns.mean() / self._returns.std()

def calculate_sortino(self) -> float:
    downside = self._returns[self._returns < 0]
    return self._returns.mean() / downside.std()
```

## Questions?

- Check `docs/contributing.md` for general contribution guidelines
- Check root `CLAUDE.md` for Finance Guru™ system overview
- Check `docs/api.md` for CLI usage examples
- Check existing tools in `src/analysis/`, `src/strategies/`, `src/utils/` for patterns
