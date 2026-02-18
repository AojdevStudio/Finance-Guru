"""Results Panel Widget for Finance Guru™ TUI.

WHAT: Displays analysis results from all tools in scrollable panel
WHY: Provides readable, formatted output for quick decision-making
ARCHITECTURE: Textual VerticalScroll with Rich table rendering

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

from datetime import datetime

from rich.table import Table
from rich.text import Text
from textual.containers import VerticalScroll
from textual.widgets import Static


class ResultsPanel(VerticalScroll):
    """Display analysis results.

    Shows formatted output from momentum, volatility, risk, and MA tools.
    Handles partial failures gracefully.
    """

    def __init__(self, *args, **kwargs):
        """Initialize results panel with welcome message."""
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        """Show welcome message on mount."""
        self.show_welcome()

    def show_welcome(self) -> None:
        """Display welcome message with instructions."""
        welcome = Text.assemble(
            "\n\n",
            ("━" * 80, "dim"),
            "\n",
            ("  Welcome to Finance Guru™ Dashboard  \n\n", "bold cyan"),
            ("━" * 80, "dim"),
            "\n\n",
            ("🚀 Quick Start Guide:\n\n", "bold yellow"),
            ("  1️⃣  ", "bold"),
            (
                "Enter a ticker symbol in the input field above (e.g., TSLA, AAPL, PLTR)\n",
                "",
            ),
            ("  2️⃣  ", "bold"),
            ("Select which analysis tools to run (all 4 are checked by default)\n", ""),
            ("  3️⃣  ", "bold"),
            ("Click the ", ""),
            ("▶ Run Analysis", "bold green"),
            (" button or press ", ""),
            ("Enter\n", ""),
            ("  4️⃣  ", "bold"),
            ("Review the results below - scroll with ", ""),
            ("↑/↓ arrows", "bold cyan"),
            (" or ", ""),
            ("mouse wheel\n", "bold cyan"),
            "\n",
            ("📊 Available Analysis Tools:\n\n", "bold yellow"),
            ("  📈 Momentum     ", "cyan"),
            ("→  RSI, MACD, Stochastic - timing entry/exit points\n", "dim"),
            ("  📊 Volatility   ", "cyan"),
            ("→  ATR, Bollinger Bands - position sizing & risk\n", "dim"),
            ("  ⚠️  Risk Metrics ", "cyan"),
            ("→  Sharpe, VaR, Max Drawdown - portfolio risk\n", "dim"),
            ("  📉 Moving Avg   ", "cyan"),
            ("→  Trend analysis, Golden/Death Cross signals\n", "dim"),
            "\n",
            ("⚡ Pro Tips:\n\n", "bold yellow"),
            ("  • Uncheck tools you don't need for faster analysis\n", "dim"),
            ("  • All data is real-time (90-day lookback period)\n", "dim"),
            ("  • Results include visual signals: ", "dim"),
            ("🟢 Bullish", "green"),
            (" | ", "dim"),
            ("🔴 Bearish", "red"),
            (" | ", "dim"),
            ("🟡 Neutral\n", "yellow"),
            "\n",
            ("⌨️  Keyboard Shortcuts:\n\n", "bold yellow"),
            ("  ", ""),
            ("Tab", "bold cyan"),
            ("      → Navigate between fields\n", "dim"),
            ("  ", ""),
            ("Space", "bold cyan"),
            ("    → Toggle checkboxes\n", "dim"),
            ("  ", ""),
            ("Enter", "bold cyan"),
            ("    → Run analysis\n", "dim"),
            ("  ", ""),
            ("Q", "bold cyan"),
            ("        → Quit dashboard\n", "dim"),
            "\n",
            ("━" * 80, "dim"),
            "\n",
            ("Ready when you are! Type a ticker above to begin.\n", "dim italic"),
        )
        self.mount(Static(welcome))

    def show_loading(self, ticker: str) -> None:
        """Display loading message while analysis runs."""
        self.remove_children()
        self.mount(Static(f"🔄 Running analysis for {ticker}...", classes="loading"))

    def show_error(self, message: str) -> None:
        """Display error message."""
        self.remove_children()
        self.mount(Static(f"❌ Error: {message}", classes="error"))

    def display_results(self, ticker: str, results: dict) -> None:  # noqa: C901
        """Display analysis results from all tools.

        Args:
            ticker: Ticker symbol that was analyzed
            results: Dictionary of tool results (envelopes with ok/data/error)
        """
        self.remove_children()

        timestamp = datetime.now().strftime("%I:%M%p")
        header_text = Text.assemble(
            "\n",
            ("━" * 80, "dim"),
            "\n",
            ("📊 ", "bold"),
            (ticker, "bold cyan"),
            (" - Real-time Analysis", "bold"),
            (f" (Updated: {timestamp})", "dim"),
            "\n",
            ("━" * 80, "dim"),
            "\n",
        )
        self.mount(Static(header_text, classes="result-header"))

        if not results:
            self.mount(
                Static(
                    "No results to display. Check your tool selection and try again.",
                    classes="error",
                )
            )
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
        """Render momentum indicators table."""
        table = Table(
            title="📈 Momentum Indicators", show_header=False, box=None, padding=(0, 2)
        )
        table.add_column("Metric", style="cyan bold", width=20)
        table.add_column("Value", style="yellow")

        if "rsi" in data:
            rsi = data["rsi"]
            signal_emoji = (
                "🟢"
                if rsi.get("rsi_signal") == "bullish"
                else "🔴"
                if rsi.get("rsi_signal") == "bearish"
                else "🟡"
            )
            table.add_row(
                "RSI",
                f"{rsi.get('current_rsi', 0):.2f} {signal_emoji} ({rsi.get('rsi_signal', 'unknown')})",
            )
        if "macd" in data:
            macd = data["macd"]
            signal_emoji = (
                "🟢"
                if macd.get("signal") == "bullish"
                else "🔴"
                if macd.get("signal") == "bearish"
                else "🟡"
            )
            table.add_row(
                "MACD", f"{signal_emoji} {macd.get('signal', 'unknown').capitalize()}"
            )
        if "stochastic" in data:
            stoch = data["stochastic"]
            signal_emoji = (
                "🟢"
                if stoch.get("signal") == "bullish"
                else "🔴"
                if stoch.get("signal") == "bearish"
                else "🟡"
            )
            table.add_row(
                "Stochastic",
                f"K: {stoch.get('k_value', 0):.2f}, D: {stoch.get('d_value', 0):.2f} {signal_emoji}",
            )

        self.mount(Static(table))
        self.mount(Static(""))  # Spacer

    def _render_volatility(self, data: dict) -> None:
        """Render volatility metrics table."""
        table = Table(
            title="📊 Volatility Metrics", show_header=False, box=None, padding=(0, 2)
        )
        table.add_column("Metric", style="cyan bold", width=20)
        table.add_column("Value", style="yellow")

        if "atr" in data:
            atr = data["atr"]
            table.add_row(
                "ATR", f"${atr.get('atr', 0):.2f} ({atr.get('atr_percent', 0):.2f}%)"
            )
        if "volatility_regime" in data:
            regime = data.get("volatility_regime", "unknown").upper()
            regime_emoji = {
                "LOW": "🟢",
                "NORMAL": "🟡",
                "HIGH": "🟠",
                "EXTREME": "🔴",
            }.get(regime, "⚪")
            table.add_row("Regime", f"{regime_emoji} {regime}")
        if "bollinger_bands" in data:
            bb = data["bollinger_bands"]
            table.add_row("Bollinger %B", f"{bb.get('percent_b', 0):.2f}")

        self.mount(Static(table))
        self.mount(Static(""))  # Spacer

    def _render_risk(self, data: dict) -> None:
        """Render risk metrics table."""
        table = Table(
            title="⚠️ Risk Metrics", show_header=False, box=None, padding=(0, 2)
        )
        table.add_column("Metric", style="cyan bold", width=20)
        table.add_column("Value", style="yellow")

        if "sharpe_ratio" in data:
            sharpe = data.get("sharpe_ratio", 0)
            sharpe_emoji = "🟢" if sharpe > 1.0 else "🟡" if sharpe > 0 else "🔴"
            table.add_row("Sharpe Ratio", f"{sharpe_emoji} {sharpe:.2f}")
        if "var_95" in data:
            var = data.get("var_95", 0)
            table.add_row("VaR (95%)", f"{var:.2f}%")
        if "sortino_ratio" in data:
            sortino = data.get("sortino_ratio", 0)
            sortino_emoji = "🟢" if sortino > 1.0 else "🟡" if sortino > 0 else "🔴"
            table.add_row("Sortino Ratio", f"{sortino_emoji} {sortino:.2f}")
        if "max_drawdown" in data:
            dd = data.get("max_drawdown", 0)
            table.add_row("Max Drawdown", f"{dd:.2f}%")

        self.mount(Static(table))
        self.mount(Static(""))  # Spacer

    def _render_ma(self, data: dict) -> None:
        """Render moving average analysis table."""
        table = Table(
            title="📉 Trend Analysis", show_header=False, box=None, padding=(0, 2)
        )
        table.add_column("Metric", style="cyan bold", width=20)
        table.add_column("Value", style="yellow")

        if "primary_ma" in data:
            ma = data["primary_ma"]
            price_vs_ma = ma.get("price_vs_ma", "unknown")
            emoji = (
                "🟢"
                if price_vs_ma == "ABOVE"
                else "🔴"
                if price_vs_ma == "BELOW"
                else "🟡"
            )
            table.add_row("Price vs MA", f"{emoji} {price_vs_ma}")
        if "crossover_analysis" in data and data["crossover_analysis"]:
            crossover = data["crossover_analysis"]
            signal = crossover.get("current_signal", "NEUTRAL")
            signal_emoji = (
                "🟢" if signal == "BULLISH" else "🔴" if signal == "BEARISH" else "🟡"
            )
            table.add_row("Crossover Signal", f"{signal_emoji} {signal}")

        self.mount(Static(table))
        self.mount(Static(""))  # Spacer
