# Finance Guru™ TUI Dashboard v0.1 - Revised Implementation Plan

**Created**: 2025-11-17 (Revised after critical review)
**Version**: v0.1 (MVP)
**Estimated Time**: 2-3 hours (realistic)
**Philosophy**: Ship something useful today, iterate tomorrow

---

## Critical Decisions Based on Feedback

### What Changed
1. ✅ **Import functions, not subprocess** - 10x faster, type-safe
2. ✅ **Config abstraction layer** - No more hard-coded paths
3. ✅ **Domain models** - Typed portfolio objects
4. ✅ **Single screen only** - No scope creep
5. ✅ **Sequential execution** - Parallel in v0.2
6. ✅ **Schema validation** - Check CSV columns

### What's Deferred to v0.2
- ❌ Preset system
- ❌ Multiple screens
- ❌ Parallel execution
- ❌ Auto-refresh
- ❌ Advanced keyboard shortcuts

---

## v0.1 Scope (Absolute Minimum)

### Must Have
1. Single command launch: `fin-guru`
2. Portfolio header with latest CSV data
3. Ticker input field
4. Tool checkboxes (Momentum, Volatility, Risk, MA)
5. "Run Analysis" button
6. Results display (simple, readable)
7. Error handling (invalid ticker, missing CSV)
8. Quit with `Q`

### Success Criteria
- ✅ Launches in < 2 seconds
- ✅ Shows portfolio data from latest CSV
- ✅ Can analyze any ticker in < 5 keystrokes
- ✅ Results are readable and accurate
- ✅ Doesn't crash on errors

---

## Architecture

```
src/
├── config.py                    # NEW: Central configuration
├── core/
│   └── portfolio.py             # NEW: Domain models
├── ui/
│   ├── app.py                   # Main Textual app
│   ├── services/
│   │   ├── portfolio_loader.py  # REVISED: With validation
│   │   └── analysis_runner.py   # REVISED: Import, not subprocess
│   └── widgets/
│       ├── portfolio_header.py
│       ├── ticker_input.py
│       └── results_panel.py
└── cli/
    └── fin_guru.py              # Entry point
```

---

## Implementation Steps

### Step 1: Config & Domain Layer (30 min)

#### 1.1 Create Config Module
```python
# src/config.py
from pathlib import Path
import os
import yaml

class FinGuruConfig:
    PROJECT_ROOT = Path(__file__).parent.parent
    PORTFOLIO_DIR = Path(os.getenv(
        "FIN_GURU_PORTFOLIO_DIR",
        PROJECT_ROOT / "notebooks/updates"
    ))
    CONFIG_DIR = Path.home() / ".config" / "finance-guru"
    LAYERS_FILE = CONFIG_DIR / "layers.yaml"

    @classmethod
    def load_layers(cls):
        """Load layer configuration with safe fallback to defaults."""
        default_layers = {
            "layer1": ["PLTR", "TSLA", "NVDA", "AAPL", "GOOGL", "COIN", "MSTR", "SOFI"],
            "layer2": ["JEPI", "JEPQ", "QQQI", "SPYI", "QQQY", "YMAX", "MSTY", "AMZY",
                       "CLM", "CRF", "BDJ", "ETY, "ETV", "ECAT", "UTG", "BST"],
            "layer3": ["SQQQ"],
        }

        if not cls.LAYERS_FILE.exists():
            return default_layers

        try:
            with open(cls.LAYERS_FILE) as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            # On any parse error, fall back to defaults
            return default_layers

        if not isinstance(data, dict):
            return default_layers

        # Normalize keys and ensure values are lists of symbols
        normalized: dict[str, list[str]] = {}
        for layer, symbols in data.items():
            if not isinstance(symbols, (list, tuple)):
                continue
            normalized[layer] = [str(sym).upper() for sym in symbols]

        return normalized or default_layers
```

#### 1.2 Create Pydantic Models (Following Existing Architecture)
```python
# src/models/dashboard_inputs.py
# ALREADY CREATED - See file for full implementation

from pydantic import BaseModel, Field, field_validator, computed_field

class HoldingInput(BaseModel):
    """Individual portfolio holding from Fidelity CSV"""
    symbol: str
    quantity: float
    current_value: float
    day_change: float
    day_change_pct: float
    layer: Literal["layer1", "layer2", "layer3", "unknown"]

    # Validators for symbol format, etc.

class PortfolioSnapshotInput(BaseModel):
    """Complete portfolio snapshot"""
    total_value: float
    day_change: float
    day_change_pct: float
    holdings: list[HoldingInput]
    timestamp: datetime

    # Computed properties for layer values/percentages
    @computed_field
    @property
    def layer1_value(self) -> float:
        return sum(h.current_value for h in self.holdings if h.layer == "layer1")

    # Similar for layer2_value, layer3_value, layer1_pct, etc.
```

**Note**: Uses Pydantic v2 to match existing models in `src/models/`

**Checkpoint**: Config and models compile

---

### Step 2: Portfolio Loader (30 min)

```python
# src/ui/services/portfolio_loader.py
from pathlib import Path
from datetime import datetime
import pandas as pd
from src.config import FinGuruConfig
from src.models.dashboard_inputs import PortfolioSnapshotInput, HoldingInput

class PortfolioLoader:
    @staticmethod
    def find_latest_csv() -> Path | None:
        csv_files = list(FinGuruConfig.PORTFOLIO_DIR.glob("Portfolio_Positions_*.csv"))
        if not csv_files:
            return None
        return max(csv_files, key=lambda p: p.stat().st_mtime)

    @staticmethod
    def parse_portfolio(csv_path: Path) -> PortfolioSnapshotInput:
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {e}")

        # Validate columns
        required = ['Symbol', 'Current Value', "Today's Gain/Loss Dollar"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        # Load layers
        layer_map = FinGuruConfig.load_layers()
        symbol_to_layer = {}
        for layer, symbols in layer_map.items():
            for symbol in symbols:
                symbol_to_layer[str(symbol).upper()] = layer

        # Parse holdings (Pydantic will validate automatically)
        holdings = []
        for _, row in df.iterrows():
            raw_symbol = str(row['Symbol']).strip()
            symbol = raw_symbol.upper()
            holdings.append(HoldingInput(
                symbol=symbol,
                quantity=row.get('Quantity', 0),
                current_value=row['Current Value'],
                day_change=row["Today's Gain/Loss Dollar"],
                day_change_pct=row.get("Today's Gain/Loss Percent", 0),
                layer=symbol_to_layer.get(symbol, "unknown")
            ))

        total_value = sum(h.current_value for h in holdings)
        day_change = sum(h.day_change for h in holdings)
        day_change_pct = (day_change / total_value * 100) if total_value else 0

        # Pydantic model validates all inputs automatically
        return PortfolioSnapshotInput(
            total_value=total_value,
            day_change=day_change,
            day_change_pct=day_change_pct,
            holdings=holdings,
            timestamp=datetime.now()
        )

    @classmethod
    def load_latest(cls) -> PortfolioSnapshotInput | None:
        """Convenience method: find latest CSV and parse it"""
        csv_path = cls.find_latest_csv()
        if not csv_path:
            return None
        return cls.parse_portfolio(csv_path)
```

**Checkpoint**: Can load and parse real CSV

---

### Step 3: Analysis Runner (30 min)

```python
# src/ui/services/analysis_runner.py
from typing import Dict, List
from src.models.momentum_inputs import MomentumConfig
from src.models.volatility_inputs import VolatilityConfig
from src.models.risk_inputs import RiskCalculationConfig
from src.models.moving_avg_inputs import MovingAverageConfig

# Import the actual calculation functions
from src.utils.momentum_cli import fetch_momentum_data
from src.utils.momentum import MomentumIndicators
from src.utils.volatility_cli import fetch_price_data
from src.utils.volatility import calculate_volatility
from src.analysis.risk_metrics_cli import fetch_price_data as fetch_risk_data
from src.analysis.risk_metrics import RiskCalculator
from src.utils.moving_averages_cli import fetch_ma_data
from src.utils.moving_averages import MovingAverageCalculator

class AnalysisRunner:
    """Execute analysis tools via Python imports (not subprocess)"""

    @staticmethod
    def run_momentum(ticker: str, days: int, realtime: bool = True) -> Dict:
        try:
            data = fetch_momentum_data(ticker, days, realtime=realtime)
            config = MomentumConfig()
            calculator = MomentumIndicators(config)
            results = calculator.calculate_all(data)
            return {
                "ok": True,
                "tool": "momentum",
                "data": results.model_dump(),
                "error": None,
            }
        except Exception as e:
            return {
                "ok": False,
                "tool": "momentum",
                "data": None,
                "error": str(e),
            }

    @staticmethod
    def run_volatility(ticker: str, days: int, realtime: bool = True) -> Dict:
        try:
            data = fetch_price_data(ticker, days, realtime=realtime)
            config = VolatilityConfig()
            results = calculate_volatility(data, config)
            return {
                "ok": True,
                "tool": "volatility",
                "data": results.model_dump(),
                "error": None,
            }
        except Exception as e:
            return {
                "ok": False,
                "tool": "volatility",
                "data": None,
                "error": str(e),
            }

    @staticmethod
    def run_risk(ticker: str, days: int, realtime: bool = True) -> Dict:
        try:
            data = fetch_risk_data(ticker, days, realtime=realtime)
            config = RiskCalculationConfig()
            calculator = RiskCalculator(config)
            results = calculator.calculate_risk_metrics(data)
            return {
                "ok": True,
                "tool": "risk",
                "data": results.model_dump(),
                "error": None,
            }
        except Exception as e:
            return {
                "ok": False,
                "tool": "risk",
                "data": None,
                "error": str(e),
            }

    @staticmethod
    def run_moving_averages(ticker: str, days: int, realtime: bool = True,
                           fast: int = 50, slow: int = 200) -> Dict:
        try:
            data = fetch_ma_data(ticker, days, realtime=realtime)
            config = MovingAverageConfig(
                ma_type="SMA",
                period=fast,
                secondary_ma_type="SMA",
                secondary_period=slow
            )
            calculator = MovingAverageCalculator(config)
            results = calculator.calculate(data)
            return {
                "ok": True,
                "tool": "moving_averages",
                "data": results.model_dump(),
                "error": None,
            }
        except Exception as e:
            return {
                "ok": False,
                "tool": "moving_averages",
                "data": None,
                "error": str(e),
            }

    @classmethod
    def run_analysis(cls, ticker: str, timeframe: int,
                    tools: List[str]) -> Dict[str, Dict]:
        """Run selected tools and return combined results as envelopes."""
        results: Dict[str, Dict] = {}

        if "momentum" in tools:
            results["momentum"] = cls.run_momentum(ticker, timeframe)
        if "volatility" in tools:
            results["volatility"] = cls.run_volatility(ticker, timeframe)
        if "risk" in tools:
            results["risk"] = cls.run_risk(ticker, timeframe)
        if "moving_averages" in tools:
            results["moving_averages"] = cls.run_moving_averages(ticker, timeframe)

        return results
```

**Checkpoint**: Can run analysis for TSLA and get results

---

### Step 4: Textual UI (1 hour)

#### 4.1 Install Textual
```bash
uv add textual
```

#### 4.2 Portfolio Header Widget
```python
# src/ui/widgets/portfolio_header.py
from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from src.models.dashboard_inputs import PortfolioSnapshotInput

class PortfolioHeader(Widget):
    """Display live portfolio statistics"""

    portfolio = reactive(None)

    def render(self) -> Text:
        if not self.portfolio:
            return Text("📥 Loading portfolio data...", style="dim")

        p: PortfolioSnapshotInput = self.portfolio
        total = f"${p.total_value:,.2f}"
        change = f"${p.day_change:,.2f}"
        change_pct = f"({p.day_change_pct:+.2f}%)"
        timestamp = p.timestamp.strftime("%b %d, %Y %I:%M%p")

        change_color = "green" if p.day_change >= 0 else "red"

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

#### 4.3 Ticker Input Widget
```python
# src/ui/widgets/ticker_input.py
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Button, Checkbox, Static
from textual.message import Message

class TickerInput(Container):
    """Ticker entry and tool selection"""

    class RunAnalysis(Message):
        def __init__(self, ticker: str, timeframe: int, tools: list):
            self.ticker = ticker
            self.timeframe = timeframe
            self.tools = tools
            super().__init__()

    def compose(self):
        yield Static("Quick Analysis", classes="section-title")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Ticker (e.g., TSLA)", id="ticker-input")
            yield Static("Timeframe: 90 days", id="timeframe-label")
            yield Button("Run Analysis", variant="success", id="run-btn")
        with Horizontal(classes="tools-row"):
            yield Checkbox("Momentum", id="tool-momentum", value=True)
            yield Checkbox("Volatility", id="tool-volatility", value=True)
            yield Checkbox("Risk Metrics", id="tool-risk", value=True)
            yield Checkbox("Moving Averages", id="tool-ma", value=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            ticker = self.query_one("#ticker-input", Input).value.strip().upper()
            if not ticker:
                return

            tools = []
            if self.query_one("#tool-momentum", Checkbox).value:
                tools.append("momentum")
            if self.query_one("#tool-volatility", Checkbox).value:
                tools.append("volatility")
            if self.query_one("#tool-risk", Checkbox).value:
                tools.append("risk")
            if self.query_one("#tool-ma", Checkbox).value:
                tools.append("moving_averages")

            if not tools:
                # Surface a clear, inline error instead of running an empty analysis
                if self.app is not None:
                    self.app.notify("Select at least one tool before running analysis.", severity="error")
                return

            self.post_message(self.RunAnalysis(ticker, 90, tools))
```

#### 4.4 Results Panel Widget
```python
# src/ui/widgets/results_panel.py
from textual.containers import VerticalScroll
from textual.widgets import Static
from rich.table import Table
from datetime import datetime

class ResultsPanel(VerticalScroll):
    """Display analysis results"""

    def show_loading(self, ticker: str) -> None:
        self.remove_children()
        self.mount(Static(f"🔄 Running analysis for {ticker}...", classes="loading"))

    def show_error(self, message: str) -> None:
        self.remove_children()
        self.mount(Static(f"❌ Error: {message}", classes="error"))

    def display_results(self, ticker: str, results: dict) -> None:
        self.remove_children()

        timestamp = datetime.now().strftime("%I:%M%p")
        self.mount(Static(f"📊 {ticker} - Real-time Analysis (Updated: {timestamp})", classes="result-header"))

        if not results:
            self.mount(Static("No results to display. Check your tool selection and try again.", classes="error"))
            return

        failed_tools: list[str] = []

        # Momentum
        momentum = results.get("momentum")
        if momentum:
            if momentum.get("ok") and momentum.get("data"):
                self._render_momentum(momentum["data"])
            elif momentum.get("error"):
                failed_tools.append(f"Momentum: {momentum['error']}")

        # Volatility
        volatility = results.get("volatility")
        if volatility:
            if volatility.get("ok") and volatility.get("data"):
                self._render_volatility(volatility["data"])
            elif volatility.get("error"):
                failed_tools.append(f"Volatility: {volatility['error']}")

        # Risk
        risk = results.get("risk")
        if risk:
            if risk.get("ok") and risk.get("data"):
                self._render_risk(risk["data"])
            elif risk.get("error"):
                failed_tools.append(f"Risk: {risk['error']}")

        # Moving Averages
        ma = results.get("moving_averages")
        if ma:
            if ma.get("ok") and ma.get("data"):
                self._render_ma(ma["data"])
            elif ma.get("error"):
                failed_tools.append(f"Moving Averages: {ma['error']}")

        if failed_tools:
            self.mount(Static("Some tools failed:", classes="error"))
            for msg in failed_tools:
                self.mount(Static(f"• {msg}", classes="error"))

    def _render_momentum(self, data: dict) -> None:
        table = Table(title="Momentum", show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        if "rsi" in data:
            rsi = data["rsi"]
            table.add_row("RSI", f"{rsi['current_rsi']:.2f} ({rsi['rsi_signal']})")
        if "macd" in data:
            macd = data["macd"]
            table.add_row("MACD", macd['signal'].capitalize())

        self.mount(Static(table))

    def _render_volatility(self, data: dict) -> None:
        table = Table(title="Volatility", show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        if "atr" in data:
            atr = data["atr"]
            table.add_row("ATR", f"${atr['atr']:.2f} ({atr['atr_percent']:.2f}%)")
        if "volatility_regime" in data:
            table.add_row("Regime", data['volatility_regime'].upper())

        self.mount(Static(table))

    def _render_risk(self, data: dict) -> None:
        table = Table(title="Risk Metrics", show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        if "sharpe_ratio" in data:
            table.add_row("Sharpe Ratio", f"{data['sharpe_ratio']:.2f}")
        if "var_95" in data:
            table.add_row("VaR (95%)", f"{data['var_95']:.2f}%")

        self.mount(Static(table))

    def _render_ma(self, data: dict) -> None:
        table = Table(title="Trend", show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        if "primary_ma" in data:
            ma = data["primary_ma"]
            table.add_row("Price vs MA", ma['price_vs_ma'])

        self.mount(Static(table))
```

#### 4.5 Main App
```python
# src/ui/app.py
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer
from textual.binding import Binding
from src.ui.widgets.portfolio_header import PortfolioHeader
from src.ui.widgets.ticker_input import TickerInput
from src.ui.widgets.results_panel import ResultsPanel
from src.ui.services.portfolio_loader import PortfolioLoader
from src.ui.services.analysis_runner import AnalysisRunner

class FinanceGuruApp(App):
    """Finance Guru™ TUI Dashboard v0.1"""

    TITLE = "Finance Guru™ Dashboard"
    CSS = """
    Screen {
        background: $surface;
    }

    PortfolioHeader {
        height: 3;
        background: $primary;
        padding: 1;
        text-align: center;
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

    .section-title {
        text-style: bold;
        color: $accent;
    }

    .result-header {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }

    .error {
        color: $error;
    }

    .loading {
        color: $warning;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield PortfolioHeader(id="portfolio-header")
            yield TickerInput(id="ticker-input")
            yield ResultsPanel(id="results-panel")
        yield Footer()

    def on_mount(self) -> None:
        """Load portfolio data on startup"""
        try:
            portfolio = PortfolioLoader.load_latest()
            if portfolio:
                self.query_one(PortfolioHeader).portfolio = portfolio
        except Exception as e:
            self.notify(f"Failed to load portfolio: {e}", severity="error")

    def on_ticker_input_run_analysis(self, message: TickerInput.RunAnalysis) -> None:
        """Handle analysis request"""
        results_panel = self.query_one(ResultsPanel)
        results_panel.show_loading(message.ticker)

        try:
            results = AnalysisRunner.run_analysis(
                message.ticker,
                message.timeframe,
                message.tools
            )
            results_panel.display_results(message.ticker, results)
        except Exception as e:
            results_panel.show_error(str(e))

if __name__ == "__main__":
    app = FinanceGuruApp()
    app.run()
```

**Checkpoint**: Dashboard launches and works!

---

### Step 5: CLI Entry Point (15 min)

```python
# src/cli/fin_guru.py
#!/usr/bin/env python3
"""Finance Guru TUI Dashboard Entry Point"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ui.app import FinanceGuruApp

def main():
    app = FinanceGuruApp()
    app.run()

if __name__ == "__main__":
    main()
```

**Add to ~/.zshrc**:
```bash
alias fin-guru='cd /Users/ossieirondi/Documents/Irondi-Household/family-office && uv run python src/cli/fin_guru.py'
```

**Checkpoint**: `fin-guru` launches dashboard!

---

## Testing Plan (v0.1)

### Manual Tests
- [ ] Launch with `fin-guru`
- [ ] Portfolio header shows correct data
- [ ] Enter TSLA, run all 4 tools
- [ ] Results display correctly
- [ ] Try invalid ticker (shows error)
- [ ] Press Q to quit

### Unit Tests (Nice to have)
```python
# tests/test_portfolio_loader.py
from src.ui.services.portfolio_loader import PortfolioLoader
from pathlib import Path

def test_parse_portfolio():
    # Use sample CSV
    csv_path = Path("tests/fixtures/sample_portfolio.csv")
    snapshot = PortfolioLoader.parse_portfolio(csv_path)

    assert snapshot.total_value > 0
    assert len(snapshot.holdings) > 0
    assert snapshot.layer1_value > 0
```

---

## Estimated Timeline

| Task | Time | Status |
|------|------|--------|
| Config + Domain Models | 30 min | Pending |
| Portfolio Loader | 30 min | Pending |
| Analysis Runner | 30 min | Pending |
| Textual UI (all widgets) | 1 hour | Pending |
| CLI Entry Point + Testing | 15 min | Pending |
| **Total** | **2h 45min** | |

---

## What's NOT in v0.1

- ❌ Preset system
- ❌ Multiple screens
- ❌ Parallel execution
- ❌ Auto-refresh
- ❌ Fancy CSS polish
- ❌ Keyboard shortcuts (beyond Q)
- ❌ Layer-specific views
- ❌ Export functionality

**All of the above → v0.2 after you've used v0.1 for 1 week**

---

## Success Metrics

- ✅ Can launch with `fin-guru`
- ✅ Portfolio data loads from latest CSV
- ✅ Can analyze any ticker in < 10 seconds
- ✅ Results are readable and accurate
- ✅ Doesn't crash on invalid input
- ✅ Actually use it daily for 1 week

---

**End of v0.1 Plan**
