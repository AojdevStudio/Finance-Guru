# PortfolioParser Reference

How to parse Fidelity CSV files for Monte Carlo simulation starting values.

## Fidelity CSV Format

The Fidelity positions CSV (`Portfolio_Positions_*.csv`) has this structure:

```csv
Account Number,Account Name,Investment Type,Symbol,Description,Quantity,Last Price,Last Price Change,Current Value,...
```

### Important Columns

| Index | Column Name | Contains |
|-------|-------------|----------|
| 3 | Symbol | Ticker symbol (e.g., PLTR, JEPI) |
| 8 | Current Value | Dollar value of position |
| 2 | Investment Type | Stocks, ETFs, Mutual Funds |

### CSV Quirks

1. **BOM Character**: File may start with UTF-8 BOM (`\ufeff`)
2. **Duplicate Holdings**: Same ticker can appear twice (margin + cash positions)
3. **Pending Activity**: Last row shows pending transactions, not a holding
4. **Footer Rows**: Disclaimer text appears after holdings

## Layer Classification

### Layer 1: Growth (Keep 100%)

```python
LAYER1_TICKERS = {
    'PLTR', 'TSLA', 'NVDA', 'AAPL', 'VOO', 'FNILX', 'SPMO',
    'VXUS', 'FZILX', 'SOFI', 'COIN', 'MSTR', 'PARR'
}
```

### Layer 2: Income (Build with W2)

```python
LAYER2_TICKERS = {
    # JPMorgan Income
    'JEPI', 'JEPQ',
    # CEF Stable
    'CLM', 'CRF', 'ECAT',
    # Covered Call ETFs
    'QQQI', 'SPYI', 'QQQY',
    # YieldMax
    'YMAX', 'AMZY', 'MSTY',
    # DRIP v2 CEFs
    'BDJ', 'ETY', 'ETV', 'BST', 'UTG'
}
```

### Layer 3: Hedge

```python
LAYER3_TICKERS = {'SQQQ'}
```

### Special Positions

```python
GOOGL_TICKERS = {'GOOGL'}
```

## Parsing Algorithm

```python
import pandas as pd

def parse_portfolio(csv_path: str) -> dict:
    """Parse Fidelity CSV and return layer values."""

    # Read CSV, handling BOM
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # Filter to valid holdings (has Symbol and Current Value)
    df = df[df['Symbol'].notna() & df['Current Value'].notna()]

    # Remove "Pending activity" row
    df = df[df['Symbol'] != 'Pending activity']

    # Parse Current Value (remove $ and ,)
    df['Value'] = df['Current Value'].str.replace('[$,]', '', regex=True).astype(float)

    # Sum by layer
    layer1 = df[df['Symbol'].isin(LAYER1_TICKERS)]['Value'].sum()
    layer2 = df[df['Symbol'].isin(LAYER2_TICKERS)]['Value'].sum()
    layer3 = df[df['Symbol'].isin(LAYER3_TICKERS)]['Value'].sum()
    googl = df[df['Symbol'].isin(GOOGL_TICKERS)]['Value'].sum()

    return {
        'layer1': layer1,
        'layer2': layer2,
        'layer3': layer3,
        'googl': googl,
        'total': layer1 + layer2 + layer3 + googl
    }
```

## Extracting Margin Balance

The margin balance is found in the Balances CSV (`Balances_for_Account_*.csv`):

```python
def parse_margin(balance_csv: str) -> float:
    """Extract current margin debt from Fidelity balance CSV."""

    df = pd.read_csv(balance_csv, encoding='utf-8-sig', header=None)

    # Find "Pending activity" or negative cash
    for idx, row in df.iterrows():
        if 'Net debit' in str(row[0]):
            # Net debit is negative margin balance
            value = str(row[1]).replace('$', '').replace(',', '').replace('-', '')
            return float(value)

    return 0.0
```

Alternatively, check the "Pending activity" row in positions CSV which shows the margin debt as a negative value.

## Example Output

```python
>>> parse_portfolio('notebooks/updates/Portfolio_Positions_REDACTED.csv')
{
    'layer1': 170073.42,
    'layer2': 61725.18,
    'layer3': 13198.87,
    'googl': 1875.52,
    'total': 246872.99
}
```

## Handling Edge Cases

### Duplicate Positions
Same ticker in margin AND cash accounts:
```
JEPI (Margin): ~67% of the combined position
JEPI (Cash): ~33% of the combined position
Total JEPI: margin + cash summed
```

The parsing algorithm sums both positions automatically.

### New Tickers
If user adds a new ticker not in classification:
1. Check the ticker's characteristics
2. Assign to appropriate layer
3. Update the ticker sets in this reference

### Missing CSV
If positions CSV not found:
1. Check `notebooks/updates/` for latest file
2. Ask user to download fresh export from Fidelity
3. Use last known values as fallback
