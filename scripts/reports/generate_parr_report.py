#!/usr/bin/env python3
"""
Generate PARR Analysis Report PDF
Finance Guru™ Document Builder
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib import colors
from datetime import datetime
import os

# Output path
OUTPUT_DIR = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "parr-analysis-2025-12-09.pdf")

# Ensure directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors
DARK_BLUE = HexColor("#1a365d")
LIGHT_BLUE = HexColor("#3182ce")
DARK_GRAY = HexColor("#2d3748")
LIGHT_GRAY = HexColor("#e2e8f0")
GREEN = HexColor("#38a169")
RED = HexColor("#e53e3e")
YELLOW = HexColor("#d69e2e")

def create_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=DARK_BLUE,
        spaceAfter=6,
        alignment=TA_CENTER
    ))

    # Subtitle
    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=DARK_GRAY,
        spaceAfter=20,
        alignment=TA_CENTER
    ))

    # Section heading
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=DARK_BLUE,
        spaceBefore=20,
        spaceAfter=10,
        borderColor=LIGHT_BLUE,
        borderWidth=2,
        borderPadding=5
    ))

    # Subsection heading
    styles.add(ParagraphStyle(
        name='SubHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=DARK_BLUE,
        spaceBefore=12,
        spaceAfter=6
    ))

    # Body text (override existing)
    styles['BodyText'].fontSize = 10
    styles['BodyText'].textColor = DARK_GRAY
    styles['BodyText'].spaceAfter = 8
    styles['BodyText'].alignment = TA_JUSTIFY

    # Bullet points
    styles.add(ParagraphStyle(
        name='BulletPoint',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_GRAY,
        leftIndent=20,
        spaceAfter=4
    ))

    # Disclaimer
    styles.add(ParagraphStyle(
        name='Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=10
    ))

    # Footer
    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=DARK_GRAY,
        alignment=TA_CENTER
    ))

    return styles

def create_table(data, col_widths=None, header=True):
    """Create a styled table."""
    if col_widths is None:
        col_widths = [2*inch] * len(data[0])

    table = Table(data, colWidths=col_widths)

    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    if not header:
        style_commands = [cmd for cmd in style_commands if cmd[1] != (0, 0) or cmd[0] not in ['BACKGROUND', 'TEXTCOLOR', 'FONTNAME']]

    table.setStyle(TableStyle(style_commands))
    return table

def build_report():
    """Build the complete PDF report."""
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = create_styles()
    story = []

    # ========== COVER PAGE ==========
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("FINANCE GURU™", styles['ReportSubtitle']))
    story.append(Paragraph("Par Pacific Holdings (PARR)", styles['ReportTitle']))
    story.append(Paragraph("Comprehensive Analysis Report", styles['ReportSubtitle']))
    story.append(Spacer(1, 0.5*inch))

    # Cover info table
    cover_data = [
        ["Prepared For:", "Ossie Irondi - Private Family Office"],
        ["Prepared By:", "Finance Guru™ Market Intelligence Team"],
        ["Date:", "December 9, 2025"],
        ["Data As Of:", "December 9, 2025 (Market Close Dec 8)"],
        ["Classification:", "Internal Use Only"],
    ]
    cover_table = create_table(cover_data, [2*inch, 4.5*inch], header=False)
    story.append(cover_table)

    story.append(Spacer(1, 0.5*inch))
    story.append(HRFlowable(width="80%", thickness=2, color=LIGHT_BLUE))
    story.append(Spacer(1, 0.3*inch))

    # Disclaimer box
    disclaimer_text = """<b>COMPLIANCE DISCLAIMER</b><br/>
    This analysis is for educational purposes only and does not constitute personalized investment advice.
    Past performance does not guarantee future results. Consult a licensed financial advisor before making investment decisions."""
    story.append(Paragraph(disclaimer_text, styles['Disclaimer']))

    story.append(PageBreak())

    # ========== EXECUTIVE SUMMARY ==========
    story.append(Paragraph("1. Executive Summary", styles['SectionHeading']))

    story.append(Paragraph("<b>Objective & Scope</b>", styles['SubHeading']))
    story.append(Paragraph(
        "Comprehensive analysis of Par Pacific Holdings, Inc. (NYSE: PARR), a niche regional refiner operating in "
        "logistically complex markets including Hawaii, the Pacific Northwest, and Rocky Mountain regions. This report "
        "evaluates PARR's business model, competitive positioning, technical indicators, risk metrics, and strategic "
        "outlook—including assessment of relevance to AI/data center energy demand thesis.",
        styles['BodyText']
    ))

    story.append(Paragraph("<b>Key Findings</b>", styles['SubHeading']))
    findings = [
        "• <b>Geographic Moat:</b> PARR operates the ONLY refinery serving the Hawaiian Islands (94,000 bpd), creating a near-monopoly position with captive demand from 1.4M residents, 10M+ annual tourists, and strategic military installations.",
        "• <b>Q3 2025 Outperformance:</b> Exceptional quarterly results ($5.16 EPS) were driven by a one-time EPA Small Refinery Exemption (SRE) worth ~$196M—this benefit is non-recurring.",
        "• <b>Renewables Transition:</b> Hawaii Renewables JV (closed October 2025) positions PARR as Hawaii's largest renewable fuels producer with 61M gallons/year capacity for SAF.",
    ]
    for finding in findings:
        story.append(Paragraph(finding, styles['BulletPoint']))

    story.append(Paragraph("<b>Recommended Actions</b>", styles['SubHeading']))
    actions = [
        "• <b>Do Not Purchase for Layer 2 Income:</b> PARR pays no dividend and is unsuitable for income strategy.",
        "• <b>Consider for Layer 1 Growth:</b> If pursuing energy sector exposure, PARR offers differentiated niche positioning.",
        "• <b>Not an AI/Bitcoin Energy Play:</b> PARR produces transportation fuels, not electricity.",
    ]
    for action in actions:
        story.append(Paragraph(action, styles['BulletPoint']))

    story.append(Paragraph("<b>Risk Posture: MODERATE-HIGH</b>", styles['SubHeading']))
    story.append(Paragraph(
        "PARR exhibits high volatility (54.90% annual), strong operational execution, but significant exposure to "
        "crack spread cyclicality and one-time regulatory benefits (SRE) that distort normalized earnings.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== COMPANY OVERVIEW ==========
    story.append(Paragraph("2. Company Overview", styles['SectionHeading']))

    overview_data = [
        ["Attribute", "Details"],
        ["Full Name", "Par Pacific Holdings, Inc."],
        ["Ticker", "NYSE: PARR"],
        ["Headquarters", "Houston, Texas"],
        ["Sector", "Energy - Oil & Gas Refining & Marketing"],
        ["Market Cap", "~$2.2 billion"],
        ["Current Price", "$43.29 (Dec 9, 2025)"],
    ]
    story.append(create_table(overview_data, [2*inch, 4.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Business Model: Three Operating Segments</b>", styles['SubHeading']))

    # Refining segment
    story.append(Paragraph("<b>Segment 1: Refining (Primary Business)</b>", styles['SubHeading']))
    refining_data = [
        ["Refinery", "Location", "Capacity (bpd)", "Market Served"],
        ["Par Hawaii", "Kapolei, HI", "94,000", "Hawaiian Islands"],
        ["Par Montana", "Billings, MT", "67,000", "Montana/Dakotas"],
        ["U.S. Oil", "Tacoma, WA", "~40,000", "Pacific Northwest"],
        ["Wyoming Refining", "Newcastle, WY", "~18,000", "Rocky Mountain"],
        ["TOTAL", "", "219,000", ""],
    ]
    story.append(create_table(refining_data, [1.5*inch, 1.5*inch, 1.5*inch, 2*inch]))
    story.append(Spacer(1, 0.2*inch))

    # Logistics
    story.append(Paragraph("<b>Segment 2: Logistics (Infrastructure)</b>", styles['SubHeading']))
    logistics_data = [
        ["Asset Type", "Scale"],
        ["Storage Capacity", "13 million barrels"],
        ["Pipelines", "549 miles"],
        ["Marine Vessels", "Inter-island Hawaii supply"],
        ["Single Point Mooring", "Hawaii crude receipt"],
    ]
    story.append(create_table(logistics_data, [2.5*inch, 4*inch]))
    story.append(Spacer(1, 0.2*inch))

    # Retail
    story.append(Paragraph("<b>Segment 3: Retail</b>", styles['SubHeading']))
    story.append(Paragraph(
        "121 fuel stations in Hawaii and Pacific Northwest operating under Hele, 76, and nomnom brands. "
        "Vertically integrated model: refine → distribute → retail at the pump.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== COMPETITIVE MOAT ==========
    story.append(Paragraph("3. Competitive Moat Analysis", styles['SectionHeading']))

    story.append(Paragraph("<b>Hawaii: The Crown Jewel</b>", styles['SubHeading']))
    moat_data = [
        ["Moat Factor", "Competitive Advantage"],
        ["Geographic Isolation", "2,400 miles from US mainland; massive shipping costs for competitors"],
        ["Sole Refinery", "ONLY refinery serving all Hawaiian Islands"],
        ["Captive Market", "1.4M residents + 10M+ tourists annually"],
        ["Military Contracts", "Strategic supplier to Pearl Harbor, Hickam AFB, DoD"],
        ["Infrastructure Lock-in", "Owns SPM, storage, pipelines, barges"],
        ["Regulatory Barriers", "Permits nearly impossible for new refinery"],
    ]
    story.append(create_table(moat_data, [2*inch, 4.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Assessment:</b> Hawaii operations function as a regulated utility without regulation—near-monopoly "
        "position with predictable demand.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== QUANTITATIVE ANALYSIS ==========
    story.append(Paragraph("4. Quantitative Analysis", styles['SectionHeading']))

    story.append(Paragraph("<b>Technical Indicators (90-Day)</b>", styles['SubHeading']))
    tech_data = [
        ["Indicator", "Value", "Signal"],
        ["RSI (14)", "50.47", "Neutral"],
        ["MACD Line", "1.18", "—"],
        ["MACD Signal", "1.60", "Bearish crossover"],
        ["Stochastic %K", "21.07", "Near oversold"],
        ["Williams %R", "-78.93", "Near oversold"],
        ["Rate of Change", "-2.20%", "Bearish momentum"],
    ]
    story.append(create_table(tech_data, [2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("<b>Momentum Confluence:</b> 0 Bullish / 2 Bearish / 3 Neutral — MIXED SIGNALS", styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Volatility Profile</b>", styles['SubHeading']))
    vol_data = [
        ["Metric", "Value", "Assessment"],
        ["Annual Volatility", "54.90%", "HIGH"],
        ["ATR (14)", "$2.10 (4.87%)", "Significant daily swings"],
        ["Max Drawdown", "-33.53%", "Significant peak-to-trough"],
        ["Volatility Regime", "HIGH", "Position sizing: 2-5% max"],
    ]
    story.append(create_table(vol_data, [2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Risk Metrics (252-Day vs SPY)</b>", styles['SubHeading']))
    risk_data = [
        ["Metric", "Value", "Interpretation"],
        ["Sharpe Ratio", "1.77", "Good risk-adjusted returns"],
        ["Sortino Ratio", "2.68", "Excellent downside-adjusted"],
        ["Beta", "0.88", "Slightly less volatile than market"],
        ["Alpha", "+91.60%", "Massive outperformance vs SPY"],
        ["95% VaR (Daily)", "-5.40%", "95% of days, losses < 5.4%"],
        ["95% CVaR", "-7.97%", "Tail risk: avg 8% when breached"],
    ]
    story.append(create_table(risk_data, [2*inch, 1.5*inch, 3*inch]))

    story.append(PageBreak())

    # ========== Q3 2025 EARNINGS ==========
    story.append(Paragraph("5. Q3 2025 Earnings Summary", styles['SectionHeading']))

    earnings_data = [
        ["Metric", "Q3 2025", "Q3 2024", "YoY Change"],
        ["Net Income", "$262.6M", "$7.5M", "+3,401%"],
        ["EPS (Diluted)", "$5.16", "$0.13", "+3,869%"],
        ["Adj. Net Income", "$302.6M", "$(5.5)M", "N/M"],
        ["Adj. EPS", "$5.95", "N/A", "N/M"],
        ["Adj. EBITDA", "$372.5M", "$51.4M", "+625%"],
        ["SRE Impact", "$195.9M", "$0", "One-time"],
    ]
    story.append(create_table(earnings_data, [1.8*inch, 1.5*inch, 1.5*inch, 1.7*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>CRITICAL NOTE:</b> The Q3 beat was heavily driven by a one-time Small Refinery Exemption (SRE) "
        "from the EPA worth ~$196M. This is NON-RECURRING and should not be extrapolated to future quarters.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== AI/BITCOIN THESIS ==========
    story.append(Paragraph("6. AI/Bitcoin Energy Thesis Assessment", styles['SectionHeading']))

    story.append(Paragraph("<b>Why PARR Does NOT Fit the AI Energy Theme:</b>", styles['SubHeading']))

    ai_data = [
        ["What AI Data Centers Need", "What PARR Provides", "Fit?"],
        ["Electricity (24/7 baseload)", "Transportation fuels", "NO"],
        ["Natural gas (on-site generation)", "Refined petroleum", "NO"],
        ["Nuclear power", "Not applicable", "NO"],
        ["Renewable electricity", "SAF/renewable diesel (transport)", "NO"],
    ]
    story.append(create_table(ai_data, [2.3*inch, 2.3*inch, 1.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Better AI Energy Plays:</b>", styles['SubHeading']))
    alt_data = [
        ["Ticker", "Company", "Why It Fits"],
        ["VST", "Vistra Corp", "Natural gas + nuclear power generator"],
        ["CEG", "Constellation Energy", "Largest US nuclear fleet"],
        ["ET", "Energy Transfer", "Natural gas pipelines to data centers"],
        ["CCJ", "Cameco", "Uranium producer for nuclear"],
        ["NEE", "NextEra Energy", "Renewable power developer"],
        ["PWR", "Quanta Services", "Grid infrastructure buildout"],
    ]
    story.append(create_table(alt_data, [1*inch, 2*inch, 3.5*inch]))

    story.append(PageBreak())

    # ========== STRATEGY RECOMMENDATIONS ==========
    story.append(Paragraph("7. Strategy Recommendations", styles['SectionHeading']))

    story.append(Paragraph("<b>Suitability Assessment</b>", styles['SubHeading']))
    suit_data = [
        ["Investment Strategy", "Suitability", "Rationale"],
        ["Layer 1 (Growth)", "Possible", "Hawaii moat + operational excellence"],
        ["Layer 2 (Income)", "NOT SUITABLE", "No dividend paid"],
        ["AI/Bitcoin Energy Play", "NOT SUITABLE", "Produces transport fuels, not electricity"],
        ["Value Investing", "Possible", "Above analyst targets but strong fundamentals"],
        ["Momentum Trading", "Caution", "Mixed technical signals, MACD bearish"],
    ]
    story.append(create_table(suit_data, [2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Primary Recommendation:</b>", styles['SubHeading']))
    story.append(Paragraph(
        "Do not add PARR to Layer 2 income portfolio—no dividend yield. Current price ($43.29) exceeds most "
        "analyst targets ($32-40), suggesting limited near-term upside unless crack spreads improve.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== RISK & COMPLIANCE ==========
    story.append(Paragraph("8. Risk & Compliance Review", styles['SectionHeading']))

    story.append(Paragraph("<b>Key Risks</b>", styles['SubHeading']))
    risk_table_data = [
        ["Risk Category", "Description", "Severity"],
        ["Commodity Cyclicality", "Crack spread compression impacts margins", "HIGH"],
        ["SRE Uncertainty", "Q3 $196M benefit is one-time", "MEDIUM"],
        ["Concentration", "Hawaii represents largest profit center", "MEDIUM"],
        ["Volatility", "55% annual vol, -33% max drawdown", "HIGH"],
        ["Valuation", "Trading above analyst targets", "MEDIUM"],
    ]
    story.append(create_table(risk_table_data, [1.8*inch, 3*inch, 1.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Limitations & Open Questions</b>", styles['SubHeading']))
    limitations = [
        "• Normalized Earnings: Q3 results distorted by $196M SRE—true run-rate profitability unclear until Q4",
        "• Crack Spread Outlook: Forward crack spread environment uncertain",
        "• Renewables Execution: Hawaii Renewables JV operational success not yet proven",
        "• Analyst Coverage: Limited coverage (5 analysts) may create information inefficiency",
    ]
    for item in limitations:
        story.append(Paragraph(item, styles['BulletPoint']))

    story.append(PageBreak())

    # ========== SOURCES ==========
    story.append(Paragraph("9. Sources & Data", styles['SectionHeading']))

    sources_data = [
        ["Source", "Data Used", "Date"],
        ["Yahoo Finance (yfinance)", "Price data, market data", "Dec 9, 2025"],
        ["Par Pacific IR", "Q3 2025 earnings, business description", "Nov 4, 2025"],
        ["Par Pacific Website", "Business segment details", "Dec 9, 2025"],
        ["Seeking Alpha", "Analyst commentary", "Dec 5, 2025"],
        ["MarketBeat", "Analyst ratings, institutional activity", "Dec 9, 2025"],
        ["Finance Guru CLI Tools", "Technical analysis, risk metrics", "Dec 9, 2025"],
    ]
    story.append(create_table(sources_data, [2*inch, 2.5*inch, 2*inch]))

    story.append(Spacer(1, 0.5*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
    story.append(Spacer(1, 0.2*inch))

    # Footer
    footer_text = """<b>COMPLIANCE DISCLAIMERS</b><br/>
    • Educational Analysis: This report is for educational purposes only and does not constitute personalized investment advice.<br/>
    • No Guarantee: Past performance does not guarantee future results. All investments involve risk of loss.<br/>
    • Professional Advice: Consult a licensed financial advisor before making any investment decisions.<br/><br/>
    <b>Report ID:</b> PARR-2025-12-09-001 | <b>Version:</b> 1.0.0<br/>
    Generated by Finance Guru™ v2.0.0 | BMAD-CORE™ v6.0.0<br/>
    December 9, 2025"""
    story.append(Paragraph(footer_text, styles['Footer']))

    # Build the PDF
    doc.build(story)
    print(f"✅ PDF Report generated: {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    build_report()
