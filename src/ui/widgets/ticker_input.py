"""Ticker Input Widget for Finance Guru™ TUI.

WHAT: Ticker entry field and tool selection checkboxes
WHY: Provides quick analysis interface for any ticker
ARCHITECTURE: Textual container with input, checkboxes, and button

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import Button, Checkbox, Input, Static


class TickerInput(Container):
    """Ticker entry and tool selection.

    Provides input field for ticker symbol, checkboxes for tool selection,
    and a button to run analysis.
    """

    class RunAnalysis(Message):
        """Message sent when user requests analysis."""

        def __init__(self, ticker: str, timeframe: int, tools: list):
            self.ticker = ticker
            self.timeframe = timeframe
            self.tools = tools
            super().__init__()

    def compose(self):
        """Compose the widget layout."""
        yield Static("━━━ Quick Analysis ━━━", classes="section-title")
        yield Static(
            "💡 Type a ticker and press Enter or click the button below", classes="hint"
        )
        with Horizontal(classes="input-row"):
            yield Static("Ticker: ", classes="label")
            yield Input(placeholder="Enter ticker (e.g., TSLA)", id="ticker-input")
            yield Static("  |  ", classes="separator")
            yield Static("Timeframe: 90 days", id="timeframe-label")
            yield Static("  ", classes="separator")
            yield Button("▶ Run Analysis", variant="primary", id="run-btn")
        yield Static("")  # Spacer
        yield Static(
            "Select tools to run (Space to toggle, Tab to navigate):", classes="hint"
        )
        with Horizontal(classes="tools-row"):
            yield Checkbox("📈 Momentum", id="tool-momentum", value=True)
            yield Checkbox("📊 Volatility", id="tool-volatility", value=True)
            yield Checkbox("⚠️ Risk Metrics", id="tool-risk", value=True)
            yield Checkbox("📉 Moving Averages", id="tool-ma", value=True)

    def _run_analysis(self) -> None:
        """Execute analysis with current settings."""
        ticker = self.query_one("#ticker-input", Input).value.strip().upper()
        if not ticker:
            if self.app is not None:
                self.app.notify("⚠️ Please enter a ticker symbol", severity="warning")
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
                self.app.notify(
                    "⚠️ Select at least one tool before running analysis.",
                    severity="error",
                )
            return

        self.post_message(self.RunAnalysis(ticker, 90, tools))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press event."""
        if event.button.id == "run-btn":
            self._run_analysis()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in ticker input."""
        if event.input.id == "ticker-input":
            self._run_analysis()
