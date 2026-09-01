# ReportGenerator Help

PDF report builder CLI for Finance Guru analysis reports.

## Usage

```bash
uv run python ReportGenerator.py --ticker TICKER [OPTIONS]
```

## Required Arguments

| Argument | Description |
|----------|-------------|
| `--ticker` | Stock ticker symbol to analyze |

## Optional Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--portfolio-value` | 250000 | Portfolio value for position sizing |
| `--output-dir` | reports | Output directory |

## Examples

### Basic Report
```bash
uv run python ReportGenerator.py --ticker TSLA
```

### Custom Portfolio Value
```bash
uv run python ReportGenerator.py --ticker PLTR --portfolio-value 500000
```

### Custom Output Directory
```bash
uv run python ReportGenerator.py --ticker NVDA --output-dir ./custom-reports/
```

## Report Structure (8-10 Pages)

1. **Cover Page** (VGT-style)
   - FINANCE GURU brand header
   - Analyst team listing
   - Current price + YTD performance

2. **Executive Summary**
   - Investment thesis
   - Key findings
   - Verdict box (rating, conviction, risk)

3. **Quantitative Analysis**
   - Risk metrics (Sharpe, Sortino, Beta, Alpha)
   - Momentum indicators (RSI, MACD)
   - Volatility assessment

4. **Portfolio Sizing**
   - Percentage allocation
   - Dollar amount (based on portfolio value)
   - Share count

5. **Market Sentiment**
   - Analyst ratings
   - 2026 catalysts
   - Key risks

6. **Disclaimer**
   - Compliance text
   - Generation timestamp

## Output

Reports are saved as PDF files with naming convention:
`{TICKER}-analysis-{YYYY-MM-DD}.pdf`

## Integration

ReportGenerator is designed to be called from workflow scripts or subagents.
For programmatic use:

```python
from ReportGenerator import FinanceGuruReport

report = FinanceGuruReport(ticker="TSLA", portfolio_value=250000)
report.add_cover_page(title="...", ...)
report.add_executive_summary(thesis="...", ...)
report.build()
```
