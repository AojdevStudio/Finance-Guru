---
name: price-history-tracking
description: Track historical prices for all portfolio holdings. Captures daily snapshots, stores in SQLite database, syncs to Google Sheets for charting. Triggers on price history, track prices, portfolio chart, historical prices, sync prices to sheets.
---

# Price History Tracking

## Purpose

Maintain historical price data for all portfolio holdings to enable:
- Portfolio value charting over time
- Layer-by-layer performance tracking
- Historical price analysis
- Google Sheets chart integration
- Future frontend UI dashboards

## When to Use

Use this skill when:
- User mentions: "price history", "track prices", "portfolio chart"
- User wants to "chart my portfolio" or "plot holdings"
- Setting up historical tracking: "sync prices", "historical prices"
- Exporting data: "export to sheets", "price data for charts"
- Checking tracking status: "price history stats"

## Architecture

### Database Location
```
~/.config/finance-guru/price_history.db (SQLite)
```

### Tables
1. **price_snapshots** - Individual ticker prices by date
2. **portfolio_snapshots** - Aggregate portfolio value
3. **holding_snapshots** - Individual holding values within portfolio

### CLI Commands
```bash
# Base path
src/services/price_history_cli.py

# Available commands
capture     # Capture daily snapshot
import      # Import historical data
history     # View price history for symbol
portfolio   # View portfolio value history
export      # Export for Google Sheets
stats       # Database statistics
cleanup     # Remove old data
```

## Core Workflows

### 1. Daily Price Capture (Recommended: Run Daily)

**Manual Trigger**:
```bash
uv run python src/services/price_history_cli.py capture
```

**What It Does**:
1. Loads holdings from latest Portfolio_Positions CSV
2. Fetches current prices from yfinance for all symbols
3. Stores individual price snapshots
4. Creates portfolio value snapshot with layer breakdown

**Output Example**:
```
✅ Captured 24 price snapshots for 2026-01-14

📊 Symbols: PLTR, TSLA, NVDA, AAPL, GOOGL, COIN, MSTR, SOFI, JEPI, JEPQ...

💼 Portfolio Snapshot:
   Total Value:  $250,000.00
   Layer 1:      $170,000.00
   Layer 2:      $65,000.00
   Layer 3:      $15,000.00
   Holdings:     24
```

### 2. Historical Data Import (Initial Setup)

**Import 1 Year of History**:
```bash
uv run python src/services/price_history_cli.py import PLTR TSLA NVDA JEPI JEPQ --days 365
```

**For All Layer 1 Holdings**:
```bash
uv run python src/services/price_history_cli.py import PLTR TSLA NVDA AAPL GOOGL COIN MSTR SOFI --days 365
```

**For All Layer 2 Holdings**:
```bash
uv run python src/services/price_history_cli.py import JEPI JEPQ QQQI SPYI QQQY YMAX MSTY AMZY CLM CRF BDJ ETY ETV ECAT UTG BST --days 365
```

### 3. View Price History

**Single Symbol**:
```bash
uv run python src/services/price_history_cli.py history PLTR --days 30
```

**Output**:
```
📈 PRICE HISTORY: PLTR
   📈 Change: $+12.50 (+15.20%)

Date         Price      Change         Volume
--------------------------------------------------
2026-01-01   $75.00     +0.50      45,000,000
2026-01-02   $76.20     +1.20      52,000,000
...
```

### 4. View Portfolio History

```bash
uv run python src/services/price_history_cli.py portfolio --days 90
```

**Output**:
```
💼 PORTFOLIO VALUE HISTORY
   📈 Change: $+25,000.00 (+10.50%)

Date         Total        Layer 1      Layer 2     Layer 3
-----------------------------------------------------------------
2025-10-15   $225,000     $155,000     $55,000     $15,000
2025-10-16   $228,000     $158,000     $55,500     $14,500
...
```

### 5. Export for Google Sheets

**CSV Format (for manual import)**:
```bash
uv run python src/services/price_history_cli.py export --type portfolio --format csv > portfolio_history.csv
```

**JSON Format (for API/automation)**:
```bash
uv run python src/services/price_history_cli.py export --type prices --format json
```

## Google Sheets Integration

### Create "Price History" Sheet

**Sheet Structure**:
```
A: Date (YYYY-MM-DD)
B: Total Value
C: Layer 1 (Growth)
D: Layer 2 (Income)
E: Layer 3 (Hedge)
```

### Sync Workflow

**Step 1**: Export data from CLI
```bash
uv run python src/services/price_history_cli.py export --type portfolio --format csv --days 90
```

**Step 2**: Use mcp__gdrive__sheets to update
```javascript
// Read spreadsheet ID from user-profile.yaml
// Update Price History sheet with exported data

mcp__gdrive__sheets(
    operation: "spreadsheets.values.update",
    params: {
        spreadsheetId: SPREADSHEET_ID,
        range: "Price History!A1:E100",
        valueInputOption: "USER_ENTERED",
        requestBody: {
            values: [[header_row], [data_rows...]]
        }
    }
)
```

### Chart Configuration (in Google Sheets)

**Recommended Chart Type**: Line Chart

**Setup**:
1. Select columns A:E (Date + Values)
2. Insert → Chart → Line Chart
3. Configure:
   - X-axis: Date (Column A)
   - Series: Total, Layer 1, Layer 2, Layer 3
   - Enable smooth lines
   - Show legend at bottom

**Alternative: Stacked Area Chart**
- Shows layer composition over time
- Good for visualizing layer allocation changes

## Automation (Future)

### Daily Capture via Cron

```bash
# Add to crontab (capture at market close 4:30 PM ET)
30 16 * * 1-5 cd /path/to/Finance-Guru && uv run python src/services/price_history_cli.py capture
```

### Google Apps Script Trigger

Can create a daily trigger in Google Sheets that:
1. Calls an API endpoint (future)
2. Updates the Price History sheet automatically

## Data Models

### PriceSnapshotInput
```python
{
    "symbol": "PLTR",
    "price": 75.42,
    "open_price": 74.50,
    "high_price": 76.10,
    "low_price": 74.20,
    "previous_close": 74.85,
    "volume": 45000000,
    "snapshot_date": "2026-01-14",
    "timestamp": "2026-01-14T16:00:00",
    "source": "yfinance"
}
```

### PortfolioValueSnapshotInput
```python
{
    "total_value": 250000.00,
    "holdings": [...],
    "snapshot_date": "2026-01-14",
    "timestamp": "2026-01-14T16:00:00",
    "cash_balance": 5000.00,
    "margin_balance": -15000.00,
    # Computed fields:
    "layer1_value": 170000.00,
    "layer2_value": 65000.00,
    "layer3_value": 15000.00,
    "holding_count": 24
}
```

## Database Statistics

```bash
uv run python src/services/price_history_cli.py stats
```

**Output**:
```
📊 PRICE HISTORY DATABASE STATS

🗄️  Database: /home/user/.config/finance-guru/price_history.db

📈 Price Snapshots:
   Total records:   8,760
   Unique symbols:  24
   Date range:      2025-01-14 to 2026-01-14

💼 Portfolio Snapshots: 365
   Latest value:    $250,000.00 (2026-01-14)
```

## Maintenance

### Cleanup Old Data
```bash
# Keep only last 2 years
uv run python src/services/price_history_cli.py cleanup --days 730
```

### Database Location
```
~/.config/finance-guru/price_history.db
```

To reset (delete all history):
```bash
rm ~/.config/finance-guru/price_history.db
```

## Integration with Other Skills

### PortfolioSyncing → Price History
After syncing portfolio from Fidelity CSV, run capture to record prices.

### Dividend Tracking + Price History
Combine dividend income data with portfolio value for total return analysis.

### Monte Carlo + Price History
Use historical volatility from price history for more accurate simulations.

## Agent Permissions

**Builder** (Write-enabled):
- Can run capture commands
- Can import historical data
- Can sync to Google Sheets

**Quant Analyst** (Read-only):
- Can query price history for analysis
- Can calculate returns and volatility

**All Other Agents** (Read-only):
- Can view statistics and history

## Example Session

**User**: "Set up price history tracking for my portfolio"

**Agent Workflow**:
1. ✅ Check database stats (first run = empty)
2. ✅ Import 1 year of history for all holdings
3. ✅ Capture today's snapshot
4. ✅ Export data for Google Sheets
5. ✅ Create/update "Price History" sheet
6. ✅ Provide charting instructions

**Commands Executed**:
```bash
# 1. Check current state
uv run python src/services/price_history_cli.py stats

# 2. Import historical data
uv run python src/services/price_history_cli.py import PLTR TSLA NVDA AAPL GOOGL COIN MSTR SOFI JEPI JEPQ QQQI SPYI QQQY YMAX MSTY AMZY CLM CRF BDJ ETY ETV ECAT UTG BST SQQQ --days 365

# 3. Capture today
uv run python src/services/price_history_cli.py capture

# 4. Export for sheets
uv run python src/services/price_history_cli.py export --type portfolio --format csv
```

---

**Skill Type**: Domain (workflow guidance)
**Enforcement**: SUGGEST (high priority advisory)
**Priority**: High
**Line Count**: < 350 (following 500-line rule)
