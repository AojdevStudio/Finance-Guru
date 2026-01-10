#!/usr/bin/env python3
"""
Finance Guru™ Watchlist Analysis Report Generator
Generates PDF reports for ticker analysis
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


def generate_crwd_report(output_path: str):
    """Generate the CRWD analysis report"""
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
        ["Ticker", "CRWD"],
        ["Company", "CrowdStrike Holdings, Inc."],
        ["Sector", "Cybersecurity / Software"],
        ["Current Price", "$477.26"],
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
        ["Business Quality", "Exceptional - market leader, strong moat", "★★★★★"],
        ["Growth Trajectory", "Accelerating ARR, AI tailwinds", "★★★★★"],
        ["Valuation", "Stretched (136x forward P/E)", "★★☆☆☆"],
        ["Technical Setup", "Deeply oversold - favorable entry", "★★★★☆"],
        ["Portfolio Fit", "Layer 1 growth, moderate diversification", "★★★☆☆"],
        ["Risk Profile Match", "Aligns with aggressive tolerance", "★★★★☆"],
    ]
    story.append(create_table(thesis_data, col_widths=[1.5*inch, 3.5*inch, 1.5*inch]))
    story.append(Spacer(1, 15))

    # Market Research Summary
    story.append(Paragraph("Market Research Summary", styles['SectionHeader']))
    story.append(Paragraph(
        "<b>Company Overview:</b> CrowdStrike is the leading cloud-native cybersecurity platform, "
        "positioned as 'the operating system of cybersecurity.' The Falcon platform provides "
        "endpoint protection, threat intelligence, and AI-driven security.",
        styles['ReportBody']
    ))

    q3_data = [
        ["Metric", "Q3 FY2026 Result", "YoY Growth"],
        ["Revenue", "$1.23B", "+22.2%"],
        ["Ending ARR", "$4.92B", "+23%"],
        ["Net New ARR", "$265M (record)", "+73%"],
        ["EPS", "$0.96", "Beat by 2.1%"],
        ["Free Cash Flow", "$296M (record Q3)", "—"],
        ["Falcon Flex ARR", "$1.35B", "+200%"],
    ]
    story.append(create_table(q3_data, col_widths=[2*inch, 2.5*inch, 2*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>July 2024 Outage Recovery:</b> Faulty Falcon update affected 8.5M Windows devices. "
        "Fortune 500 lost ~$5.4B. However, customer retention remained strong with NO significant "
        "exodus - validating platform stickiness and high switching costs. CRWD is fully recovered.",
        styles['ReportBody']
    ))
    story.append(Spacer(1, 15))

    # Quantitative Analysis
    story.append(Paragraph("Quantitative Analysis", styles['SectionHeader']))

    story.append(Paragraph("Risk Metrics (252-Day)", styles['SubSection']))
    risk_data = [
        ["Metric", "Value", "Interpretation"],
        ["VaR (95%, Daily)", "-4.11%", "High risk"],
        ["CVaR (95%, Daily)", "-5.87%", "Significant tail risk"],
        ["Sharpe Ratio", "0.66", "Poor (<1.0)"],
        ["Sortino Ratio", "1.11", "Acceptable"],
        ["Max Drawdown", "-32.17%", "Significant"],
        ["Annual Volatility", "46.35%", "High (40-80% band)"],
        ["Beta vs SPY", "1.56", "High systematic risk"],
        ["Alpha vs SPY", "+17.59%", "Strong outperformance"],
    ]
    story.append(create_table(risk_data, col_widths=[2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Momentum Indicators (90-Day)", styles['SubSection']))
    momentum_data = [
        ["Indicator", "Value", "Signal"],
        ["RSI", "32.67", "Neutral (approaching oversold)"],
        ["MACD", "-7.49", "Bearish"],
        ["Stochastic %K", "0.31", "Oversold"],
        ["Williams %R", "-99.69", "Extremely oversold"],
        ["ROC", "-6.77%", "Bearish"],
        ["Confluence", "2/5 Bull, 2/5 Bear", "Mixed signals"],
    ]
    story.append(create_table(momentum_data, col_widths=[2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Portfolio Correlation", styles['SubSection']))
    corr_data = [
        ["Your Holding", "Correlation with CRWD", "Impact"],
        ["PLTR", "0.555", "Moderate"],
        ["TSLA", "0.497", "Moderate"],
        ["NVDA", "0.606", "High"],
        ["VOO", "0.664", "High"],
    ]
    story.append(create_table(corr_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Paragraph("Diversification Score: 0.403 (GOOD)", styles['ReportBody']))
    story.append(Spacer(1, 15))

    # Strategy Recommendation
    story.append(Paragraph("Strategy Recommendation", styles['SectionHeader']))

    story.append(Paragraph("Position Sizing", styles['SubSection']))
    sizing_data = [
        ["Factor", "Recommendation"],
        ["Recommended Allocation", "2-3% ($5,000-$7,500)"],
        ["Entry Strategy", "Scale in over 2-3 tranches"],
        ["Initial Position", "$2,500 (T1) at current levels"],
    ]
    story.append(create_table(sizing_data, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Entry Plan", styles['SubSection']))
    entry_data = [
        ["Tranche", "Price Target", "Amount", "Notes"],
        ["T1", "Current ($477)", "$2,500", "Oversold entry"],
        ["T2", "$440-450", "$2,500", "If weakness continues"],
        ["T3", "$400-420", "$2,500", "Full position if major pullback"],
    ]
    story.append(create_table(entry_data, col_widths=[1*inch, 1.5*inch, 1.5*inch, 2.5*inch]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Risk Management", styles['SubSection']))
    risk_mgmt_data = [
        ["Metric", "Level", "Action"],
        ["Stop Loss", "$400 (-16%)", "Hard stop"],
        ["Target Price (12mo)", "$550-600", "+15-25% upside"],
        ["Position Monitor", "Quarterly earnings", "Must beat expectations"],
        ["Red Flag", "Customer churn > 5%", "Exit immediately"],
    ]
    story.append(create_table(risk_mgmt_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 15))

    # 2026 Catalysts
    story.append(Paragraph("2026 Catalysts", styles['SectionHeader']))
    catalysts = [
        ["Catalyst", "Details"],
        ["AI Security (Charlotte AI)", "AI-native threat detection driving upsells"],
        ["Platform Consolidation", "Customers consolidating security vendors onto Falcon"],
        ["Cloud Security Growth", "Cloud, Identity, and SIEM products accelerating"],
        ["Enterprise Partnerships", "AWS, EY, CoreWeave, Kroll validating leadership"],
        ["Falcon Flex Model", "Subscription flexibility driving 200%+ ARR growth"],
    ]
    story.append(create_table(catalysts, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 15))

    # Key Risks
    story.append(Paragraph("Key Risks to Monitor", styles['SectionHeader']))
    risks = [
        ["Risk", "Impact"],
        ["Valuation compression", "If AI hype fades, multiple could contract significantly"],
        ["Competition", "Microsoft Defender, Palo Alto, SentinelOne are threats"],
        ["Economic sensitivity", "Enterprise security budgets could be cut in recession"],
        ["Tech concentration", "Adding CRWD increases your tech exposure further"],
    ]
    story.append(create_table(risks, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 20))

    # Final Summary Box
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GOLD))
    story.append(Spacer(1, 10))
    final_data = [
        ["FINAL RECOMMENDATION"],
        ["Action: BUY (Scale-in)"],
        ["Timing: Now (T1) - Oversold conditions"],
        ["Size: Start with $2,500"],
        ["Layer: Layer 1 Growth"],
        ["Conviction: Medium-High"],
        ["Time Horizon: 12-24 months"],
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

    output_file = output_dir / f"CRWD-analysis-{datetime.now().strftime('%Y-%m-%d')}.pdf"
    generate_crwd_report(str(output_file))
