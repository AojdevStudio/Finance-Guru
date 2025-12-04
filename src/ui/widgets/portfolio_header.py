"""
Portfolio Header Widget for Finance Guru™ TUI

WHAT: Displays live portfolio statistics in dashboard header
WHY: Provides at-a-glance portfolio overview from latest CSV
ARCHITECTURE: Textual widget with reactive portfolio property

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from src.models.dashboard_inputs import PortfolioSnapshotInput


class PortfolioHeader(Widget):
    """
    Display live portfolio statistics.
    
    Shows total value, day change, and timestamp from latest CSV snapshot.
    """

    portfolio = reactive(None)

    def render(self) -> Text:
        """
        Render portfolio header with formatted statistics.
        
        Returns:
            Rich Text object with formatted portfolio display
        """
        if not self.portfolio:
            return Text("📥 No portfolio data - upload CSV to notebooks/updates/", style="dim")

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


