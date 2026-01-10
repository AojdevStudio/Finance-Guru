#!/usr/bin/env python3
"""
Finance Guru™ Watchlist Analysis Report Generator - AVGO
Generates PDF report for Broadcom Inc. (AVGO) analysis
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from pathlib import Path


# Finance Guru brand colors
BRAND_NAVY = HexColor("#1a365d")
BRAND_GOLD = HexColor("#d69e2e")
BRAND_GREEN = HexColor("#38a169")
BRAND_RED = HexColor("#e53e3e")
BRAND_GRAY = HexColor("#718096")


def create_styles():
    """Create custom styles for the report"""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=BRAND_NAVY,
        spaceAfter=20,
        alignment=TA_CENTER,
    ))

    # Section header style
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=BRAND_NAVY,
        spaceBefore=15,
        spaceAfter=10,
        borderColor=BRAND_GOLD,
        borderWidth=2,
        borderPadding=5,
    ))

    # Subsection style
    styles.add(ParagraphStyle(
        name='SubSection',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=BRAND_NAVY,
        spaceBefore=10,
        spaceAfter=5,
    ))

    # Body text - using custom name to avoid conflict
    styles.add(ParagraphStyle(
        name='ReportBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        leading=14,
    ))

    # Verdict style
    styles.add(ParagraphStyle(
        name='Verdict',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=BRAND_GREEN,
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=10,
    ))

    # Disclaimer style
    styles.add(ParagraphStyle(
        name='Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=BRAND_GRAY,
        alignment=TA_CENTER,
        spaceBefore=20,
    ))

    return styles


def create_table(data, col_widths=None):
    """Create a styled table"""
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


def generate_avgo_report(output_path: str):
    """Generate the AVGO analysis report"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = create_styles()
    story = []

    # Header
    story.append(Paragraph("Finance Guru™", styles['ReportTitle']))
    story.append(Paragraph("2026 Watchlist Analysis Report", styles['SubSection']))
    story.append(Spacer(1, 10))

    # Ticker info
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GOLD))
    story.append(Spacer(1, 10))

    ticker_info = [
        ["Ticker", "AVGO"],
        ["Company", "Broadcom Inc."],
        ["Sector", "Semiconductors / AI Infrastructure"],
        ["Current Price", "$329.88"],
        ["Analysis Date", datetime.now().strftime("%B %d, %Y")],
    ]
    story.append(create_table(ticker_info, col_widths=[2*inch, 4.5*inch]))
    story.append(Spacer(1, 20))

    # Verdict
    story.append(Paragraph("VERDICT: CONDITIONAL BUY ✓", styles['Verdict']))
    story.append(Spacer(1, 10))

    # Investment Thesis Summary
    story.append(Paragraph("Investment Thesis Summary", styles['SectionHeader']))
    thesis_data = [
        ["Dimension", "Assessment", "Rating"],
        ["Business Quality", "Exceptional - AI chip leader, VMware integration", "★★★★★"],
        ["Growth Trajectory", "AI revenue doubling to $40B in FY2026", "★★★★★"],
        ["Valuation", "Fair after -18% pullback from highs", "★★★★☆"],
        ["Technical Setup", "Oversold - near lower Bollinger Band", "★★★★☆"],
        ["Portfolio Fit", "High correlation with NVDA/VOO", "★★☆☆☆"],
        ["Risk Profile Match", "High volatility aligns with aggressive tolerance", "★★★★☆"],
    ]
    story.append(create_table(thesis_data, col_widths=[1.5*inch, 3.5*inch, 1.5*inch]))
    story.append(Spacer(1, 15))

    # Market Research Summary
    story.append(Paragraph("Market Research Summary", styles['SectionHeader']))
    story.append(Paragraph(
        "<b>Company Overview:</b> Broadcom is a vertically integrated AI infrastructure powerhouse, "
        "combining custom AI chip design (ASICs for Google, Meta, OpenAI) with VMware's enterprise "
        "software stack. The company sits at the critical intersection of AI accelerators and AI networking "
        "as hyperscalers build massive data centers.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 10))

    # Key Metrics
    key_metrics = [
        ["Metric", "FY2025 (Current)", "FY2026 Projection"],
        ["AI Revenue", "$20B", "$40B (+100%)"],
        ["Total Market Cap", "$1.9T (Nov 2025)", "—"],
        ["AI Revenue by 2030", "—", "$120B (CEO target)"],
        ["Trailing P/E", "100+", "High premium"],
        ["Stock Performance YTD", "+46% (through Nov)", "—"],
        ["Recent Pullback", "-18% from highs", "Now at $329.88"],
    ]
    story.append(create_table(key_metrics, col_widths=[2*inch, 2.5*inch, 2*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>AI Chip Dominance:</b> Q4 AI revenue hit $6.5B (+74% YoY). Broadcom announced $10B+ in "
        "new AI orders for 2026 from a major customer, deepening partnerships with Alphabet, OpenAI, "
        "Meta, and Anthropic for custom AI processors.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>VMware Acquisition ($69B):</b> Closed Nov 2023. Positions Broadcom as unique vertically "
        "integrated provider - from chips to cloud-native tools. VMware Cloud Foundation (VCF) enables "
        "hybrid AI infrastructure management across public/private clouds, generating solid subscription growth.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 15))

    # Quantitative Analysis
    story.append(Paragraph("Quantitative Analysis", styles['SectionHeader']))

    story.append(Paragraph("Risk Metrics (252-Day)", styles['SubSection']))
    risk_data = [
        ["Metric", "Value", "Interpretation"],
        ["VaR (95%, Daily)", "-4.92%", "High risk - losses can exceed 4.92%"],
        ["CVaR (95%, Daily)", "-7.66%", "Significant tail risk - 7.66% avg loss when VaR breached"],
        ["Sharpe Ratio", "1.29", "Good (1.0-2.0 range)"],
        ["Sortino Ratio", "1.94", "Excellent - strong downside protection"],
        ["Max Drawdown", "-41.15%", "Worst peak-to-trough decline"],
        ["Annual Volatility", "60.13%", "HIGH (40-80% band)"],
        ["Beta vs SPY", "1.85", "High systematic risk (aggressive)"],
        ["Alpha vs SPY", "+61.81%", "Exceptional outperformance"],
    ]
    story.append(create_table(risk_data, col_widths=[2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Momentum Indicators (90-Day)", styles['SubSection']))
    momentum_data = [
        ["Indicator", "Value", "Signal"],
        ["RSI", "35.16", "Neutral (approaching oversold)"],
        ["MACD", "-1.84 (below signal -6.14)", "Bearish - downward momentum"],
        ["Stochastic %K", "4.94", "Oversold (<20) - potential reversal up"],
        ["Williams %R", "-95.06", "Oversold (<-80) - potential buy signal"],
        ["ROC", "-15.56%", "Bearish - negative momentum"],
        ["Confluence", "2/5 Bull, 2/5 Bear", "MIXED SIGNALS - no clear direction"],
    ]
    story.append(create_table(momentum_data, col_widths=[2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Volatility Analysis (90-Day)", styles['SubSection']))
    vol_data = [
        ["Metric", "Value", "Interpretation"],
        ["Volatility Regime", "HIGH", "Reduce position sizes (2-5% of portfolio)"],
        ["ATR (Average True Range)", "$19.20 (5.82%)", "Suggested stop loss: 2x ATR = $38.41"],
        ["Annual Volatility", "70.52%", "Very high - expect large swings"],
        ["Bollinger Bands", "Lower: $318.51 | Mid: $374.69 | Upper: $430.87", "Price near LOWER band (support)"],
        ["Bollinger %B", "0.101", "Price in lower 10% of band range"],
        ["Bandwidth", "29.99%", "Wide bands = high volatility"],
    ]
    story.append(create_table(vol_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Portfolio Correlation Analysis", styles['SubSection']))
    corr_data = [
        ["Your Holding", "Correlation with AVGO", "Impact"],
        ["PLTR", "0.491", "Moderate"],
        ["TSLA", "0.448", "Moderate"],
        ["NVDA", "0.719", "VERY HIGH - overlapping AI exposure"],
        ["VOO", "0.670", "HIGH - moves with broad market"],
    ]
    story.append(create_table(corr_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Paragraph(
        "Diversification Score: 0.401 (GOOD) - Average correlation: 0.599. "
        "<b>⚠️ NOTE:</b> Very high correlation with NVDA (0.719) means adding AVGO increases AI chip concentration risk.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 15))

    # Strategy Recommendation
    story.append(Paragraph("Strategy Recommendation", styles['SectionHeader']))

    story.append(Paragraph("Position Sizing", styles['SubSection']))
    sizing_data = [
        ["Factor", "Recommendation"],
        ["Recommended Allocation", "2-3% ($5,000-$7,500)"],
        ["Entry Strategy", "Scale in over 3 tranches - WAIT for confirmation"],
        ["Initial Position", "$2,000-2,500 (T1) at current oversold levels"],
        ["⚠️ Constraint", "High NVDA correlation - don't over-concentrate AI chips"],
    ]
    story.append(create_table(sizing_data, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Entry Plan", styles['SubSection']))
    entry_data = [
        ["Tranche", "Price Target", "Amount", "Notes"],
        ["T1", "$320-330 (current)", "$2,000-2,500", "Oversold entry - near lower Bollinger"],
        ["T2", "$340-350", "$2,500", "If momentum confirms reversal"],
        ["T3", "$300-310", "$2,500", "If further weakness - major support"],
    ]
    story.append(create_table(entry_data, col_widths=[1*inch, 1.5*inch, 1.5*inch, 2.5*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Risk Management", styles['SubSection']))
    risk_mgmt_data = [
        ["Metric", "Level", "Action"],
        ["Stop Loss", "$290 (-12%)", "Hard stop - breaks key support"],
        ["Target Price (12mo)", "$425-500", "+29-52% upside (analyst targets)"],
        ["Position Monitor", "Quarterly earnings", "AI revenue growth must continue"],
        ["Red Flag #1", "AI revenue growth < 50% YoY", "Re-evaluate thesis"],
        ["Red Flag #2", "VMware customer churn > 10%", "Integration concerns - exit"],
    ]
    story.append(create_table(risk_mgmt_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 15))

    # 2026 Catalysts
    story.append(Paragraph("2026 Catalysts", styles['SectionHeader']))
    catalysts = [
        ["Catalyst", "Details"],
        ["AI Revenue Doubling", "$40B in FY2026 (from $20B) - custom chips for hyperscalers"],
        ["$10B+ New Orders", "Major customer AI infrastructure orders for 2026 delivery"],
        ["VMware Cloud Foundation", "Hybrid AI workload management driving enterprise adoption"],
        ["Hyperscaler Partnerships", "Deepening ties with Google, OpenAI, Meta, Anthropic"],
        ["AI Networking Boom", "Data center networking equipment for AI clusters"],
        ["Analyst Upgrades", "Jefferies names AVGO top semiconductor pick for 2026"],
    ]
    story.append(create_table(catalysts, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 15))

    # Key Risks
    story.append(Paragraph("Key Risks to Monitor", styles['SectionHeader']))
    risks = [
        ["Risk", "Impact"],
        ["AI Air Pocket (BofA warning)", "Temporary cooling of AI spending in 2026 could hit high-multiple stocks"],
        ["Valuation Compression", "P/E 100+ - any AI hype fade could re-rate to 25-30x semiconductor peers"],
        ["VMware Customer Churn", "Pricing changes post-acquisition causing enterprise defections"],
        ["Tech Concentration", "Very high correlation with NVDA (0.719) = overlapping AI exposure"],
        ["High Volatility", "60-70% annual volatility = expect -20-30% drawdowns"],
        ["Margin Concerns", "AI chip margins under scrutiny - recent stock weakness"],
    ]
    story.append(create_table(risks, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 15))

    # Analyst Consensus
    story.append(Paragraph("Wall Street Consensus", styles['SectionHeader']))
    analyst_data = [
        ["Metric", "Value"],
        ["Rating", "STRONG BUY (23 Buys, 2 Holds)"],
        ["Average Price Target", "$425-435"],
        ["Upside from Current", "+29-32%"],
        ["Jefferies Target", "$500 (+52%) - Top 2026 Pick"],
        ["Mizuho Target", "$450 (Outperform)"],
        ["Morgan Stanley Target", "$462 (Overweight)"],
    ]
    story.append(create_table(analyst_data, col_widths=[3*inch, 3.5*inch]))
    story.append(Spacer(1, 20))

    # Final Summary Box
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GOLD))
    story.append(Spacer(1, 10))
    final_data = [
        ["FINAL RECOMMENDATION"],
        ["Action: CONDITIONAL BUY (Scale-in)"],
        ["Timing: T1 Now at oversold levels | T2 on momentum confirmation"],
        ["Size: Start with $2,000-2,500 (2-3% max total)"],
        ["Layer: Layer 1 Growth (AI Infrastructure)"],
        ["Conviction: Medium-High"],
        ["Time Horizon: 12-24 months"],
        ["⚠️ KEY CONSIDERATION: High NVDA correlation - manage AI chip concentration"],
    ]
    final_table = Table(final_data, colWidths=[6.5*inch])
    final_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor("#e6fffa")),
        ('TEXTCOLOR', (0, 1), (-1, -1), BRAND_NAVY),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
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

    # Build PDF
    doc.build(story)
    print(f"✅ Report generated: {output_path}")


if __name__ == "__main__":
    output_dir = Path("/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"AVGO-analysis-{datetime.now().strftime('%Y-%m-%d')}.pdf"
    generate_avgo_report(str(output_file))
