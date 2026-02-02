# Finance Guru™ TUI Dashboard v0.2 - Enhancement Plan

**Created**: 2025-11-17
**Version**: v0.2 (Power User Edition)
**Estimated Time**: 4 hours
**Philosophy**: Incremental enhancements on v0.1's solid foundation

---

## Problem Statement

**Current State (v0.1)**:
- ✅ Single-command launch working (`fin-guru`)
- ✅ Portfolio header with live data
- ✅ Ticker input + tool selection
- ✅ Real-time analysis execution
- ⚠️ Moving Averages tool broken (method name issue)
- ⚠️ Portfolio day change showing "ERROR"
- 🔄 Sequential execution (slow for 4 tools)
- 🔄 No saved presets (repetitive typing)
- 🔄 Single screen only (can't compare tickers)
- 🔄 No auto-refresh (data goes stale)

**Desired State (v0.2)**:
- ✅ All tools working reliably
- ✅ One-click presets for Layer 1/2/3 analysis
- ✅ Multiple screens (Home, Portfolio)
- ✅ Parallel execution (4x faster)
- ✅ Auto-refresh for live tracking
- ✅ Polished visuals (colors, icons, indicators)

---

## Objectives

### Must Have (v0.2)
1. **Fix Critical Bugs** - All 4 tools working without errors
2. **Preset System** - Quick access to Layer 1/2/3 ticker groups
3. **Multi-Screen Navigation** - Switch between Home and Portfolio
4. **Parallel Execution** - Run tools simultaneously, not sequentially

### Should Have (v0.2)
5. **Auto-Refresh** - Configurable refresh intervals (1min, 5min, 15min)
6. **Visual Polish** - Color-coded metrics, emojis, better spacing

### Nice to Have (Deferred to v0.3)
- ❌ Layer-specific filters
- ❌ Export to PDF/CSV
- ❌ Advanced keyboard shortcuts (vim-style)
- ❌ Correlation matrix view
- ❌ Strategy backtesting integration
- ❌ Advanced auto-refresh for presets / multi-ticker portfolios

---

## Technical Approach

### Architecture Decisions
- **Storage**: YAML config at `~/.config/finance-guru/presets.yaml`
- **Schema**:
```yaml
presets:
  layer1:
    name: "Layer 1 Growth"
    tickers: [PLTR, TSLA, NVDA, AAPL, GOOGL, COIN, MSTR, SOFI]
    tools: [momentum, volatility, risk, moving_averages]
  layer2:
    name: "Layer 2 Income"
    tickers: [JEPI, JEPQ, QQQI, SPYI, QQQY, YMAX, CLM, CRF, BDJ, ETY, ETV, ECAT, UTG, BST]
    tools: [momentum, volatility, risk]
  layer3:
    name: "Layer 3 Hedge"
    tickers: [SQQQ]
    tools: [volatility, risk]
  custom:
    - name: "Tech Leaders"
      tickers: [AAPL, GOOGL, MSFT, NVDA]
      tools: [momentum, risk]
```

- **Pydantic Model**:
```python
# src/models/preset_inputs.py
from pydantic import BaseModel, Field

class PresetInput(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    tickers: list[str] = Field(min_items=1, max_items=20)
    tools: list[str] = Field(min_items=1)

    @field_validator('tickers')
    def validate_tickers(cls, v):
        return [ticker.upper().strip() for ticker in v]

    @field_validator('tools')
    def validate_tools(cls, v):
        valid_tools = {'momentum', 'volatility', 'risk', 'moving_averages'}
        for tool in v:
            if tool not in valid_tools:
                raise ValueError(f"Invalid tool: {tool}")
        return v

class PresetsConfig(BaseModel):
    presets: dict[str, PresetInput | list[PresetInput]]
```

**2. Multi-Screen Navigation**
- **Framework**: Textual's built-in `TabbedContent` widget
- **Screens**:
  - `Home` - Current quick analysis view (existing v0.1)
  - `Portfolio` - All holdings with mini-analysis cards grouped by layer

- **State Management**: Each screen maintains its own reactive state
- **Navigation**: Tab bar at top, keyboard shortcuts (1-2)

**3. Parallel Execution**
- **Framework**: Python `asyncio` with `asyncio.gather()`
- **Approach**: Convert analysis runner methods to async
- **Progress Tracking**: Reactive progress bar (1/4 → 2/4 → 3/4 → 4/4)
- **Error Isolation**: One tool failure doesn't block others

**4. Auto-Refresh**
- **Scope**: Refresh the current analysis automatically using the last-run parameters (ticker, tools, timeframe). For v0.2 this can apply to both single-ticker and preset runs, but refresh frequency should be conservative for large presets.
- **Framework**: Textual's `@work` decorator with an async loop using `asyncio.sleep()`.
- **Configuration**: Toggle on/off and select interval (Off, 1min, 5min, 15min, 30min).
- **Smart Refresh**:
  - Only refresh when the Home tab is active.
  - No overlapping refreshes (exclusive worker).
  - If no prior analysis has been run, refresh is a no-op.
- **Indicator**: "Last updated: HH:MM:SS" label updated after each refresh.

---

## Implementation Plan

### Phase 1: Bug Fixes (v0.1.1) - 30 minutes

**Ship First: Stabilize v0.1**

#### 1.1 Fix Moving Averages Method Name (15 min)

**Problem**: `MovingAverageCalculator` object has no attribute `calculate`

**Root Cause Analysis**:
```python
# Current broken code (src/ui/services/analysis_runner.py:341)
results = calculator.calculate(data)  # ❌ Method doesn't exist
```

**Solution**:
```bash
# Step 1: Check actual method name
uv run python -c "from src.utils.moving_averages import MovingAverageCalculator; import inspect; print([m for m in dir(MovingAverageCalculator) if not m.startswith('_')])"
```

Expected output will show either:
- `calculate_all()`
- `calculate_moving_averages()`
- `get_moving_averages()`

**Fix**:
```python
# src/ui/services/analysis_runner.py (line 341)
# BEFORE
results = calculator.calculate(data)

# AFTER (use correct method name from inspection)
results = calculator.calculate_all(data)  # or whatever the actual method is
```

**Validation**:
```bash
# Test Moving Averages tool standalone
uv run python src/utils/moving_averages_cli.py TSLA --days 90 --ma-type SMA --period 50 --secondary-period 200
```

#### 1.2 Fix Portfolio Day Change Parsing (15 min)

**Problem**: Day change showing "ERROR" instead of numeric value

**Root Cause**: CSV contains non-numeric values in "Today's Gain/Loss Dollar" column

**Solution**:
```python
# src/ui/services/portfolio_loader.py (line 213)
# BEFORE
day_change=row["Today's Gain/Loss Dollar"],

# AFTER - Add safe parsing with fallback
@staticmethod
def safe_parse_float(value, default=0.0) -> float:
    """Parse numeric value, handle ERROR/N/A/empty strings"""
    if pd.isna(value):
        return default
    try:
        # Strip currency symbols, commas, and convert
        clean_value = str(value).replace('$', '').replace(',', '').strip()
        if clean_value.upper() in ['ERROR', 'N/A', '']:
            return default
        return float(clean_value)
    except (ValueError, AttributeError):
        return default

# Update holdings parsing
day_change=PortfolioLoader.safe_parse_float(row.get("Today's Gain/Loss Dollar", 0)),
day_change_pct=PortfolioLoader.safe_parse_float(row.get("Today's Gain/Loss Percent", 0)),
```

**Validation**:
```python
# Test with actual CSV
from src.ui.services.portfolio_loader import PortfolioLoader
portfolio = PortfolioLoader.load_latest()
assert isinstance(portfolio.day_change, float)
print(f"✅ Day change: ${portfolio.day_change:,.2f}")
```

**Checkpoint**: Run `fin-guru`, verify all 4 tools work and day change shows correctly → **Ship v0.1.1**

---

### Phase 2: Preset System - 1 hour

#### 2.1 Create Preset Configuration Module (20 min)

```python
# src/config.py (add to existing file)
from pathlib import Path
import yaml
from src.models.preset_inputs import PresetsConfig, PresetInput

class FinGuruConfig:
    # ... existing config ...

    PRESETS_FILE = CONFIG_DIR / "presets.yaml"

    @classmethod
    def load_presets(cls) -> PresetsConfig:
        """Load preset configuration with defaults"""
        default_presets = {
            "layer1": PresetInput(
                name="Layer 1 Growth",
                tickers=["PLTR", "TSLA", "NVDA", "AAPL", "GOOGL", "COIN", "MSTR", "SOFI"],
                tools=["momentum", "volatility", "risk", "moving_averages"]
            ),
            "layer2": PresetInput(
                name="Layer 2 Income",
                tickers=["JEPI", "JEPQ", "QQQI", "SPYI", "QQQY", "YMAX", "CLM", "CRF",
                        "BDJ", "ETY", "ETV", "ECAT", "UTG", "BST"],
                tools=["momentum", "volatility", "risk"]
            ),
            "layer3": PresetInput(
                name="Layer 3 Hedge",
                tickers=["SQQQ"],
                tools=["volatility", "risk"]
            ),
        }

        if not cls.PRESETS_FILE.exists():
            # Create default presets file
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(cls.PRESETS_FILE, 'w') as f:
                yaml.dump({"presets": {k: v.model_dump() for k, v in default_presets.items()}}, f)
            return PresetsConfig(presets=default_presets)

        try:
            with open(cls.PRESETS_FILE) as f:
                data = yaml.safe_load(f) or {}
            return PresetsConfig(**data)
        except Exception:
            return PresetsConfig(presets=default_presets)

    @classmethod
    def save_preset(cls, key: str, preset: PresetInput):
        """Save a new or updated preset"""
        config = cls.load_presets()
        config.presets[key] = preset

        with open(cls.PRESETS_FILE, 'w') as f:
            yaml.dump({"presets": {k: v.model_dump() for k, v in config.presets.items()}}, f)
```

#### 2.2 Add Preset Selector Widget (25 min)

```python
# src/ui/widgets/preset_selector.py
from textual.containers import Horizontal
from textual.widgets import Select, Button
from textual.message import Message
from src.config import FinGuruConfig

class PresetSelector(Horizontal):
    """Preset selection dropdown for quick analysis"""

    class PresetSelected(Message):
        def __init__(self, preset_key: str, tickers: list[str], tools: list[str]):
            self.preset_key = preset_key
            self.tickers = tickers
            self.tools = tools
            super().__init__()

    def compose(self):
        # Load presets
        config = FinGuruConfig.load_presets()

        # Build dropdown options
        options = [("-- Select Preset --", None)]
        for key, preset in config.presets.items():
            if isinstance(preset, list):
                for i, p in enumerate(preset):
                    options.append((f"{p.name} (Custom {i+1})", f"{key}_{i}"))
            else:
                options.append((preset.name, key))

        yield Select(options, id="preset-select", prompt="Quick Presets")
        yield Button("Load Preset", variant="primary", id="load-preset-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "load-preset-btn":
            select = self.query_one("#preset-select", Select)
            preset_key = select.value

            if not preset_key:
                if self.app:
                    self.app.notify("Select a preset first", severity="warning")
                return

            config = FinGuruConfig.load_presets()
            preset = config.presets.get(preset_key)

            if preset:
                self.post_message(self.PresetSelected(preset_key, preset.tickers, preset.tools))
```

#### 2.3 Integrate Preset into Main App (15 min)

```python
# src/ui/app.py (update)
from src.ui.widgets.preset_selector import PresetSelector

class FinanceGuruApp(App):
    # ... existing code ...

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield PortfolioHeader(id="portfolio-header")
            yield PresetSelector(id="preset-selector")  # NEW
            yield TickerInput(id="ticker-input")
            yield ResultsPanel(id="results-panel")
        yield Footer()

    def on_preset_selector_preset_selected(self, message: PresetSelector.PresetSelected) -> None:
        """Handle preset selection"""
        results_panel = self.query_one(ResultsPanel)

        # Show loading for all tickers
        ticker_list = ", ".join(message.tickers)
        results_panel.show_loading(ticker_list)

        # Run analysis for each ticker (sequentially for now, parallel in Phase 4)
        all_results = {}
        for ticker in message.tickers:
            try:
                results = AnalysisRunner.run_analysis(ticker, 90, message.tools)
                all_results[ticker] = results
            except Exception as e:
                all_results[ticker] = {"error": str(e)}

        # Display combined results
        results_panel.display_preset_results(message.preset_key, all_results)
```

**Checkpoint**: Load Layer 1 preset → See analysis for all 8 tickers

---

### Phase 3: Multi-Screen Navigation - 40 minutes

#### 3.1 Create Portfolio Screen (30 min)

```python
# src/ui/screens/portfolio_screen.py
from textual.containers import VerticalScroll, Grid
from textual.widgets import Static
from rich.table import Table
from src.ui.services.portfolio_loader import PortfolioLoader

class PortfolioScreen(VerticalScroll):
    """Portfolio overview with all holdings"""

    def compose(self):
        yield Static("📊 Portfolio Overview", classes="screen-title")
        yield Grid(id="holdings-grid", classes="holdings-grid")

    def on_mount(self) -> None:
        """Load portfolio data on screen mount"""
        try:
            portfolio = PortfolioLoader.load_latest()
            if portfolio:
                self._render_holdings(portfolio)
        except Exception as e:
            self.mount(Static(f"❌ Error loading portfolio: {e}", classes="error"))

    def _render_holdings(self, portfolio):
        """Render holdings as cards grouped by layer"""
        grid = self.query_one("#holdings-grid", Grid)

        # Group holdings by layer
        layers = {"layer1": [], "layer2": [], "layer3": [], "unknown": []}
        for holding in portfolio.holdings:
            layers[holding.layer].append(holding)

        # Render each layer
        for layer_name, holdings in layers.items():
            if not holdings:
                continue

            layer_display = {
                "layer1": "🚀 Layer 1: Growth",
                "layer2": "💰 Layer 2: Income",
                "layer3": "🛡️ Layer 3: Hedge",
                "unknown": "❓ Unclassified"
            }

            table = Table(title=layer_display[layer_name], show_header=True, box=None)
            table.add_column("Ticker", style="cyan")
            table.add_column("Value", style="yellow")
            table.add_column("Day Δ", style="white")
            table.add_column("% Port", style="dim")

            for h in holdings:
                change_color = "green" if h.day_change >= 0 else "red"
                pct_port = (h.current_value / portfolio.total_value) * 100

                table.add_row(
                    h.symbol,
                    f"${h.current_value:,.2f}",
                    f"[{change_color}]{h.day_change:+.2f} ({h.day_change_pct:+.2f}%)[/]",
                    f"{pct_port:.1f}%"
                )

            grid.mount(Static(table))
```

#### 3.2 Integrate Tabbed Navigation (10 min)

```python
# src/ui/app.py (update)
from textual.widgets import TabbedContent, TabPane
from src.ui.screens.portfolio_screen import PortfolioScreen

class FinanceGuruApp(App):
    # ... existing code ...

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("1", "switch_tab('home')", "Home", show=False),
        Binding("2", "switch_tab('portfolio')", "Portfolio", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield PortfolioHeader(id="portfolio-header")

        with TabbedContent(initial="home"):
            with TabPane("Home", id="home"):
                yield PresetSelector(id="preset-selector")
                yield TickerInput(id="ticker-input")
                yield ResultsPanel(id="results-panel")

            with TabPane("Portfolio", id="portfolio"):
                yield PortfolioScreen()

        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to tab by ID"""
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = tab_id
```

**Checkpoint**: Press `2` → See Portfolio screen with holdings grouped by layer

---

### Phase 4: Parallel Execution - 45 minutes

#### 4.1 Convert Analysis Runner to Async (30 min)

```python
# src/ui/services/analysis_runner.py (refactor)
import asyncio
from typing import Dict, List

class AnalysisRunner:
    """Execute analysis tools via Python imports (async, parallel)"""

    @staticmethod
    async def run_momentum_async(ticker: str, days: int, realtime: bool = True) -> Dict:
        """Async wrapper for momentum analysis"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: AnalysisRunner.run_momentum(ticker, days, realtime)
        )

    @staticmethod
    async def run_volatility_async(ticker: str, days: int, realtime: bool = True) -> Dict:
        """Async wrapper for volatility analysis"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: AnalysisRunner.run_volatility(ticker, days, realtime)
        )

    @staticmethod
    async def run_risk_async(ticker: str, days: int, realtime: bool = True) -> Dict:
        """Async wrapper for risk analysis"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: AnalysisRunner.run_risk(ticker, days, realtime)
        )

    @staticmethod
    async def run_moving_averages_async(ticker: str, days: int, realtime: bool = True,
                                       fast: int = 50, slow: int = 200) -> Dict:
        """Async wrapper for moving averages analysis"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: AnalysisRunner.run_moving_averages(ticker, days, realtime, fast, slow)
        )

    @classmethod
    async def run_analysis_parallel(cls, ticker: str, timeframe: int,
                                    tools: List[str]) -> Dict[str, Dict]:
        """Run selected tools in parallel and return combined results"""
        tasks = []
        tool_map = {}

        if "momentum" in tools:
            tasks.append(cls.run_momentum_async(ticker, timeframe))
            tool_map[len(tasks) - 1] = "momentum"

        if "volatility" in tools:
            tasks.append(cls.run_volatility_async(ticker, timeframe))
            tool_map[len(tasks) - 1] = "volatility"

        if "risk" in tools:
            tasks.append(cls.run_risk_async(ticker, timeframe))
            tool_map[len(tasks) - 1] = "risk"

        if "moving_averages" in tools:
            tasks.append(cls.run_moving_averages_async(ticker, timeframe))
            tool_map[len(tasks) - 1] = "moving_averages"

        # Run all tasks in parallel
        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results back to tool names
        results: Dict[str, Dict] = {}
        for idx, result in enumerate(results_list):
            tool_name = tool_map[idx]
            if isinstance(result, Exception):
                results[tool_name] = {
                    "ok": False,
                    "tool": tool_name,
                    "data": None,
                    "error": str(result)
                }
            else:
                results[tool_name] = result

        return results
```

#### 4.2 Update App to Use Async Execution (15 min)

```python
# src/ui/app.py (update)
import asyncio

class FinanceGuruApp(App):
    # ... existing code ...

    async def on_ticker_input_run_analysis(self, message: TickerInput.RunAnalysis) -> None:
        """Handle analysis request (async, parallel)"""
        results_panel = self.query_one(ResultsPanel)
        results_panel.show_loading(message.ticker)

        try:
            # Run analysis in parallel
            results = await AnalysisRunner.run_analysis_parallel(
                message.ticker,
                message.timeframe,
                message.tools
            )
            results_panel.display_results(message.ticker, results)
        except Exception as e:
            results_panel.show_error(str(e))

    async def on_preset_selector_preset_selected(self, message: PresetSelector.PresetSelected) -> None:
        """Handle preset selection (async, parallel)"""
        results_panel = self.query_one(ResultsPanel)

        ticker_list = ", ".join(message.tickers)
        results_panel.show_loading(ticker_list)

        # Run analysis for all tickers in parallel
        tasks = [
            AnalysisRunner.run_analysis_parallel(ticker, 90, message.tools)
            for ticker in message.tickers
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results back to tickers
        all_results = {}
        for ticker, result in zip(message.tickers, results_list):
            if isinstance(result, Exception):
                all_results[ticker] = {"error": str(result)}
            else:
                all_results[ticker] = result

        results_panel.display_preset_results(message.preset_key, all_results)
```

**Checkpoint**: Run analysis → See 4 tools execute simultaneously (4x faster)

### Phase 5: Auto-Refresh - 30 minutes

#### 5.1 Add Refresh Configuration (10 min)

```python
# src/ui/widgets/refresh_controls.py
from textual.containers import Horizontal
from textual.widgets import Switch, Select, Static

class RefreshControls(Horizontal):
    """Auto-refresh toggle and interval selector"""

    def compose(self):
        yield Static("Auto-refresh:", classes="label")
        yield Switch(id="refresh-toggle", value=False)
        yield Select(
            [
                ("Off", 0),
                ("1 minute", 60),
                ("5 minutes", 300),
                ("15 minutes", 900),
                ("30 minutes", 1800),
            ],
            id="refresh-interval",
            value=0,
            prompt="Interval"
        )
        yield Static("Last updated: Never", id="last-updated")
```
#### 5.2 Implement Auto-Refresh Logic (20 min)

```python
# src/ui/app.py (update)
from datetime import datetime
from textual import work

class FinanceGuruApp(App):
    # ... existing code ...

    refresh_enabled = reactive(False)
    refresh_interval = reactive(0)
    last_refresh = reactive(None)

    def compose(self) -> ComposeResult:
        yield Header()
        yield PortfolioHeader(id="portfolio-header")
        yield RefreshControls(id="refresh-controls")  # NEW

        # ... rest of compose ...

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle refresh toggle"""
        if event.switch.id == "refresh-toggle":
            self.refresh_enabled = event.value
            if event.value:
                self._start_auto_refresh()
            else:
                self._stop_auto_refresh()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle interval selection"""
        if event.select.id == "refresh-interval":
            self.refresh_interval = event.value
            if self.refresh_enabled:
                self._restart_auto_refresh()

    @work(exclusive=True)
    async def _start_auto_refresh(self):
        """Start auto-refresh loop"""
        while self.refresh_enabled and self.refresh_interval > 0:
            await asyncio.sleep(self.refresh_interval)

            # Only refresh if Home tab is active
            tabbed_content = self.query_one(TabbedContent)
            if tabbed_content.active == "home":
                await self._refresh_current_analysis()
                self.last_refresh = datetime.now()

    async def _refresh_current_analysis(self):
        """Re-run current analysis with same parameters"""
        ticker_input = self.query_one("#ticker-input", TickerInput)
        # Re-trigger analysis with current ticker and tools
        # Implementation depends on storing current state

    def _stop_auto_refresh(self):
        """Stop auto-refresh"""
        self.refresh_enabled = False

    def _restart_auto_refresh(self):
        """Restart with new interval"""
        self._stop_auto_refresh()
        self._start_auto_refresh()
```

**Checkpoint**: Enable auto-refresh → See analysis update every N minutes

---

### Phase 5: Auto-Refresh - 30 minutes

#### 5.1 Add Refresh Configuration (10 min)

```python
# src/ui/widgets/refresh_controls.py
from textual.containers import Horizontal
from textual.widgets import Switch, Select, Static

class RefreshControls(Horizontal):
    """Auto-refresh toggle and interval selector"""

    def compose(self):
        yield Static("Auto-refresh:", classes="label")
        yield Switch(id="refresh-toggle", value=False)
        yield Select(
            [
                ("Off", 0),
                ("1 minute", 60),
                ("5 minutes", 300),
                ("15 minutes", 900),
                ("30 minutes", 1800),
            ],
            id="refresh-interval",
            value=0,
            prompt="Interval"
        )
        yield Static("Last updated: Never", id="last-updated")
```

#### 5.2 Implement Auto-Refresh Logic (20 min)

```python
# src/ui/app.py (update)
from datetime import datetime
from textual import work

class FinanceGuruApp(App):
    # ... existing code ...

    refresh_enabled = reactive(False)
    refresh_interval = reactive(0)
    last_refresh = reactive(None)

    def compose(self) -> ComposeResult:
        yield Header()
        yield PortfolioHeader(id="portfolio-header")
        yield RefreshControls(id="refresh-controls")  # NEW

        # ... rest of compose ...

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle refresh toggle"""
        if event.switch.id == "refresh-toggle":
            self.refresh_enabled = event.value
            if event.value:
                self._start_auto_refresh()
            else:
                self._stop_auto_refresh()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle interval selection"""
        if event.select.id == "refresh-interval":
            self.refresh_interval = event.value
            if self.refresh_enabled:
                self._restart_auto_refresh()

    @work(exclusive=True)
    async def _start_auto_refresh(self):
        """Start auto-refresh loop"""
        while self.refresh_enabled and self.refresh_interval > 0:
            await asyncio.sleep(self.refresh_interval)

            # Only refresh if Home tab is active
            tabbed_content = self.query_one(TabbedContent)
            if tabbed_content.active == "home":
                await self._refresh_current_analysis()
                self.last_refresh = datetime.now()

    async def _refresh_current_analysis(self):
        """Re-run current analysis with same parameters"""
        ticker_input = self.query_one("#ticker-input", TickerInput)
        # Re-trigger analysis with current ticker and tools
        # Implementation depends on storing current state

    def _stop_auto_refresh(self):
        """Stop auto-refresh"""
        self.refresh_enabled = False

    def _restart_auto_refresh(self):
        """Restart with new interval"""
        self._stop_auto_refresh()
        self._start_auto_refresh()
```

**Checkpoint**: Enable auto-refresh → See analysis update every N minutes

---

### Phase 6: Visual Polish - 45 minutes

#### 6.1 Enhanced CSS Styling (20 min)

```python
# src/ui/app.py (update CSS)
class FinanceGuruApp(App):
    CSS = """
    /* Base Theme */
    Screen {
        background: $surface;
    }

    /* Portfolio Header */
    PortfolioHeader {
        height: 3;
        background: $primary;
        padding: 1;
        text-align: center;
        border: heavy $accent;
    }

    /* Preset Selector */
    PresetSelector {
        height: 4;
        padding: 1;
        border: solid $secondary;
        margin-bottom: 1;
    }

    /* Ticker Input */
    TickerInput {
        height: 8;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }

    /* Results Panel */
    ResultsPanel {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    /* Refresh Controls */
    RefreshControls {
        height: 3;
        padding: 1;
        background: $panel;
        border: solid $secondary;
    }

    /* Section Titles */
    .screen-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin: 1 0;
        padding: 1;
        background: $primary;
        border: heavy $accent;
    }

    .section-title {
        text-style: bold;
        color: $accent;
    }

    /* Result States */
    .result-header {
        text-style: bold;
        color: $accent;
        margin: 1 0;
        padding: 0 1;
        background: $panel;
    }

    .error {
        color: $error;
        text-style: bold;
    }

    .loading {
        color: $warning;
        text-style: italic;
    }

    .success {
        color: $success;
        text-style: bold;
    }

    /* Portfolio Grid */
    .holdings-grid {
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
    }

    /* Tool Checkboxes */
    .tools-row {
        padding: 1 0;
    }

    /* Buttons */
    Button {
        margin: 0 1;
    }
    """
```

#### 6.2 Add Emojis and Color-Coded Metrics (15 min)

```python
# src/ui/widgets/ticker_input.py (update)
class TickerInput(Container):
    def compose(self):
        yield Static("⚡ Quick Analysis", classes="section-title")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Ticker (e.g., TSLA)", id="ticker-input")
            yield Static("📅 Timeframe: 90 days", id="timeframe-label")
            yield Button("▶ Run Analysis", variant="success", id="run-btn")
        with Horizontal(classes="tools-row"):
            yield Checkbox("📊 Momentum", id="tool-momentum", value=True)
            yield Checkbox("📈 Volatility", id="tool-volatility", value=True)
            yield Checkbox("⚠️ Risk Metrics", id="tool-risk", value=True)
            yield Checkbox("📉 Moving Averages", id="tool-ma", value=True)
```

```python
# src/ui/widgets/results_panel.py (update)
class ResultsPanel(VerticalScroll):
    def _render_momentum(self, data: dict) -> None:
        table = Table(title="📊 Momentum Indicators", show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        if "rsi" in data:
            rsi = data["rsi"]
            signal = rsi['rsi_signal'].upper()

            # Color-code RSI signal
            signal_color = {
                "OVERSOLD": "green",
                "OVERBOUGHT": "red",
                "NEUTRAL": "yellow"
            }.get(signal, "white")

            table.add_row(
                "RSI (14)",
                f"{rsi['current_rsi']:.2f} [{signal_color}]({signal})[/]"
            )

        if "macd" in data:
            macd = data["macd"]
            signal = macd['signal'].upper()

            signal_emoji = {
                "BULLISH": "🟢",
                "BEARISH": "🔴",
                "NEUTRAL": "🟡"
            }.get(signal, "⚪")

            table.add_row(
                "MACD Signal",
                f"{signal_emoji} {signal}"
            )

        self.mount(Static(table))
```

#### 6.3 Add Layer Badges to Portfolio Header (10 min)

```python
# src/ui/widgets/portfolio_header.py (update)
class PortfolioHeader(Widget):
    def render(self) -> Text:
        if not self.portfolio:
            return Text("📥 Loading portfolio data...", style="dim")

        p: PortfolioSnapshotInput = self.portfolio

        # Main portfolio stats
        total = f"${p.total_value:,.2f}"
        change = f"${p.day_change:,.2f}"
        change_pct = f"({p.day_change_pct:+.2f}%)"
        timestamp = p.timestamp.strftime("%b %d, %Y %I:%M%p")
        change_color = "green" if p.day_change >= 0 else "red"

        # Layer breakdown
        l1_pct = (p.layer1_value / p.total_value * 100) if p.total_value else 0
        l2_pct = (p.layer2_value / p.total_value * 100) if p.total_value else 0
        l3_pct = (p.layer3_value / p.total_value * 100) if p.total_value else 0

        return Text.assemble(
            ("💼 Portfolio: ", "bold"),
            (total, "bold cyan"),
            " | Day: ",
            (change, change_color),
            " ",
            (change_pct, change_color),
            " | ",
            ("🚀 L1: ", "bold"),
            (f"{l1_pct:.1f}%", "green"),
            " ",
            ("💰 L2: ", "bold"),
            (f"{l2_pct:.1f}%", "yellow"),
            " ",
            ("🛡️ L3: ", "bold"),
            (f"{l3_pct:.1f}%", "blue"),
            " | ",
            (f"📅 {timestamp}", "dim"),
        )
```

**Checkpoint**: Dashboard looks polished with colors, emojis, and clear visual hierarchy

---

## Testing Strategy

### Unit Tests

```python
# tests/test_preset_config.py
from src.config import FinGuruConfig
from src.models.preset_inputs import PresetInput

def test_load_default_presets():
    config = FinGuruConfig.load_presets()
    assert "layer1" in config.presets
    assert isinstance(config.presets["layer1"], PresetInput)
    assert len(config.presets["layer1"].tickers) > 0

def test_save_custom_preset():
    preset = PresetInput(
        name="Test Preset",
        tickers=["AAPL", "GOOGL"],
        tools=["momentum", "risk"]
    )
    FinGuruConfig.save_preset("test", preset)

    # Reload and verify
    config = FinGuruConfig.load_presets()
    assert "test" in config.presets
    assert config.presets["test"].name == "Test Preset"
```

```python
# tests/test_parallel_execution.py
import asyncio
from src.ui.services.analysis_runner import AnalysisRunner

async def test_parallel_execution_speed():
    import time

    # Measure sequential execution
    start = time.time()
    results_seq = AnalysisRunner.run_analysis("TSLA", 90, ["momentum", "volatility", "risk", "moving_averages"])
    seq_time = time.time() - start

    # Measure parallel execution
    start = time.time()
    results_par = await AnalysisRunner.run_analysis_parallel("TSLA", 90, ["momentum", "volatility", "risk", "moving_averages"])
    par_time = time.time() - start

    # Parallel should be significantly faster
    assert par_time < seq_time * 0.5  # At least 2x speedup

    # Results should be equivalent
    assert set(results_seq.keys()) == set(results_par.keys())
```

### Manual Testing Checklist

**v0.1.1 (Bug Fixes)**
- [ ] Launch `fin-guru`
- [ ] Verify Moving Averages tool works for TSLA
- [ ] Verify portfolio day change shows numeric value (not ERROR)
- [ ] All 4 tools execute without errors

**v0.2 (Presets)**
- [ ] Load Layer 1 preset → See 8 tickers analyzed
- [ ] Load Layer 2 preset → See 14 tickers analyzed
- [ ] Create custom preset → Save and reload
- [ ] Verify preset YAML file created at `~/.config/finance-guru/presets.yaml`

**v0.2 (Multi-Screen)**
- [ ] Press `2` → Switch to Portfolio screen
- [ ] Verify all holdings grouped by layer (L1/L2/L3)
- [ ] Press `1` → Return to Home screen

**v0.2 (Parallel Execution)**
- [ ] Run all 4 tools on TSLA
- [ ] Verify execution time < 3 seconds (vs ~8-10 seconds sequential)
- [ ] Check that one tool failure doesn't block others

**v0.2 (Auto-Refresh)**
- [ ] Enable auto-refresh with 1-minute interval
- [ ] Wait 1 minute → Verify analysis re-runs automatically
- [ ] Switch to Portfolio tab → Verify refresh pauses
- [ ] Return to Home tab → Verify refresh resumes
- [ ] Disable auto-refresh → Verify refresh stops

**v0.2 (Auto-Refresh)**
- [ ] Enable auto-refresh with 1-minute interval
- [ ] Wait 1 minute → Verify analysis re-runs automatically
- [ ] Switch to Portfolio tab → Verify refresh pauses
- [ ] Return to Home tab → Verify refresh resumes
- [ ] Disable auto-refresh → Verify refresh stops

**v0.2 (Visual Polish)**
- [ ] Verify emojis appear on tool names
- [ ] Check RSI signal color-coding (green=oversold, red=overbought)
- [ ] Verify MACD signal emojis (🟢 bullish, 🔴 bearish)
- [ ] Check layer badges in portfolio header (L1/L2/L3 percentages)

---

## Potential Challenges & Solutions

### Challenge 1: Async/Await Complexity
**Problem**: Textual event handlers need to be async for parallel execution
**Solution**:
- Use `@work` decorator for background tasks
- Ensure all analysis methods have async wrappers
- Use `asyncio.gather()` for parallel execution with error handling

### Challenge 2: State Management Across Screens
**Problem**: Each screen needs access to portfolio data
**Solution**:
- Use Textual's reactive state for shared data
- Load portfolio data once at app mount, share via app.portfolio reactive variable
- Each screen accesses via `self.app.portfolio`

### Challenge 3: YAML Config File Corruption
**Problem**: User manually edits YAML and breaks format
**Solution**:
- Always validate with Pydantic models
- Fallback to defaults on parse errors
- Log warnings but don't crash

### Challenge 4: Auto-Refresh Performance
**Problem**: Refreshing 14 Layer 2 tickers every minute could be slow  
**Solution**:
- Only refresh visible screen
- Use parallel execution for preset refreshes
- Add "Pause refresh" button for manual control

### Challenge 5: Portfolio CSV Schema Changes
**Problem**: Fidelity changes CSV column names
**Solution**:
- Schema validation with clear error messages
- Flexible column matching (case-insensitive, fuzzy match)
- Document expected CSV format for user troubleshooting

---

## Success Criteria

### v0.1.1 (Bug Fixes)
- ✅ Moving Averages tool works without errors
- ✅ Portfolio day change parses correctly
- ✅ All 4 tools execute successfully on test tickers (TSLA, PLTR, JEPI)

### v0.2 (Full Release)
- ✅ Preset system allows one-click analysis of Layer 1/2/3
- ✅ Multiple screens (Home, Portfolio) with tab navigation
- ✅ Parallel execution achieves 2x+ speedup over sequential
- ✅ Auto-refresh works reliably without blocking UI
- ✅ Visual polish: emojis, colors, clear hierarchy
- ✅ Daily usage for 1 week without crashes or major bugs

---

## Implementation Timeline

| Phase | Tasks | Time | Completion |
|-------|-------|------|------------|
| **Phase 1: Bug Fixes (v0.1.1)** | Moving Averages fix, day change parsing | 30 min | ⬜ |
| **Phase 2: Preset System** | Config module, preset selector, integration | 1 hour | ⬜ |
| **Phase 3: Multi-Screen** | Portfolio screen, tabbed navigation | 40 min | ⬜ |
| **Phase 4: Parallel Execution** | Async wrappers, parallel analysis runner | 45 min | ⬜ |
| **Phase 5: Auto-Refresh** | Refresh controls, interval logic | 30 min | ⬜ |
| **Phase 6: Visual Polish** | CSS updates, emojis, color-coding | 45 min | ⬜ |
| **Testing & Validation** | Manual tests, bug fixes, polish | 30 min | ⬜ |
| **Total** | | **4h 10min** | |

---

## Deferred to Future Versions

### v0.3 (Advanced Features)
- Advanced auto-refresh and scheduling (smarter presets handling, richer controls)
- Layer-specific filtering (show only L1, L2, or L3)
- Export results to PDF/CSV
- Correlation matrix heatmap view
- Strategy backtesting integration
- Price alerts and notifications

### v0.4 (Professional Edition)
- Historical analysis comparison (today vs. 30 days ago)
- Custom indicator builder
- Multi-portfolio support (track multiple accounts)
- API integration for broker data (beyond CSV)
- Mobile-responsive TUI layout

---

## End of v0.2 Enhancement Plan

**Status**: Ready for implementation
**Next Action**: Ship v0.1.1 bug fixes, then proceed with v0.2 phases sequentially

**Key Principle**: Ship iteratively. Each phase can be tested independently before moving to the next.
