"""Finance Guru™ TUI Dashboard Main Application.

WHAT: Main Textual application for Finance Guru dashboard
WHY: Provides single-screen interface for portfolio overview and ticker analysis
ARCHITECTURE: Textual App with custom widgets and event handling

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, Header

from src.ui.services.analysis_runner import AnalysisRunner
from src.ui.services.portfolio_loader import PortfolioLoader
from src.ui.widgets.portfolio_header import PortfolioHeader
from src.ui.widgets.results_panel import ResultsPanel
from src.ui.widgets.ticker_input import TickerInput


class FinanceGuruApp(App):
    """Finance Guru™ TUI Dashboard v0.1.

    Single-screen dashboard with:
    - Portfolio header (from latest CSV)
    - Ticker input and tool selection
    - Results panel (scrollable)
    """

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
        width: 1fr;
        height: auto;
        border: solid $accent;
        padding: 2;
        margin: 1 1;
    }

    .input-row {
        height: auto;
        margin: 1 0;
        width: 100%;
    }

    .tools-row {
        height: auto;
        margin: 1 0;
        width: 100%;
    }

    #ticker-input {
        width: 1fr;
        margin-right: 2;
    }

    #timeframe-label {
        width: auto;
        min-width: 22;
        padding: 0 2;
        content-align: center middle;
    }

    #run-btn {
        width: auto;
        min-width: 22;
        margin-left: 2;
    }

    Checkbox {
        margin-right: 4;
        width: auto;
    }

    .label {
        width: auto;
        min-width: 10;
        color: $text;
        text-style: bold;
        content-align: center middle;
    }

    .separator {
        width: auto;
        min-width: 3;
        color: $text-muted;
    }

    ResultsPanel {
        height: 1fr;
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
    }

    .hint {
        color: $text-muted;
        text-style: italic;
        text-align: center;
        margin: 0 0 1 0;
    }

    .label {
        width: auto;
        color: $text;
        text-style: bold;
        content-align: center middle;
    }

    .separator {
        width: auto;
        color: $text-muted;
    }

    .result-header {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }

    .error {
        color: $error;
        margin: 1 0;
    }

    .loading {
        color: $warning;
        margin: 1 0;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("h", "show_help", "Help", show=True),
        Binding("r", "refresh_portfolio", "Refresh Portfolio", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        with Vertical():
            yield PortfolioHeader(id="portfolio-header")
            yield TickerInput(id="ticker-input")
            yield ResultsPanel(id="results-panel")
        yield Footer()

    def on_mount(self) -> None:
        """Load portfolio data on startup."""
        try:
            portfolio = PortfolioLoader.load_latest()
            if portfolio:
                self.query_one(PortfolioHeader).portfolio = portfolio
            else:
                # Show warning but allow ticker input to proceed
                self.notify(
                    "Portfolio CSV not found - continuing with ticker input only",
                    severity="warning",
                )
        except Exception as e:
            self.notify(f"Failed to load portfolio: {e}", severity="error")

    def action_show_help(self) -> None:
        """Show help/instructions in results panel."""
        results_panel = self.query_one(ResultsPanel)
        results_panel.show_welcome()
        self.notify("📖 Help displayed in results panel", severity="information")

    def action_refresh_portfolio(self) -> None:
        """Refresh portfolio data from latest CSV."""
        try:
            portfolio = PortfolioLoader.load_latest()
            if portfolio:
                self.query_one(PortfolioHeader).portfolio = portfolio
                self.notify(
                    "✅ Portfolio refreshed successfully", severity="information"
                )
            else:
                self.notify("⚠️ No portfolio CSV found", severity="warning")
        except Exception as e:
            self.notify(f"❌ Failed to refresh portfolio: {e}", severity="error")

    def on_ticker_input_run_analysis(self, message: TickerInput.RunAnalysis) -> None:
        """Handle analysis request from ticker input widget."""
        results_panel = self.query_one(ResultsPanel)
        results_panel.show_loading(message.ticker)

        try:
            results = AnalysisRunner.run_analysis(
                message.ticker, message.timeframe, message.tools
            )
            results_panel.display_results(message.ticker, results)
            self.notify(
                f"✅ Analysis complete for {message.ticker}", severity="information"
            )
        except Exception as e:
            results_panel.show_error(str(e))
            self.notify(f"❌ Analysis failed: {str(e)}", severity="error")


if __name__ == "__main__":
    app = FinanceGuruApp()
    app.run()
