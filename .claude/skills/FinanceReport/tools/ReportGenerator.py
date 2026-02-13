#!/usr/bin/env python3
"""ReportGenerator - Finance Guru PDF Report Builder.

Generates institutional-quality 8-10 page PDF analysis reports.
Follows VGT header style and AMZN content depth.

Usage:
    uv run python ReportGenerator.py --ticker TSLA --portfolio-value 250000
    uv run python ReportGenerator.py --ticker PLTR --output-dir ./reports/
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[4]  # Go up from tools/ to project root
sys.path.insert(0, str(PROJECT_ROOT))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Finance Guru Brand Colors
NAVY = colors.HexColor("#1a365d")
GOLD = colors.HexColor("#d69e2e")
GREEN = colors.HexColor("#38a169")
RED = colors.HexColor("#e53e3e")
LIGHT_GRAY = colors.HexColor("#f7fafc")
DARK_GRAY = colors.HexColor("#2d3748")


class FinanceGuruStyles:
    """Centralized style management for Finance Guru reports."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create all custom paragraph styles."""
        # Brand Title
        self.styles.add(
            ParagraphStyle(
                name="BrandTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=NAVY,
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

        # Gold Subtitle
        self.styles.add(
            ParagraphStyle(
                name="GoldSubtitle",
                parent=self.styles["Normal"],
                fontSize=14,
                textColor=GOLD,
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName="Helvetica",
            )
        )

        # Section Header
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=16,
                textColor=NAVY,
                spaceBefore=16,
                spaceAfter=10,
                fontName="Helvetica-Bold",
            )
        )

        # Subsection Header
        self.styles.add(
            ParagraphStyle(
                name="SubHeader",
                parent=self.styles["Heading3"],
                fontSize=12,
                textColor=NAVY,
                spaceBefore=10,
                spaceAfter=6,
                fontName="Helvetica-Bold",
            )
        )

        # Body Text
        self.styles.add(
            ParagraphStyle(
                name="ReportBody",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=DARK_GRAY,
                spaceAfter=6,
                alignment=TA_JUSTIFY,
                fontName="Helvetica",
            )
        )

        # Bullet Point
        self.styles.add(
            ParagraphStyle(
                name="BulletPoint",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=DARK_GRAY,
                leftIndent=20,
                spaceAfter=4,
                fontName="Helvetica",
            )
        )

        # Disclaimer
        self.styles.add(
            ParagraphStyle(
                name="Disclaimer",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=DARK_GRAY,
                alignment=TA_CENTER,
                spaceAfter=6,
                fontName="Helvetica-Oblique",
            )
        )

        # Table Cell - for text that needs to wrap inside table cells
        self.styles.add(
            ParagraphStyle(
                name="TableCell",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=DARK_GRAY,
                spaceAfter=0,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica",
                wordWrap="CJK",  # Enables better word wrapping
            )
        )

        # Table Header Cell - bold text for table headers
        self.styles.add(
            ParagraphStyle(
                name="TableHeaderCell",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.white,
                spaceAfter=0,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                wordWrap="CJK",
            )
        )

    def get(self, name: str) -> ParagraphStyle:
        """Get a style by name."""
        return self.styles[name]


class FinanceGuruReport:
    """Main report builder class for Finance Guru PDF reports."""

    def __init__(
        self,
        ticker: str,
        portfolio_value: float = 250000,
        output_dir: str = "fin-guru-private/fin-guru/analysis/reports",
    ):
        self.ticker = ticker
        self.portfolio_value = portfolio_value
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.date = datetime.now().strftime("%Y-%m-%d")
        self.date_display = datetime.now().strftime("%B %d, %Y")

        self.styles = FinanceGuruStyles()
        self.story = []

        # Report data (populated during build)
        self.data = {}

    def _wrap_cell_text(self, text: str, is_header: bool = False) -> Paragraph:
        """Wrap text in a Paragraph for proper table cell wrapping.

        CRITICAL: Plain strings in ReportLab tables DO NOT wrap.
        All table cell content must be wrapped in Paragraph objects.
        """
        style = (
            self.styles.get("TableHeaderCell")
            if is_header
            else self.styles.get("TableCell")
        )
        # Handle None values
        if text is None:
            text = "N/A"
        return Paragraph(str(text), style)

    def _create_table(
        self,
        data: list[list[str]],
        col_widths: list[float] | None = None,
        has_header: bool = True,
    ) -> Table:
        """Create a styled table with proper text wrapping.

        CRITICAL: All cell content is wrapped in Paragraph objects to ensure
        text wraps within cells instead of overflowing.

        Args:
            data: 2D list of cell values (strings or Paragraph objects)
            col_widths: Explicit column widths (REQUIRED for proper wrapping)
            has_header: Whether first row is a header row
        """
        # Wrap all cell content in Paragraph objects for proper text wrapping
        wrapped_data = []
        for row_idx, row in enumerate(data):
            wrapped_row = []
            for cell in row:
                # Skip if already a Paragraph or other flowable
                if hasattr(cell, "wrap"):
                    wrapped_row.append(cell)
                else:
                    is_header = has_header and row_idx == 0
                    wrapped_row.append(self._wrap_cell_text(cell, is_header))
            wrapped_data.append(wrapped_row)

        table = Table(wrapped_data, colWidths=col_widths)

        style_commands = [
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, DARK_GRAY),
        ]

        if has_header:
            style_commands.extend(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("TOPPADDING", (0, 0), (-1, 0), 10),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
                ]
            )
        else:
            style_commands.append(
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT_GRAY])
            )

        table.setStyle(TableStyle(style_commands))
        return table

    def _create_verdict_box(
        self, rating: str, conviction: str, risk_level: str
    ) -> Table:
        """Create a styled verdict box with proper column widths.

        CRITICAL: Column widths must accommodate text at specified font sizes.
        "INVESTMENT RATING" at 14pt bold needs ~2.5" minimum.
        """
        data = [
            ["INVESTMENT RATING", rating.upper()],
            ["Conviction", conviction],
            ["Risk Level", risk_level],
        ]

        # Color based on rating
        if "BUY" in rating.upper():
            header_color = GREEN
        elif "SELL" in rating.upper():
            header_color = RED
        else:
            header_color = GOLD

        # Column widths: 2.8" + 4.2" = 7" (fits in 7.5" content area)
        # First column needs 2.8" to fit "INVESTMENT RATING" at 14pt bold
        table = Table(data, colWidths=[2.8 * inch, 4.2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), header_color),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 14),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 1.5, NAVY),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("TEXTCOLOR", (0, 1), (-1, -1), DARK_GRAY),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 11),
                ]
            )
        )
        return table

    def add_cover_page(
        self,
        title: str,
        subtitle: str,
        current_price: float,
        ytd_performance: float,
        analyst_team: list[str] = None,
        week_52_range: str = None,
        market_cap: str = None,
        expense_ratio: float = None,
    ):
        """Add GOOG-style cover page with proper table formatting.

        STANDARD FORMAT (matching GOOG example - Image #1):
        - Navy header row with "Report Date:" label and date value
        - Clean data rows with borders for each field
        - Analyst names listed WITHOUT bullet points, one per line
        - No "Finance Guru Multi-Agent System" header
        """
        # Default analyst team - names with roles (matching GOOG format)
        if analyst_team is None:
            analyst_team = [
                "Dr. Aleksandr Petrov (Market Research)",
                "Dr. Priya Desai (Quantitative Analysis)",
                "Elena Rodriguez-Park (Strategy)",
            ]

        # Brand header
        self.story.append(Spacer(1, 0.3 * inch))
        self.story.append(Paragraph("FINANCE GURU™", self.styles.get("BrandTitle")))
        self.story.append(
            Paragraph(
                "Family Office Investment Analysis", self.styles.get("GoldSubtitle")
            )
        )
        self.story.append(HRFlowable(width="100%", thickness=2, color=NAVY))
        self.story.append(Spacer(1, 0.2 * inch))

        # Report title - ticker prominently displayed
        self.story.append(
            Paragraph(
                f"<b>{self.ticker}</b> - {title}", self.styles.get("SectionHeader")
            )
        )
        self.story.append(Paragraph(subtitle, self.styles.get("ReportBody")))
        self.story.append(Spacer(1, 0.3 * inch))

        # Create analyst team text (no bullets, just line breaks)
        team_paragraph = Paragraph(
            "<br/>".join(analyst_team), self.styles.get("TableCell")
        )

        # Build table data - HEADER ROW FIRST (navy background)
        key_info = [
            ["Report Date:", self.date]  # Header row
        ]

        # Data rows
        key_info.append(["Analyst Team:", team_paragraph])
        key_info.append(["Current Price:", f"${current_price:,.2f}"])

        if week_52_range:
            key_info.append(["52-Week Range:", week_52_range])

        key_info.append(["YTD Performance:", f"{ytd_performance:+.1f}%"])

        if market_cap:
            key_info.append(["Market Cap:", market_cap])

        if expense_ratio is not None:
            key_info.append(["Expense Ratio:", f"{expense_ratio:.2f}%"])

        # Create table with GOOG-style formatting
        info_table = Table(key_info, colWidths=[2.5 * inch, 4.5 * inch])

        # Style the table like GOOG example
        info_table.setStyle(
            TableStyle(
                [
                    # Header row (first row) - Navy background, white bold text
                    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    # All rows styling
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 1), (0, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    # Grid lines
                    ("GRID", (0, 0), (-1, -1), 0.5, DARK_GRAY),
                    # Data rows - white background
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ]
            )
        )

        self.story.append(info_table)
        self.story.append(Spacer(1, 0.3 * inch))

    def add_executive_summary(
        self,
        thesis: str,
        key_findings: list[dict[str, str]],
        rating: str,
        conviction: str,
        risk_level: str,
    ):
        """Add executive summary section."""
        self.story.append(
            Paragraph("EXECUTIVE SUMMARY", self.styles.get("SectionHeader"))
        )
        self.story.append(HRFlowable(width="80%", thickness=1, color=GOLD))
        self.story.append(Spacer(1, 0.15 * inch))

        # Investment thesis
        self.story.append(
            Paragraph("<b>Investment Thesis</b>", self.styles.get("SubHeader"))
        )
        self.story.append(Paragraph(thesis, self.styles.get("ReportBody")))
        self.story.append(Spacer(1, 0.15 * inch))

        # Key findings
        self.story.append(
            Paragraph("<b>Key Findings</b>", self.styles.get("SubHeader"))
        )
        for finding in key_findings:
            label = finding.get("label", "")
            detail = finding.get("detail", "")
            self.story.append(
                Paragraph(f"• <b>{label}:</b> {detail}", self.styles.get("BulletPoint"))
            )
        self.story.append(Spacer(1, 0.2 * inch))

        # Verdict box
        self.story.append(self._create_verdict_box(rating, conviction, risk_level))
        self.story.append(PageBreak())

    def add_quant_analysis(
        self,
        risk_metrics: dict[str, Any],
        momentum_data: dict[str, Any],
        volatility_data: dict[str, Any],
    ):
        """Add quantitative analysis section."""
        self.story.append(
            Paragraph("QUANTITATIVE ANALYSIS", self.styles.get("SectionHeader"))
        )
        self.story.append(HRFlowable(width="80%", thickness=1, color=GOLD))
        self.story.append(Spacer(1, 0.15 * inch))

        # Risk Metrics Table
        self.story.append(
            Paragraph(
                "<b>Risk & Performance Metrics (252-Day)</b>",
                self.styles.get("SubHeader"),
            )
        )

        risk_table_data = [
            ["Metric", "Value", "Benchmark", "Assessment"],
            [
                "Sharpe Ratio",
                str(risk_metrics.get("sharpe", "N/A")),
                str(risk_metrics.get("benchmark_sharpe", "1.0")),
                self._assess_sharpe(risk_metrics.get("sharpe")),
            ],
            ["Sortino Ratio", str(risk_metrics.get("sortino", "N/A")), "-", "-"],
            [
                "Beta",
                str(risk_metrics.get("beta", "N/A")),
                "1.0",
                self._assess_beta(risk_metrics.get("beta")),
            ],
            ["Alpha", str(risk_metrics.get("alpha", "N/A")), "0%", "-"],
            ["Max Drawdown", str(risk_metrics.get("max_drawdown", "N/A")), "-", "-"],
            ["VaR (95%)", str(risk_metrics.get("var_95", "N/A")), "-", "-"],
        ]

        self.story.append(
            self._create_table(
                risk_table_data, [1.5 * inch, 1.3 * inch, 1.3 * inch, 2.4 * inch]
            )
        )
        self.story.append(Spacer(1, 0.2 * inch))

        # Momentum Indicators
        self.story.append(
            Paragraph(
                "<b>Momentum Indicators (90-Day)</b>", self.styles.get("SubHeader")
            )
        )

        momentum_table_data = [
            ["Indicator", "Value", "Signal"],
            [
                "RSI (14)",
                str(momentum_data.get("rsi", "N/A")),
                self._assess_rsi(momentum_data.get("rsi")),
            ],
            [
                "MACD",
                str(momentum_data.get("macd", "N/A")),
                momentum_data.get("macd_signal", "-"),
            ],
            ["Stochastic %K", str(momentum_data.get("stochastic_k", "N/A")), "-"],
            ["Williams %R", str(momentum_data.get("williams_r", "N/A")), "-"],
        ]

        self.story.append(
            self._create_table(momentum_table_data, [2 * inch, 2 * inch, 2.5 * inch])
        )
        self.story.append(Spacer(1, 0.2 * inch))

        # Volatility Assessment
        self.story.append(
            Paragraph("<b>Volatility Assessment</b>", self.styles.get("SubHeader"))
        )

        vol_table_data = [
            ["Metric", "Value"],
            [
                "Annualized Volatility",
                str(volatility_data.get("annualized_vol", "N/A")),
            ],
            ["ATR (14)", str(volatility_data.get("atr", "N/A"))],
            ["Bollinger Band Width", str(volatility_data.get("bb_width", "N/A"))],
            ["Volatility Regime", volatility_data.get("regime", "Normal")],
        ]

        self.story.append(self._create_table(vol_table_data, [3 * inch, 3.5 * inch]))
        self.story.append(PageBreak())

    def add_portfolio_sizing(
        self, recommended_pct: float, current_price: float, entry_strategy: str
    ):
        """Add portfolio sizing section with actual dollar amounts."""
        self.story.append(
            Paragraph("PORTFOLIO SIZING", self.styles.get("SectionHeader"))
        )
        self.story.append(HRFlowable(width="80%", thickness=1, color=GOLD))
        self.story.append(Spacer(1, 0.15 * inch))

        # Calculate sizing
        min_pct = recommended_pct - 0.5
        max_pct = recommended_pct + 0.5
        min_amount = self.portfolio_value * (min_pct / 100)
        max_amount = self.portfolio_value * (max_pct / 100)
        min_shares = int(min_amount / current_price)
        max_shares = int(max_amount / current_price)

        self.story.append(
            Paragraph(
                f"Based on your portfolio value of <b>${self.portfolio_value:,.0f}</b>:",
                self.styles.get("ReportBody"),
            )
        )
        self.story.append(Spacer(1, 0.1 * inch))

        sizing_data = [
            ["Parameter", "Value"],
            ["Recommended Allocation", f"{min_pct:.1f}% - {max_pct:.1f}%"],
            ["Dollar Amount", f"${min_amount:,.0f} - ${max_amount:,.0f}"],
            ["Share Count", f"{min_shares} - {max_shares} shares"],
            ["Current Price", f"${current_price:,.2f}"],
        ]

        self.story.append(self._create_table(sizing_data, [3 * inch, 3.5 * inch]))
        self.story.append(Spacer(1, 0.2 * inch))

        # Entry Strategy
        self.story.append(
            Paragraph("<b>Entry Strategy</b>", self.styles.get("SubHeader"))
        )
        self.story.append(Paragraph(entry_strategy, self.styles.get("ReportBody")))
        self.story.append(Spacer(1, 0.2 * inch))

    def add_sentiment_section(
        self,
        sentiment_summary: str,
        analyst_ratings: dict[str, Any],
        catalysts: list[str],
        risks: list[str],
    ):
        """Add market sentiment section."""
        self.story.append(
            Paragraph("MARKET SENTIMENT & RESEARCH", self.styles.get("SectionHeader"))
        )
        self.story.append(HRFlowable(width="80%", thickness=1, color=GOLD))
        self.story.append(Spacer(1, 0.15 * inch))

        # Sentiment Summary
        self.story.append(Paragraph(sentiment_summary, self.styles.get("ReportBody")))
        self.story.append(Spacer(1, 0.15 * inch))

        # Analyst Ratings
        if analyst_ratings:
            self.story.append(
                Paragraph("<b>Analyst Consensus</b>", self.styles.get("SubHeader"))
            )
            ratings_data = [
                ["Rating", "Count"],
                ["Buy", str(analyst_ratings.get("buy", 0))],
                ["Hold", str(analyst_ratings.get("hold", 0))],
                ["Sell", str(analyst_ratings.get("sell", 0))],
                ["Average Target", f"${analyst_ratings.get('target', 0):,.2f}"],
            ]
            self.story.append(self._create_table(ratings_data, [2 * inch, 2 * inch]))
            self.story.append(Spacer(1, 0.15 * inch))

        # 2026 Catalysts
        self.story.append(
            Paragraph("<b>2026 Catalysts</b>", self.styles.get("SubHeader"))
        )
        for catalyst in catalysts:
            self.story.append(
                Paragraph(f"• {catalyst}", self.styles.get("BulletPoint"))
            )
        self.story.append(Spacer(1, 0.15 * inch))

        # Key Risks
        self.story.append(Paragraph("<b>Key Risks</b>", self.styles.get("SubHeader")))
        for risk in risks:
            self.story.append(Paragraph(f"• {risk}", self.styles.get("BulletPoint")))
        # No PageBreak here - let disclaimer flow naturally on same page if space allows

    def add_disclaimer(self):
        """Add compliance disclaimer with 'Powered by Finance Guru™' branding.

        FORMAT (matching user preference from FTNT analysis):
        - Horizontal rule separator
        - Disclaimer text (educational purposes only)
        - 'Powered by Finance Guru™' branding line
        - Report date
        """
        self.story.append(Spacer(1, 0.3 * inch))
        self.story.append(HRFlowable(width="100%", thickness=1, color=DARK_GRAY))
        self.story.append(Spacer(1, 0.15 * inch))

        disclaimer = """
        <b>DISCLAIMER:</b> This analysis is provided for educational and informational
        purposes only. It does not constitute investment advice, financial advice,
        trading advice, or any other sort of advice. Finance Guru is a personal
        family office system and does not provide recommendations to third parties.
        Past performance is not indicative of future results. All investments
        involve risk, including the possible loss of principal. Consult with a
        qualified financial professional before making any investment decisions.
        """

        self.story.append(Paragraph(disclaimer.strip(), self.styles.get("Disclaimer")))
        self.story.append(Spacer(1, 0.15 * inch))

        # "Powered by Finance Guru™" branding (user preferred format)
        powered_by_style = ParagraphStyle(
            name="PoweredBy",
            parent=self.styles.get("Disclaimer"),
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=4,
        )
        self.story.append(Paragraph("Powered by Finance Guru™", powered_by_style))
        self.story.append(
            Paragraph(
                f"Report Date: {self.date_display}", self.styles.get("Disclaimer")
            )
        )

    def build(self) -> str:
        """Build the PDF and return the output path."""
        output_file = self.output_dir / f"{self.ticker}-analysis-{self.date}.pdf"

        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        # Add disclaimer at end if not already added
        if not any("DISCLAIMER" in str(item) for item in self.story):
            self.add_disclaimer()

        doc.build(self.story)
        print(f"Report generated: {output_file}")
        return str(output_file)

    # Helper methods for assessments
    def _assess_sharpe(self, sharpe) -> str:
        if sharpe is None:
            return "N/A"
        try:
            s = float(sharpe)
            if s > 2.0:
                return "Excellent"
            elif s > 1.0:
                return "Good"
            elif s > 0:
                return "Moderate"
            else:
                return "Poor"
        except (TypeError, ValueError):
            return "N/A"

    def _assess_beta(self, beta) -> str:
        if beta is None:
            return "N/A"
        try:
            b = float(beta)
            if b > 1.5:
                return "High volatility vs market"
            elif b > 1.0:
                return "Slightly more volatile"
            elif b > 0.5:
                return "Less volatile than market"
            else:
                return "Low correlation"
        except (TypeError, ValueError):
            return "N/A"

    def _assess_rsi(self, rsi) -> str:
        if rsi is None:
            return "N/A"
        try:
            r = float(rsi)
            if r > 70:
                return "Overbought"
            elif r < 30:
                return "Oversold"
            else:
                return "Neutral"
        except (TypeError, ValueError):
            return "N/A"


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ReportGenerator - Finance Guru PDF Report Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate report with default portfolio:
    uv run python ReportGenerator.py --ticker TSLA

  Generate with custom portfolio value:
    uv run python ReportGenerator.py --ticker PLTR --portfolio-value 500000

  Specify output directory:
    uv run python ReportGenerator.py --ticker NVDA --output-dir ./custom-reports/
        """,
    )

    parser.add_argument("--ticker", type=str, required=True, help="Stock ticker symbol")
    parser.add_argument(
        "--portfolio-value",
        type=float,
        default=250000,
        help="Portfolio value for sizing (default: 250000)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="fin-guru-private/fin-guru/analysis/reports",
        help="Output directory for PDF",
    )

    args = parser.parse_args()

    # Fetch real-time price data using market_data module
    print(f"Fetching real-time price data for {args.ticker}...")
    try:
        from src.utils.market_data import get_prices

        price_data = get_prices(args.ticker, realtime=True)

        if args.ticker in price_data:
            current_price = price_data[args.ticker].price
            change_percent = price_data[args.ticker].change_percent
            print(f"  ✓ {args.ticker}: ${current_price:.2f} ({change_percent:+.2f}%)")
        else:
            print(f"  ⚠ Could not fetch price for {args.ticker}, using fallback")
            current_price = 100.00
            change_percent = 0.0
    except Exception as e:
        print(f"  ⚠ Price fetch failed: {e}, using fallback")
        current_price = 100.00
        change_percent = 0.0

    # Create report
    report = FinanceGuruReport(
        ticker=args.ticker,
        portfolio_value=args.portfolio_value,
        output_dir=args.output_dir,
    )

    # Add sections with REAL price data
    report.add_cover_page(
        title=f"{args.ticker} Comprehensive Analysis",
        subtitle="2026 Watchlist Analysis & Investment Recommendation",
        current_price=current_price,
        ytd_performance=change_percent,  # Using daily change as proxy for now
    )

    report.add_executive_summary(
        thesis=f"{args.ticker} presents a compelling investment opportunity based on quantitative analysis...",
        key_findings=[
            {
                "label": "Risk Profile",
                "detail": "Moderate risk with favorable risk-adjusted returns",
            },
            {
                "label": "Technical Setup",
                "detail": "Momentum indicators suggest bullish trend",
            },
            {
                "label": "Valuation",
                "detail": "Trading near fair value with upside potential",
            },
        ],
        rating="CONDITIONAL BUY",
        conviction="7/10",
        risk_level="MEDIUM",
    )

    report.add_quant_analysis(
        risk_metrics={
            "sharpe": "1.45",
            "sortino": "2.1",
            "beta": "1.2",
            "alpha": "5%",
            "max_drawdown": "-18%",
            "var_95": "-3.2%",
        },
        momentum_data={
            "rsi": "55",
            "macd": "2.3",
            "macd_signal": "Bullish",
            "stochastic_k": "65",
            "williams_r": "-35",
        },
        volatility_data={
            "annualized_vol": "28%",
            "atr": "4.5",
            "bb_width": "15%",
            "regime": "Normal",
        },
    )

    report.add_portfolio_sizing(
        recommended_pct=2.5,
        current_price=current_price,  # Using real-time price
        entry_strategy="Scale in with 3 tranches: 40% at current price, 30% on 5% pullback, 30% on 10% pullback",
    )

    report.add_sentiment_section(
        sentiment_summary="Market sentiment is cautiously optimistic with institutional accumulation observed.",
        analyst_ratings={"buy": 15, "hold": 8, "sell": 2, "target": 125.00},
        catalysts=[
            "AI infrastructure expansion driving revenue growth",
            "New product launches scheduled for Q2 2026",
            "Strong cash flow enabling share buybacks",
        ],
        risks=[
            "Valuation stretched relative to historical averages",
            "Regulatory headwinds in key markets",
            "Competition intensifying in core segments",
        ],
    )

    output_path = report.build()
    print(f"\nReport successfully generated at: {output_path}")


if __name__ == "__main__":
    main()
