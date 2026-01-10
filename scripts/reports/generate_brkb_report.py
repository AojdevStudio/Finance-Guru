#!/usr/bin/env python3
"""
Finance Guru™ - BRK.B Analysis Report Generator
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from pathlib import Path


BRAND_NAVY = HexColor("#1a365d")
BRAND_GOLD = HexColor("#d69e2e")
BRAND_GREEN = HexColor("#38a169")
BRAND_GRAY = HexColor("#718096")


def create_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle', parent=styles['Heading1'], fontSize=24, textColor=BRAND_NAVY, spaceAfter=20, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SectionHeader', parent=styles['Heading2'], fontSize=14, textColor=BRAND_NAVY, spaceBefore=15, spaceAfter=10))
    styles.add(ParagraphStyle(name='SubSection', parent=styles['Heading3'], fontSize=12, textColor=BRAND_NAVY, spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name='ReportBody', parent=styles['Normal'], fontSize=10, spaceAfter=8, leading=14))
    styles.add(ParagraphStyle(name='Verdict', parent=styles['Heading1'], fontSize=18, textColor=BRAND_GREEN, alignment=TA_CENTER, spaceBefore=10, spaceAfter=10))
    styles.add(ParagraphStyle(name='Disclaimer', parent=styles['Normal'], fontSize=8, textColor=BRAND_GRAY, alignment=TA_CENTER, spaceBefore=20))
    return styles


def create_table(data, col_widths=None):
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor("#f7fafc")),
        ('TEXTCOLOR', (0, 1), (-1, -1), black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return table


def generate_brkb_report(output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = create_styles()
    story = []

    # Header
    story.append(Paragraph("Finance Guru™", styles['ReportTitle']))
    story.append(Paragraph("2026 Watchlist Analysis Report", styles['SubSection']))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GOLD))
    story.append(Spacer(1, 10))

    # Ticker info header
    header_data = [
        ["Ticker", "BRK-B", "Analyst Team", "Finance Guru™ Quant Team"],
        ["Company", "Berkshire Hathaway Inc. (Class B)", "Current Price", "$503.39"],
        ["Sector", "Diversified Financials", "YTD Performance", "+11.0% (vs SPY +15%)"],
        ["Market Cap", "$1.09 Trillion", "52-Week Range", "$458.88 - $542.07"],
        ["Analysis Date", datetime.now().strftime("%B %d, %Y"), "Report Version", "v2.0.0"],
    ]
    header_table = Table(header_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2.5*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, -1), HexColor("#f7fafc")),
        ('BACKGROUND', (2, 0), (3, -1), HexColor("#e6f7ff")),
        ('TEXTCOLOR', (0, 0), (-1, -1), BRAND_NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))

    # Verdict
    story.append(Paragraph("VERDICT: BUY WITH CAUTION ⚠", styles['Verdict']))
    story.append(Spacer(1, 10))

    # Executive Summary
    story.append(Paragraph("Executive Summary", styles['SectionHeader']))
    story.append(Paragraph(
        "Berkshire Hathaway represents Warren Buffett's legendary conglomerate holding company with $382B cash, "
        "diversified operating businesses, and a conservative value approach. While fundamentally strong with excellent "
        "diversification benefits, current momentum signals are mixed with succession uncertainty casting shadow over 2026.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 10))

    # Investment Thesis
    story.append(Paragraph("Investment Thesis Summary", styles['SectionHeader']))
    thesis_data = [
        ["Dimension", "Assessment", "Rating"],
        ["Business Quality", "Legendary - Buffett's masterpiece", "★★★★★"],
        ["Valuation", "Fair at 16.1x P/E", "★★★☆☆"],
        ["Diversification Benefit", "EXCEPTIONAL for tech-heavy portfolio", "★★★★★"],
        ["Volatility", "Low (18.55% annual)", "★★★★☆"],
        ["2026 Catalysts", "Succession, cash deployment uncertainty", "★★★☆☆"],
        ["Technical Momentum", "Mixed signals, bearish MACD", "★★☆☆☆"],
        ["Risk Profile", "Defensive, low beta (0.48)", "★★★★★"],
    ]
    story.append(create_table(thesis_data, col_widths=[2*inch, 3*inch, 1.5*inch]))
    story.append(Spacer(1, 15))

    # Q3 2025 Results
    story.append(Paragraph("Q3 2025 Financial Results", styles['SectionHeader']))
    q3_data = [
        ["Metric", "Result", "YoY Change"],
        ["Operating Profit", "$13.485B", "+34%"],
        ["Insurance Underwriting", "$2.37B", "+200%"],
        ["Cash Position", "$381.7B", "RECORD"],
        ["Share Buybacks", "$0", "Waiting for opportunities"],
    ]
    story.append(create_table(q3_data, col_widths=[2.5*inch, 2*inch, 2*inch]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Key Insight:</b> Warren Buffett has built a $382 billion 'war chest' signaling he's waiting for "
        "market dislocations to deploy capital. Greg Abel takes over as CEO on January 1, 2026, with Buffett remaining Chairman.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 15))

    # Business Overview
    story.append(Paragraph("Business Overview & Competitive Advantages", styles['SectionHeader']))
    story.append(Paragraph(
        "Berkshire Hathaway operates as a diversified holding company with three core pillars: "
        "(1) <b>Insurance Operations</b> - GEICO, National Indemnity, Berkshire Hathaway Primary Group generating $174B float; "
        "(2) <b>Operating Businesses</b> - BNSF Railroad, Berkshire Hathaway Energy, manufacturing, retail; "
        "(3) <b>Investment Portfolio</b> - $360B in equities including Apple (21.4%), Bank of America (9.6%), and new Alphabet position.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 10))

    bus_strengths = [
        ["Business Segment", "Key Metrics", "Competitive Moat"],
        ["Insurance (Float)", "$174B, up from $171B YoY", "Cost-free capital, underwriting discipline"],
        ["BNSF Railroad", "$1.47B Q3 earnings, +19% YoY", "Network effects, high barriers to entry"],
        ["BH Energy", "$0.70B Q3 earnings, +7% YoY", "Regulated utility, stable cash flows"],
        ["Investment Portfolio", "Apple 21.4%, diversified holdings", "Patient capital, no fund constraints"],
        ["Leadership", "Buffett → Abel transition Jan 2026", "25-year veteran, cultural continuity"],
    ]
    story.append(create_table(bus_strengths, col_widths=[2*inch, 2.5*inch, 2*inch]))
    story.append(Spacer(1, 15))

    # Quantitative Analysis
    story.append(Paragraph("Quantitative Analysis", styles['SectionHeader']))

    story.append(Paragraph("Risk Metrics (252-Day Analysis)", styles['SubSection']))
    risk_data = [
        ["Metric", "Value", "Interpretation"],
        ["95% VaR (Daily)", "-1.53%", "95% of days, losses won't exceed 1.53%"],
        ["95% CVaR (Daily)", "-2.65%", "Expected loss in worst 5% of days"],
        ["Sharpe Ratio", "0.21", "POOR - below 1.0 threshold"],
        ["Sortino Ratio", "0.28", "Low risk-adjusted returns"],
        ["Max Drawdown", "-14.95%", "Worst peak-to-trough decline"],
        ["Calmar Ratio", "0.57", "Annual return per unit drawdown"],
        ["Annual Volatility", "18.55%", "LOW - defensive positioning"],
        ["Beta vs SPY", "0.48", "Low systematic risk (defensive)"],
        ["Alpha vs SPY", "-0.10%", "Underperforming benchmark annually"],
    ]
    story.append(create_table(risk_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Momentum Indicators (90-Day Analysis)", styles['SubSection']))
    momentum_data = [
        ["Indicator", "Value", "Signal"],
        ["RSI", "53.79", "Neutral - no extreme condition"],
        ["MACD Line", "0.55", "Bearish - below signal line"],
        ["MACD Signal", "0.98", "Downward momentum"],
        ["Stochastic %K", "54.96", "Neutral"],
        ["Williams %R", "-45.04", "Neutral"],
        ["ROC", "-0.84%", "Bearish - negative momentum"],
        ["Confluence", "2/5 Bearish", "⚠ Mixed signals, no clear trend"],
    ]
    story.append(create_table(momentum_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Volatility Metrics (90-Day)", styles['SubSection']))
    vol_data = [
        ["Metric", "Value", "Interpretation"],
        ["Volatility Regime", "LOW", "Can use 10-20% position sizing"],
        ["ATR Value", "$6.79", "Average daily range"],
        ["ATR %", "1.35%", "Very low daily swings"],
        ["Suggested Stop", "$13.59", "2x ATR for risk management"],
        ["Bollinger %B", "0.513", "Within normal range"],
        ["BB Bandwidth", "4.83%", "Narrow bands - potential breakout"],
    ]
    story.append(create_table(vol_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 15))

    # Market Sentiment & 2026 Outlook
    story.append(Paragraph("Market Sentiment & 2026 Outlook", styles['SectionHeader']))
    story.append(Paragraph(
        "<b>Analyst Consensus:</b> Moderate Buy with average 12-month price target of $538 (range: $481-$595). "
        "YTD performance of +11% trails S&P 500 but outperforms financials peer group.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("2026 Catalysts & Risks", styles['SubSection']))
    catalysts = [
        ["Factor", "Type", "Impact"],
        ["$382B Cash Deployment", "Catalyst", "Market dislocation = buying opportunity"],
        ["Greg Abel CEO Transition", "Risk/Catalyst", "Succession Jan 1, 2026 - uncertainty"],
        ["Insurance Super-Cycle", "Catalyst", "Hard market driving underwriting gains"],
        ["Apple Stake Reduction", "Risk", "Trimmed from 300M to 238M shares in 2025"],
        ["Todd Combs Departure", "Risk", "Investment manager leaving for JPMorgan"],
        ["Portfolio Concentration", "Risk", "Top 10 positions = 87.3% of holdings"],
        ["Valuation Concerns", "Risk", "Cash earning interest may decline with rate cuts"],
    ]
    story.append(create_table(catalysts, col_widths=[2.5*inch, 1.5*inch, 2.5*inch]))
    story.append(Spacer(1, 15))

    # Portfolio Positioning
    story.append(Paragraph("Portfolio Positioning for $250,000 Portfolio", styles['SectionHeader']))

    story.append(Paragraph("Position Sizing Recommendation", styles['SubSection']))
    sizing_data = [
        ["Parameter", "Recommendation", "Rationale"],
        ["Target Allocation", "3-5%", "Conservative given succession risk"],
        ["Dollar Amount", "$7,500 - $12,500", "Balance diversification vs uncertainty"],
        ["Entry Strategy", "2-3 tranches", "DCA over 4-8 weeks given mixed signals"],
        ["Initial Tranche", "$5,000 (2%)", "Start conservative, reassess post-succession"],
        ["Stop Loss Level", "$490", "2x ATR from entry (~$13.59)"],
        ["Target Price", "$538-$560", "Conservative analyst consensus range"],
        ["Time Horizon", "12-24 months", "Allow succession transition to stabilize"],
    ]
    story.append(create_table(sizing_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>Entry Timing:</b> Given bearish MACD and mixed momentum, consider waiting for either: "
        "(1) MACD bullish crossover, (2) successful test of $490 support, or (3) Greg Abel's first quarterly "
        "earnings call in Q1 2026 to assess leadership transition.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 15))

    # Final Summary Box
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GOLD))
    story.append(Spacer(1, 10))
    final_data = [
        ["FINAL RECOMMENDATION"],
        ["Action: CAUTIOUS BUY - Small Initial Position"],
        ["Initial Size: $5,000 (2% allocation)"],
        ["Full Target: $7,500-$12,500 (3-5%) over 4-8 weeks"],
        ["Entry: DCA in 2-3 tranches, watch for MACD confirmation"],
        ["Rationale: Strong fundamentals + diversification, but succession uncertainty"],
        ["Key Risks: CEO transition, bearish momentum, portfolio concentration"],
        ["Conviction: MODERATE (upgrade to HIGH post-succession clarity)"],
        ["Time Horizon: 12-24 months"],
    ]
    final_table = Table(final_data, colWidths=[6.5*inch])
    final_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor("#fff4e6")),
        ('TEXTCOLOR', (0, 1), (-1, -1), BRAND_NAVY),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, BRAND_NAVY),
    ]))
    story.append(final_table)
    story.append(Spacer(1, 20))

    # Disclaimer
    story.append(Paragraph(
        "⚠️ DISCLAIMER: All Finance Guru™ outputs are for educational purposes only and do not "
        "constitute investment advice. Please consult qualified financial professionals before "
        "making investment decisions. Past performance is not indicative of future results.",
        styles['Disclaimer']
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"Report generated by Finance Guru™ v2.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        styles['Disclaimer']
    ))

    doc.build(story)
    print(f"✅ Report generated: {output_path}")


if __name__ == "__main__":
    output_dir = Path("/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"BRKB-analysis-{datetime.now().strftime('%Y-%m-%d')}.pdf"
    generate_brkb_report(str(output_file))
