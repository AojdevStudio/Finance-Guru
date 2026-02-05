---
title: "Contributing to Finance Guru"
description: "Development guidelines, code standards, and contribution workflow for Finance Guru"
category: root
---

# Contributing to Finance Guru

This is a private family office system. These guidelines are for the primary developer and any collaborators.

## Development Philosophy

1. **Start simple, iterate**: Build the simplest working solution first
2. **CLI-first**: Heavy computation in CLI tools, not context
3. **Token efficiency**: Minimize context consumption
4. **Type safety**: Pydantic models for all data structures

## Getting Started

### Prerequisites

```bash
# Python 3.12+ with uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Verify setup
uv run python --version
uv run python src/analysis/risk_metrics_cli.py SPY --days 30
```

### Project Structure

```
family-office/
├── src/                 # Python analysis tools
│   ├── analysis/        # Risk, correlation, ITC
│   ├── strategies/      # Optimizer, backtester
│   ├── utils/           # Momentum, volatility
│   └── models/          # Pydantic type definitions
├── fin-guru/            # Agent system
│   ├── agents/          # Specialist definitions
│   ├── tasks/           # Workflow configs
│   └── data/            # Knowledge base
├── .claude/             # Claude Code configuration
│   ├── hooks/           # Hook scripts
│   └── skills/          # Skill definitions
├── docs/                # Documentation
└── tests/               # Test suite
```

## Code Standards

### Python CLI Tools

Follow the 3-layer architecture:

```python
# Layer 1: Pydantic Models (src/models/)
class RiskMetrics(BaseModel):
    var_95: float
    cvar_95: float
    sharpe_ratio: float
    # ...

# Layer 2: Calculator Classes (src/analysis/)
class RiskCalculator:
    def __init__(self, prices: pd.DataFrame):
        self.prices = prices

    def calculate_var(self, confidence: float = 0.95) -> float:
        # Business logic here
        pass

# Layer 3: CLI Interface (src/analysis/risk_metrics_cli.py)
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ticker')
    parser.add_argument('--days', type=int, default=90)
    # ...
```

### Type Hints

Always use type hints:

```python
def calculate_sharpe(
    returns: pd.Series,
    risk_free_rate: float = 0.0
) -> float:
    """Calculate Sharpe ratio."""
    excess_returns = returns - risk_free_rate
    return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
```

### Documentation

Add docstrings to public functions:

```python
def calculate_var(
    returns: pd.Series,
    confidence: float = 0.95
) -> float:
    """
    Calculate Value at Risk.

    Args:
        returns: Daily returns series
        confidence: Confidence level (default 95%)

    Returns:
        VaR as a negative percentage (e.g., -0.034 for -3.4%)
    """
    pass
```

## Adding New CLI Tools

### 1. Create the Calculator

```python
# src/analysis/my_tool.py
from pydantic import BaseModel
import pandas as pd

class MyToolOutput(BaseModel):
    metric_1: float
    metric_2: float

class MyToolCalculator:
    def __init__(self, prices: pd.DataFrame):
        self.prices = prices

    def calculate(self) -> MyToolOutput:
        # Implementation
        return MyToolOutput(metric_1=..., metric_2=...)
```

### 2. Create the CLI

```python
# src/analysis/my_tool_cli.py
import argparse
from src.utils.market_data import fetch_prices
from src.analysis.my_tool import MyToolCalculator

def main():
    parser = argparse.ArgumentParser(description='My Tool')
    parser.add_argument('ticker', help='Stock ticker')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--output', choices=['text', 'json'], default='text')

    args = parser.parse_args()

    # Fetch data
    prices = fetch_prices(args.ticker, days=args.days)

    # Calculate
    calc = MyToolCalculator(prices)
    result = calc.calculate()

    # Output
    if args.output == 'json':
        print(result.model_dump_json(indent=2))
    else:
        print(f"Metric 1: {result.metric_1:.2f}")
        print(f"Metric 2: {result.metric_2:.2f}")

if __name__ == '__main__':
    main()
```

### 3. Update CLAUDE.md

Add the new tool to the tool reference table in `CLAUDE.md`.

### 4. Add Tests

```python
# tests/test_my_tool.py
import pytest
from src.analysis.my_tool import MyToolCalculator

def test_calculation():
    # Test with known data
    pass
```

## Adding New Hooks

### 1. Create the Hook Script

```bash
#!/bin/bash
# .claude/hooks/my-hook.sh

input=$(cat)
# Process input
echo "Hook output"
exit 0
```

### 2. Make Executable

```bash
chmod +x .claude/hooks/my-hook.sh
```

### 3. Add to settings.json

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/my-hook.sh"
          }
        ]
      }
    ]
  }
}
```

### 4. Test

```bash
echo '{"session_id": "test"}' | ./.claude/hooks/my-hook.sh
```

## Adding New Skills

### 1. Create Skill Directory

```
.claude/skills/my-skill/
├── SKILL.md          # Main skill file
└── resources/        # Optional resource files
    └── examples.md
```

### 2. Write SKILL.md

```markdown
---
name: my-skill
description: What this skill does. USE WHEN user asks about X OR mentions Y.
---

# My Skill

## Purpose
[Why this skill exists]

## When to Use
[Activation scenarios]

## Quick Reference
[Key patterns and examples]
```

### 3. Add to skill-rules.json

```json
{
  "my-skill": {
    "type": "domain",
    "enforcement": "suggest",
    "priority": "medium",
    "promptTriggers": {
      "keywords": ["keyword1", "keyword2"]
    }
  }
}
```

## Git Workflow

### Commit Messages

Use conventional commits:

```
feat: add new volatility regime detection
fix: correct Sharpe ratio calculation
docs: update API documentation
refactor: simplify correlation calculator
test: add backtester edge cases
```

### Before Committing

1. Run tests: `uv run pytest`
2. Check types: `uv run mypy src/`
3. Format code: `uv run black src/`

## Testing

### Run All Tests

```bash
uv run pytest
```

### Run Specific Test

```bash
uv run pytest tests/test_risk_metrics.py -v
```

### Test Coverage

```bash
uv run pytest --cov=src --cov-report=html
```

## Documentation Updates

When adding features, update:

1. **CLAUDE.md** - Tool reference, agent-tool matrix
2. **docs/reference/api.md** - CLI usage examples
3. **README.md** - If it affects quick start or architecture

## Questions?

This is a private system. If you're working on this codebase and have questions, check:

1. `CLAUDE.md` - Development context
2. `docs/` - Technical documentation
3. `fin-guru/data/` - System knowledge base
