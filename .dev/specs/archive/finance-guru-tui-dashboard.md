# Finance Guru™ TUI Dashboard - Implementation Plan

**Created**: 2025-11-17
**Version**: 1.0
**Status**: Planning
**Estimated Time**: 6-8 hours

---

## 1. Problem Statement & Objectives

### Current Pain Points
- **Too Verbose**: Running analysis requires typing long `uv run python src/...` commands
- **No Visual Context**: CLI tools run in isolation, no portfolio overview
- **Manual Repetition**: Must manually run multiple tools for comprehensive analysis
- **No Presets**: Can't save common analysis workflows

### Objectives
1. Create a professional terminal UI dashboard for Finance Guru™
2. Single command (`fin-guru`) launches full interface
3. Interactive navigation with keyboard shortcuts
4. Real-time portfolio overview from Fidelity CSV data
5. Quick analysis panel for on-demand ticker scanning
6. Saved presets for common workflows
7. Beautiful, modern terminal UX

### Success Criteria
- ✅ Launch dashboard with single command
- ✅ Navigate all features with keyboard only
- ✅ Run any analysis tool in < 5 keystrokes
- ✅ Portfolio overview auto-loads from latest CSV
- ✅ Real-time data integration works seamlessly
- ✅ Dashboard runs smoothly on macOS terminal

---

## 2. Technical Architecture

### Technology Stack

**Primary Framework**: `textual` (v0.47.0+)
- Modern Python TUI framework by Textualize
- CSS-like styling system
- Reactive/async components
- Built-in widgets (Input, Button, DataTable, etc.)
- Mouse + keyboard support
- Excellent documentation

**Supporting Libraries**:
- `rich` - Already installed, used by textual for rendering
- `yfinance` - Already integrated for price data
- `pandas` - CSV parsing for Fidelity data
- Existing CLI tools - Backend for all analysis

**Architecture Pattern**: MVC-style
```
┌─ View Layer ─────────────────────┐
│  - Textual Widgets & Screens     │
│  - Layout/Styling (CSS)           │
└───────────────────────────────────┘
           ↕
┌─ Controller Layer ───────────────┐
│  - Event Handlers                 │
│  - Navigation Logic               │
│  - User Input Processing          │
└───────────────────────────────────┘
           ↕
┌─ Model Layer ────────────────────┐
│  - Portfolio Data Parser          │
│  - Analysis Tool Integrator       │
│  - Preset Manager                 │
└───────────────────────────────────┘
```

---

## 3. Component Architecture

### 3.1 Main App Structure

```
src/ui/
├── dashboard_app.py          # Main Textual App
├── screens/
│   ├── main_screen.py        # Primary dashboard view
│   ├── analysis_screen.py    # Full analysis results
│   └── preset_screen.py      # Manage saved presets
├── widgets/
│   ├── portfolio_header.py   # Live portfolio stats
│   ├── quick_nav.py          # [1-8] menu buttons
│   ├── ticker_input.py       # Ticker entry + analysis tools selection
│   ├── results_panel.py      # Display analysis output
│   └── preset_list.py        # Saved workflow presets
├── services/
│   ├── portfolio_loader.py   # Parse Fidelity CSV
│   ├── analysis_runner.py    # Execute CLI tools
│   └── preset_manager.py     # Load/save presets
└── styles/
    └── dashboard.tcss         # Textual CSS styling
```

### 3.2 Screen Layouts

#### Main Screen (Primary View)
```
┌─ Finance Guru™ Dashboard ─────────────────────────────────────────┐
│ Portfolio: $222,214.99 | Day: -$4,091 (-1.80%) | Nov 17 2025 3:33p│ <- PortfolioHeader
├───────────────────────────────────────────────────────────────────┤
│ [1] Layer 1  [2] Layer 2  [3] Layer 3  [4] Momentum  [5] Vol     │ <- QuickNav
│ [6] Risk     [7] Golden Cross  [8] Portfolio  [R] Refresh [Q] Quit│
├─ Quick Analysis ─────────────────────────────────────────────────┤
│ Ticker: [TSLA____]  Timeframe: [90 days ▼]  [Run Analysis]       │ <- TickerInput
│ ☑ Momentum  ☑ Volatility  ☑ Risk Metrics  ☑ Moving Averages      │
├─ Results ────────────────────────────────────────────────────────┤
│                                                                    │
│ 📊 TSLA - Real-time Analysis (Last updated: 3:35pm)              │
│                                                                    │ <- ResultsPanel
│ Momentum:    RSI 42.65 (Neutral)  |  MACD Bullish                │
│ Volatility:  ATR $18.36 (High)    |  Annual Vol: 55%             │
│ Risk:        Sharpe 1.25          |  VaR -4.2%                   │
│ Trend:       Above 50-MA          |  Below 200-MA                │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

#### Analysis Screen (Detail View)
- Full-screen results for selected tool
- Tabs for each analysis type
- Side-by-side comparison mode
- Export to file option

#### Preset Screen
- List of saved workflows
- Create new preset
- Edit/delete existing
- Quick execute

---

## 4. Data Flow

### 4.1 Portfolio Data Loading

```python
# Startup sequence
1. App.on_mount() → Load latest Fidelity CSV
2. PortfolioLoader.parse_csv(notebooks/updates/Portfolio_Positions_*.csv)
3. Extract: total_value, day_change, holdings by layer
4. PortfolioHeader.update(portfolio_data)
5. Set refresh timer (5 min during market hours)
```

**Fidelity CSV Integration**:
- Path: `notebooks/updates/Portfolio_Positions_*.csv`
- Find latest by date in filename
- Parse columns: Symbol, Current Value, Today's Gain/Loss, Layer (inferred)
- Calculate totals and layer breakdowns

### 4.2 Analysis Execution Flow

```python
# User triggers analysis
1. User types ticker + selects tools
2. TickerInput.on_button_pressed("Run Analysis")
3. AnalysisRunner.execute(ticker, tools, timeframe, realtime=True)
4. Parallel execution of selected CLI tools:
   - momentum_cli.py TSLA --days 90 --realtime --output json
   - volatility_cli.py TSLA --days 90 --realtime --output json
   - risk_metrics_cli.py TSLA --days 90 --realtime --output json
   - moving_averages_cli.py TSLA --days 252 --fast 50 --slow 200 --realtime --output json
5. Parse JSON outputs
6. ResultsPanel.display(formatted_results)
7. Cache results for quick re-display
```

### 4.3 Preset Execution

```python
# Preset structure (YAML)
presets:
  morning-scan:
    name: "Morning Layer 1 Scan"
    tickers: [PLTR, TSLA, NVDA, AAPL, GOOGL]
    tools: [momentum, volatility]
    timeframe: 90
    realtime: true

  golden-cross-watch:
    name: "Golden Cross Detection"
    tickers: [PLTR, TSLA, COIN]
    tools: [moving_averages]
    ma_config:
      fast: 50
      slow: 200
    timeframe: 252
    realtime: true
```

**Storage**: `~/.config/finance-guru/presets.yaml`

---

## 5. Implementation Roadmap

### Phase 1: Foundation (2 hours)

#### Step 1.1: Install Dependencies
```bash
uv add textual
uv add pyyaml  # For preset storage
```

#### Step 1.2: Create Basic App Shell
```python
# src/ui/dashboard_app.py
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer

class FinanceGuruApp(App):
    """Finance Guru™ TUI Dashboard"""

    TITLE = "Finance Guru™ Dashboard"
    CSS_PATH = "styles/dashboard.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(id="main-container")
        yield Footer()

    def action_quit(self) -> None:
        self.exit()

    def action_refresh(self) -> None:
        # Reload portfolio data
        pass

if __name__ == "__main__":
    app = FinanceGuruApp()
    app.run()
```

#### Step 1.3: Create CLI Entry Point
```python
# src/cli/fin_guru.py
#!/usr/bin/env python3
"""Entry point for Finance Guru TUI Dashboard"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ui.dashboard_app import FinanceGuruApp

def main():
    app = FinanceGuruApp()
    app.run()

if __name__ == "__main__":
    main()
```

#### Step 1.4: Create Shell Alias
```bash
# Add to ~/.zshrc or ~/.bashrc
alias fin-guru='uv run python src/cli/fin_guru.py'
```

**Milestone 1**: Can launch dashboard with `fin-guru` command

---

### Phase 2: Portfolio Header (1 hour)

#### Step 2.1: Portfolio Data Loader
```python
# src/ui/services/portfolio_loader.py
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Dict, Optional

class PortfolioLoader:
    """Load and parse Fidelity portfolio CSV data"""

    @staticmethod
    def find_latest_csv() -> Optional[Path]:
        """Find most recent Portfolio_Positions CSV"""
        updates_dir = Path("notebooks/updates")
        csv_files = list(updates_dir.glob("Portfolio_Positions_*.csv"))

        if not csv_files:
            return None

        # Sort by filename date (MMM-DD-YYYY format)
        return max(csv_files, key=lambda p: p.stat().st_mtime)

    @staticmethod
    def parse_portfolio(csv_path: Path) -> Dict:
        """Parse portfolio CSV and extract key metrics"""
        df = pd.read_csv(csv_path)

        # Calculate totals
        total_value = df['Current Value'].sum()
        day_change = df['Today\'s Gain/Loss Dollar'].sum()
        day_change_pct = (day_change / total_value) * 100

        # Group by layer (inferred from symbol patterns)
        layer1 = df[df['Symbol'].isin(['PLTR', 'TSLA', 'NVDA', 'AAPL', 'GOOGL', 'COIN', 'MSTR', 'SOFI'])]
        layer2 = df[df['Symbol'].isin(['JEPI', 'JEPQ', 'QQQI', 'SPYI', 'QQQY', 'YMAX', 'MSTY', 'AMZY', 'CLM', 'CRF', 'BDJ', 'ETY', 'ETV', 'ECAT', 'UTG', 'BST'])]
        layer3 = df[df['Symbol'].isin(['SQQQ'])]

        return {
            'total_value': total_value,
            'day_change': day_change,
            'day_change_pct': day_change_pct,
            'layer1_value': layer1['Current Value'].sum(),
            'layer2_value': layer2['Current Value'].sum(),
            'layer3_value': layer3['Current Value'].sum(),
            'timestamp': datetime.now(),
        }
```

#### Step 2.2: Portfolio Header Widget
```python
# src/ui/widgets/portfolio_header.py
from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text

class PortfolioHeader(Widget):
    """Display live portfolio statistics"""

    portfolio_data = reactive({})

    def render(self) -> Text:
        if not self.portfolio_data:
            return Text("Loading portfolio data...")

        data = self.portfolio_data
        total = f"${data['total_value']:,.2f}"
        change = f"${data['day_change']:,.2f}"
        change_pct = f"({data['day_change_pct']:+.2f}%)"
        timestamp = data['timestamp'].strftime("%b %d, %Y %I:%M%p")

        # Color code based on gain/loss
        change_color = "green" if data['day_change'] >= 0 else "red"

        return Text.assemble(
            ("Portfolio: ", "bold"),
            (total, "bold cyan"),
            " | Day: ",
            (change, change_color),
            " ",
            (change_pct, change_color),
            " | ",
            (f"📅 {timestamp}", "dim"),
        )
```

**Milestone 2**: Portfolio header shows live data from latest CSV

---

### Phase 3: Quick Navigation (1 hour)

#### Step 3.1: Quick Nav Widget
```python
# src/ui/widgets/quick_nav.py
from textual.containers import Horizontal
from textual.widgets import Button

class QuickNav(Horizontal):
    """Quick navigation buttons for main functions"""

    def compose(self):
        yield Button("Layer 1 Growth", id="layer1", variant="primary")
        yield Button("Layer 2 Income", id="layer2", variant="primary")
        yield Button("Layer 3 Hedge", id="layer3", variant="primary")
        yield Button("Momentum Scan", id="momentum")
        yield Button("Volatility Check", id="volatility")
        yield Button("Risk Analysis", id="risk")
        yield Button("Golden Cross", id="golden-cross")
        yield Button("Portfolio View", id="portfolio")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        # Emit custom event for parent to handle
        self.post_message(self.NavButtonPressed(button_id))

    class NavButtonPressed(Message):
        """Custom message when nav button clicked"""
        def __init__(self, button_id: str) -> None:
            self.button_id = button_id
            super().__init__()
```

#### Step 3.2: Handle Navigation Events
```python
# In dashboard_app.py
def on_quick_nav_nav_button_pressed(self, message: QuickNav.NavButtonPressed) -> None:
    """Handle quick nav button clicks"""
    button_id = message.button_id

    if button_id == "layer1":
        self.run_layer_scan(layer=1)
    elif button_id == "momentum":
        self.show_momentum_panel()
    # ... etc
```

**Milestone 3**: All quick nav buttons functional

---

### Phase 4: Ticker Input & Analysis (2 hours)

#### Step 4.1: Ticker Input Widget
```python
# src/ui/widgets/ticker_input.py
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Button, Checkbox, Select

class TickerInput(Container):
    """Ticker entry and analysis tool selection"""

    def compose(self):
        with Vertical():
            with Horizontal(classes="input-row"):
                yield Input(placeholder="Enter ticker (e.g., TSLA)", id="ticker-input")
                yield Select(
                    options=[
                        ("30 days", 30),
                        ("90 days", 90),
                        ("180 days", 180),
                        ("1 year", 252),
                    ],
                    value=90,
                    id="timeframe-select"
                )
                yield Button("Run Analysis", variant="success", id="run-btn")

            with Horizontal(classes="tools-row"):
                yield Checkbox("Momentum", id="tool-momentum", value=True)
                yield Checkbox("Volatility", id="tool-volatility", value=True)
                yield Checkbox("Risk Metrics", id="tool-risk", value=True)
                yield Checkbox("Moving Averages", id="tool-ma", value=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            ticker = self.query_one("#ticker-input", Input).value.upper()
            timeframe = self.query_one("#timeframe-select", Select).value

            tools = []
            if self.query_one("#tool-momentum", Checkbox).value:
                tools.append("momentum")
            if self.query_one("#tool-volatility", Checkbox).value:
                tools.append("volatility")
            if self.query_one("#tool-risk", Checkbox).value:
                tools.append("risk")
            if self.query_one("#tool-ma", Checkbox).value:
                tools.append("moving_averages")

            # Post message to parent
            self.post_message(
                self.RunAnalysis(ticker, timeframe, tools)
            )

    class RunAnalysis(Message):
        def __init__(self, ticker: str, timeframe: int, tools: list):
            self.ticker = ticker
            self.timeframe = timeframe
            self.tools = tools
            super().__init__()
```

#### Step 4.2: Analysis Runner Service
```python
# src/ui/services/analysis_runner.py
import subprocess
import json
from pathlib import Path
from typing import Dict, List

class AnalysisRunner:
    """Execute CLI analysis tools and parse results"""

    @staticmethod
    def run_tool(tool: str, ticker: str, days: int, **kwargs) -> Dict:
        """Run a single analysis tool and return JSON results"""

        tool_paths = {
            "momentum": "src/utils/momentum_cli.py",
            "volatility": "src/utils/volatility_cli.py",
            "risk": "src/analysis/risk_metrics_cli.py",
            "moving_averages": "src/utils/moving_averages_cli.py",
        }

        cmd = [
            "uv", "run", "python",
            tool_paths[tool],
            ticker,
            "--days", str(days),
            "--realtime",
            "--output", "json"
        ]

        # Add tool-specific args
        if tool == "moving_averages" and "fast" in kwargs:
            cmd.extend(["--fast", str(kwargs["fast"])])
            cmd.extend(["--slow", str(kwargs["slow"])])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {"error": result.stderr}

        # Parse JSON output
        return json.loads(result.stdout)

    @staticmethod
    def run_analysis(ticker: str, timeframe: int, tools: List[str]) -> Dict[str, Dict]:
        """Run multiple tools in parallel and return combined results"""
        results = {}

        for tool in tools:
            try:
                results[tool] = AnalysisRunner.run_tool(tool, ticker, timeframe)
            except Exception as e:
                results[tool] = {"error": str(e)}

        return results
```

**Milestone 4**: Can run analysis from ticker input panel

---

### Phase 5: Results Display (1.5 hours)

#### Step 5.1: Results Panel Widget
```python
# src/ui/widgets/results_panel.py
from textual.containers import Container, VerticalScroll
from textual.widgets import Static, Label
from rich.table import Table

class ResultsPanel(VerticalScroll):
    """Display analysis results in formatted layout"""

    def display_results(self, ticker: str, results: Dict) -> None:
        """Format and display analysis results"""

        # Clear existing results
        self.remove_children()

        # Header
        timestamp = datetime.now().strftime("%I:%M%p")
        self.mount(Label(f"📊 {ticker} - Real-time Analysis (Last updated: {timestamp})", classes="result-header"))

        # Momentum Results
        if "momentum" in results and "error" not in results["momentum"]:
            momentum = results["momentum"]
            table = Table(title="Momentum Indicators", show_header=False)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")

            if "rsi" in momentum:
                table.add_row("RSI", f"{momentum['rsi']['current_rsi']:.2f} ({momentum['rsi']['rsi_signal']})")
            if "macd" in momentum:
                table.add_row("MACD", momentum['macd']['signal'].capitalize())

            self.mount(Static(table))

        # Volatility Results
        if "volatility" in results and "error" not in results["volatility"]:
            vol = results["volatility"]
            table = Table(title="Volatility Analysis", show_header=False)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")

            if "atr" in vol:
                table.add_row("ATR", f"${vol['atr']['atr']:.2f} ({vol['atr']['atr_percent']:.2f}%)")
            if "volatility_regime" in vol:
                table.add_row("Regime", vol['volatility_regime'].upper())

            self.mount(Static(table))

        # Risk Metrics Results
        if "risk" in results and "error" not in results["risk"]:
            risk = results["risk"]
            table = Table(title="Risk Metrics", show_header=False)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")

            if "sharpe_ratio" in risk:
                table.add_row("Sharpe Ratio", f"{risk['sharpe_ratio']:.2f}")
            if "var_95" in risk:
                table.add_row("VaR (95%)", f"{risk['var_95']:.2f}%")

            self.mount(Static(table))

        # Moving Average Results
        if "moving_averages" in results and "error" not in results["moving_averages"]:
            ma = results["moving_averages"]
            table = Table(title="Trend Analysis", show_header=False)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")

            if "primary_ma" in ma:
                table.add_row("Price vs MA", ma['primary_ma']['price_vs_ma'])
            if "crossover" in ma:
                table.add_row("Crossover Signal", ma['crossover']['signal'])

            self.mount(Static(table))
```

**Milestone 5**: Results display beautifully in panel

---

### Phase 6: Presets System (1 hour)

#### Step 6.1: Preset Manager
```python
# src/ui/services/preset_manager.py
from pathlib import Path
import yaml

class PresetManager:
    """Manage saved analysis presets"""

    PRESETS_FILE = Path.home() / ".config" / "finance-guru" / "presets.yaml"

    @classmethod
    def load_presets(cls) -> Dict:
        """Load presets from YAML file"""
        if not cls.PRESETS_FILE.exists():
            return cls.get_default_presets()

        with open(cls.PRESETS_FILE) as f:
            return yaml.safe_load(f)

    @classmethod
    def save_preset(cls, name: str, config: Dict) -> None:
        """Save a new preset"""
        presets = cls.load_presets()
        presets[name] = config

        cls.PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(cls.PRESETS_FILE, 'w') as f:
            yaml.dump(presets, f)

    @classmethod
    def get_default_presets(cls) -> Dict:
        """Default preset configurations"""
        return {
            "morning-scan": {
                "name": "Morning Layer 1 Scan",
                "tickers": ["PLTR", "TSLA", "NVDA", "AAPL", "GOOGL"],
                "tools": ["momentum", "volatility"],
                "timeframe": 90,
                "realtime": True
            },
            "golden-cross-watch": {
                "name": "Golden Cross Detection",
                "tickers": ["PLTR", "TSLA", "COIN"],
                "tools": ["moving_averages"],
                "ma_config": {"fast": 50, "slow": 200},
                "timeframe": 252,
                "realtime": True
            },
            "volatility-check": {
                "name": "High Volatility Positions",
                "tickers": ["PLTR", "COIN", "MSTR"],
                "tools": ["volatility", "risk"],
                "timeframe": 90,
                "realtime": True
            }
        }
```

**Milestone 6**: Presets can be loaded and executed

---

### Phase 7: Styling & Polish (30 min)

#### Step 7.1: CSS Styling
```css
/* src/ui/styles/dashboard.tcss */

Screen {
    background: $surface;
}

PortfolioHeader {
    height: 3;
    background: $primary;
    color: $text;
    padding: 1;
    text-align: center;
}

QuickNav {
    height: 5;
    padding: 1;
    background: $panel;
}

QuickNav Button {
    margin: 0 1;
}

TickerInput {
    height: 8;
    border: solid $accent;
    padding: 1;
}

ResultsPanel {
    height: 1fr;
    border: solid $primary;
    padding: 1;
}

.result-header {
    text-style: bold;
    color: $accent;
    margin: 1 0;
}

.error-message {
    color: $error;
    text-style: italic;
}
```

**Milestone 7**: Dashboard looks polished and professional

---

## 6. Testing Strategy

### Unit Tests
- `PortfolioLoader.parse_portfolio()` - CSV parsing accuracy
- `AnalysisRunner.run_tool()` - CLI tool execution
- `PresetManager.load_presets()` - YAML parsing

### Integration Tests
- Full analysis workflow (ticker input → execution → results display)
- Preset execution end-to-end
- Portfolio refresh cycle

### Manual Testing Checklist
- [ ] Launch with `fin-guru` command
- [ ] Portfolio header loads correct data from latest CSV
- [ ] All quick nav buttons work
- [ ] Can enter ticker and run analysis
- [ ] Results display correctly for all 4 tools
- [ ] Keyboard shortcuts work (Q, R, 1-8)
- [ ] Presets execute successfully
- [ ] Dashboard refreshes portfolio data
- [ ] Error handling for invalid tickers
- [ ] Performance acceptable on macOS terminal

---

## 7. Potential Challenges & Solutions

### Challenge 1: CLI Tool Output Parsing
**Problem**: CLI tools currently output human-readable text, not JSON
**Solution**: All tools already support `--output json` flag - use this exclusively

### Challenge 2: Async Tool Execution
**Problem**: Running 4 tools serially is slow
**Solution**: Use `asyncio` to run tools in parallel, collect results

### Challenge 3: Large Result Display
**Problem**: Full analysis output may overflow panel
**Solution**: Use `VerticalScroll` container, implement tab navigation for tools

### Challenge 4: CSV Auto-Detection
**Problem**: Filename date format may vary
**Solution**: Use file modification time as fallback, implement date parsing with multiple formats

### Challenge 5: Real-time Updates
**Problem**: Auto-refresh may interrupt user input
**Solution**: Only refresh header, not active results; pause refresh when user typing

---

## 8. Future Enhancements (Phase 2)

### Auto-Refresh Mode
- Toggle auto-refresh every 1-5 minutes during market hours
- Smart refresh (only update changed data)
- Notification system for significant changes

### Comparison View
- Side-by-side analysis of multiple tickers
- Historical comparison (today vs. yesterday)
- Layer performance comparison

### Export Functionality
- Save results to markdown/PDF
- Email analysis results
- Integration with Google Sheets Portfolio Tracker

### Advanced Presets
- Conditional presets (if RSI < 30, run full analysis)
- Scheduled presets (auto-run at market open/close)
- Alert-based presets (notify when Golden Cross detected)

### Chart Visualization
- ASCII charts for price history
- Sparklines for key metrics
- Plotext integration for terminal charts

---

## 9. Implementation Timeline

| Phase | Description | Time | Status |
|-------|-------------|------|--------|
| 1 | Foundation & App Shell | 2h | Pending |
| 2 | Portfolio Header | 1h | Pending |
| 3 | Quick Navigation | 1h | Pending |
| 4 | Ticker Input & Analysis | 2h | Pending |
| 5 | Results Display | 1.5h | Pending |
| 6 | Presets System | 1h | Pending |
| 7 | Styling & Polish | 0.5h | Pending |
| **Total** | | **6-8h** | |

---

## 10. Success Metrics

- ✅ Single command launch (`fin-guru`)
- ✅ < 5 keystrokes for any analysis
- ✅ Real-time portfolio data integration
- ✅ All 4 analysis tools accessible
- ✅ Preset system functional
- ✅ Beautiful, professional terminal UX
- ✅ Fast, responsive navigation
- ✅ Error handling for edge cases

---

## Appendix A: Quick Reference Commands

### Development
```bash
# Launch dashboard
fin-guru

# Run with debug mode
uv run python src/cli/fin_guru.py --dev

# Run tests
pytest tests/ui/
```

### Keyboard Shortcuts
- `Q` - Quit dashboard
- `R` - Refresh portfolio data
- `1-8` - Quick nav buttons
- `T` - Focus ticker input
- `Tab` - Navigate between widgets
- `Enter` - Activate button/run analysis
- `Esc` - Cancel/go back

### File Locations
- **App**: `src/ui/dashboard_app.py`
- **Presets**: `~/.config/finance-guru/presets.yaml`
- **Styles**: `src/ui/styles/dashboard.tcss`
- **Portfolio Data**: `notebooks/updates/Portfolio_Positions_*.csv`

---

## Appendix B: Example Preset Configuration

```yaml
# ~/.config/finance-guru/presets.yaml

morning-scan:
  name: "Morning Layer 1 Scan"
  description: "Quick momentum + volatility check of growth stocks"
  tickers: [PLTR, TSLA, NVDA, AAPL, GOOGL]
  tools: [momentum, volatility]
  timeframe: 90
  realtime: true
  output: summary  # or 'detailed'

golden-cross-watch:
  name: "Golden Cross Detection"
  description: "Monitor 50/200 MA crossovers"
  tickers: [PLTR, TSLA, COIN]
  tools: [moving_averages]
  ma_config:
    fast: 50
    slow: 200
  timeframe: 252
  realtime: true

volatility-check:
  name: "High Volatility Positions"
  description: "Risk assessment for volatile holdings"
  tickers: [PLTR, COIN, MSTR]
  tools: [volatility, risk]
  timeframe: 90
  realtime: true
  alerts:
    - condition: "atr_percent > 6"
      action: "highlight"

layer2-income-review:
  name: "Layer 2 Income Analysis"
  description: "Monthly dividend fund review"
  tickers: [JEPI, JEPQ, QQQI, SPYI, QQQY, YMAX, MSTY, AMZY]
  tools: [risk, moving_averages]
  timeframe: 180
  realtime: true
  group_by: "bucket"  # Based on Dividend Master Strategy
```

---

**End of Implementation Plan**
