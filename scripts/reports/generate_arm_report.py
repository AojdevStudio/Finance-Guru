#!/usr/bin/env python3
"""
Generate ARM Holdings Analysis Report PDF
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
OUTPUT_DIR = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "ARM-analysis-2025-12-18.pdf")

# Ensure directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors - Finance Guru Branding
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

    # Body text
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
    story.append(Paragraph("ARM Holdings (ARM)", styles['ReportTitle']))
    story.append(Paragraph("2026 Watchlist Analysis", styles['ReportSubtitle']))
    story.append(Spacer(1, 0.5*inch))

    # Cover info table
    cover_data = [
        ["Prepared For:", "Ossie Irondi - Private Family Office"],
        ["Prepared By:", "Finance Guru™ Multi-Agent Team"],
        ["Date:", "December 18, 2025"],
        ["Data As Of:", "December 17, 2025 (Market Close)"],
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
    Past performance does not guarantee future results. All investments carry risk of loss. Consult a
    licensed financial advisor before making investment decisions."""
    story.append(Paragraph(disclaimer_text, styles['Disclaimer']))

    story.append(PageBreak())

    # ========== EXECUTIVE SUMMARY ==========
    story.append(Paragraph("1. Executive Summary", styles['SectionHeading']))

    story.append(Paragraph("<b>Investment Thesis</b>", styles['SubHeading']))
    story.append(Paragraph(
        "ARM Holdings (NASDAQ: ARM) is the dominant CPU architecture designer powering 99%+ of smartphones and "
        "rapidly expanding into data centers and AI infrastructure. The company's royalty-based business model "
        "provides leverage to secular growth in AI computing, with higher royalty rates from next-generation "
        "Armv9 designs and compute subsystems (CSS) commanding 2-4x the rates of legacy architectures.",
        styles['BodyText']
    ))

    story.append(Paragraph("<b>Key Findings</b>", styles['SubHeading']))
    findings = [
        "• <b>Financial Momentum:</b> Q2 FY2026 revenue of $1.14B (↑34% YoY), driven by 56% licensing growth and 21% royalty growth. Third consecutive quarter above $1B.",
        "• <b>AI Positioning:</b> Data center royalties doubled YoY. ARM expects 50% market share of hyperscaler CPUs by 2025, up from ~15-20% royalty mix.",
        "• <b>Premium Pricing Power:</b> Armv9 commands 2x royalty vs Armv8; CSS commands 2x Armv9. Migration to higher-value IP accelerating.",
        "• <b>Strategic Pivot:</b> ARM announced plans to design its own AI accelerator chips for data centers (FY2027+ revenue), entering direct competition with some customers.",
        "• <b>Risk Profile:</b> EXTREME volatility (61.87% annual), -52.3% max drawdown, negative Sharpe ratio (-0.06), massive underperformance vs SPY (Alpha: -22.74%).",
    ]
    for finding in findings:
        story.append(Paragraph(finding, styles['BulletPoint']))

    story.append(Paragraph("<b>Current Technical Posture</b>", styles['SubHeading']))
    story.append(Paragraph(
        "ARM is deeply oversold across all momentum indicators (RSI: 23.39, Williams %R: -93.83, Stochastic: 6.17) "
        "with 3/5 bullish confluence signals. Price is trading below the lower Bollinger Band ($113.51 vs $115.94), "
        "suggesting potential mean reversion opportunity—but MACD remains bearish with negative momentum.",
        styles['BodyText']
    ))

    story.append(Paragraph("<b>Verdict: CONDITIONAL BUY</b>", styles['SubHeading']))
    verdict_data = [
        ["Rating", "CONDITIONAL BUY (Speculative Growth)"],
        ["Confidence", "MODERATE - High execution risk, extreme volatility"],
        ["Position Size", "2-3% maximum (High volatility regime)"],
        ["Time Horizon", "12-24 months (2026-2027)"],
        ["Catalyst Dependency", "HIGH - Requires AI adoption, Qualcomm resolution, chip execution"],
    ]
    story.append(create_table(verdict_data, [2*inch, 4.5*inch], header=False))

    story.append(PageBreak())

    # ========== COMPANY OVERVIEW ==========
    story.append(Paragraph("2. Company Overview", styles['SectionHeading']))

    overview_data = [
        ["Attribute", "Details"],
        ["Full Name", "ARM Holdings plc"],
        ["Ticker", "NASDAQ: ARM"],
        ["Headquarters", "Cambridge, United Kingdom"],
        ["Sector", "Technology - Semiconductors (IP Licensing)"],
        ["Market Cap", "~$115 billion (Dec 18, 2025)"],
        ["Current Price", "$113.51 (-0.93% / -$1.07)"],
        ["52-Week Range", "$80.23 - $188.75"],
        ["IPO Date", "September 14, 2023 (Re-IPO)"],
    ]
    story.append(create_table(overview_data, [2*inch, 4.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Business Model: The Architecture Royalty Machine</b>", styles['SubHeading']))
    story.append(Paragraph(
        "ARM does NOT manufacture chips. Instead, it licenses intellectual property (CPU architecture designs, IP blocks, "
        "development tools) to semiconductor companies and device manufacturers. Revenue comes from:",
        styles['BodyText']
    ))

    revenue_data = [
        ["Revenue Stream", "Description", "Characteristics"],
        ["Licensing Fees", "Upfront payments for IP access ($1M-$10M per license)", "Fixed, predictable, recognize upfront"],
        ["Royalties", "1-2% of chip selling price for each unit shipped", "Variable, scalable, recurring"],
        ["Top Customers", "Apple, Qualcomm, Samsung, MediaTek, NVIDIA, AWS", "56% revenue from top 5 (inc. Arm China)"],
    ]
    story.append(create_table(revenue_data, [1.5*inch, 2.5*inch, 2.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Competitive Positioning</b>", styles['SubHeading']))
    story.append(Paragraph(
        "<b>Dominant in Mobile:</b> ARM powers 99%+ of smartphones globally (iPhone, Android, all use ARM architecture). "
        "This is a mature, stable royalty base.<br/><br/>"
        "<b>Expanding in Data Centers:</b> AWS Graviton, Google Axion, Microsoft Cobalt, NVIDIA Grace—all ARM-based. "
        "Data center royalties doubled YoY and now represent 15-20% of total royalties (up from 10%).<br/><br/>"
        "<b>AI Acceleration:</b> Armv9 architecture optimized for AI workloads. Compute Subsystems (CSS) are pre-integrated "
        "IP blocks that command 2x royalty vs Armv9 alone (4x vs legacy Armv8).",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== FINANCIAL PERFORMANCE ==========
    story.append(Paragraph("3. Financial Performance", styles['SectionHeading']))

    story.append(Paragraph("<b>Q2 FY2026 Earnings (Sept 30, 2025)</b>", styles['SubHeading']))
    earnings_data = [
        ["Metric", "Q2 FY2026", "Q2 FY2025", "YoY Growth"],
        ["Total Revenue", "$1.14B", "$850M", "+34%"],
        ["Royalty Revenue", "$620M", "$512M", "+21%"],
        ["License Revenue", "$550M", "$352M", "+56%"],
        ["Q3 Guidance (Midpoint)", "$1.225B", "—", "+22% projected"],
    ]
    story.append(create_table(earnings_data, [2*inch, 1.5*inch, 1.5*inch, 1.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>FY2025-2028 Growth Projections</b>", styles['SubHeading']))
    story.append(Paragraph(
        "Analysts expect 20% revenue CAGR and 34% EPS CAGR from FY2025 to FY2028 as AI chip sales accelerate. "
        "This assumes continued migration to Armv9, CSS adoption, and data center penetration.",
        styles['BodyText']
    ))

    story.append(Paragraph("<b>Royalty Rate Expansion Strategy</b>", styles['SubHeading']))
    royalty_data = [
        ["Architecture/Product", "Royalty Rate vs Armv8 Baseline", "Status"],
        ["Armv8 (Legacy)", "1x (baseline)", "Mature, declining share"],
        ["Armv9 (AI-optimized)", "2x", "Rapid adoption across mobile/DC"],
        ["Compute Subsystems (CSS)", "4x (2x Armv9)", "Premium offering, double royalty"],
        ["Own AI Chips (2027+)", "N/A (direct revenue)", "Announced, in development"],
    ]
    story.append(create_table(royalty_data, [2*inch, 2.5*inch, 2*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Price Hike Plans:</b> ARM is pursuing a long-term strategy to increase smartphone revenue by ~$1B/decade "
        "via higher per-chip royalty rates. However, sophisticated customers like Apple and Qualcomm design from scratch "
        "using architectural licenses, potentially avoiding some rate increases.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== QUANTITATIVE ANALYSIS ==========
    story.append(Paragraph("4. Quantitative Analysis", styles['SectionHeading']))

    story.append(Paragraph("<b>Risk Metrics (252-Day vs SPY)</b>", styles['SubHeading']))
    risk_data = [
        ["Metric", "Value", "Interpretation", "Rating"],
        ["Sharpe Ratio", "-0.06", "Negative risk-adjusted returns", "POOR"],
        ["Sortino Ratio", "-0.10", "Negative downside-adjusted returns", "POOR"],
        ["Beta", "2.22", "2.2x more volatile than SPY", "HIGH RISK"],
        ["Alpha", "-22.74%", "Massive underperformance vs SPY", "VERY POOR"],
        ["95% VaR (Daily)", "-5.52%", "95% of days, losses < 5.52%", "HIGH"],
        ["95% CVaR", "-8.22%", "Tail risk: 8.22% when VaR breached", "HIGH"],
        ["Max Drawdown", "-52.30%", "Peak-to-trough worst decline", "EXTREME"],
        ["Calmar Ratio", "0.01", "Very low return/drawdown", "POOR"],
    ]
    story.append(create_table(risk_data, [1.5*inch, 1.3*inch, 2.2*inch, 1.5*inch]))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "<b>CRITICAL INSIGHT:</b> ARM has exhibited catastrophic risk-adjusted performance over the past year, with "
        "Beta of 2.22 (highly leveraged to market moves) and Alpha of -22.74% (massive systematic underperformance). "
        "The -52.3% max drawdown reflects severe volatility. This is NOT a stable, low-risk investment.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Volatility Profile (90-Day)</b>", styles['SubHeading']))
    vol_data = [
        ["Metric", "Value", "Assessment"],
        ["Annual Volatility", "61.87% (Daily: 39.27%)", "EXTREME - Top decile"],
        ["Volatility Regime", "HIGH", "Reduce position sizes to 2-5%"],
        ["ATR (14)", "$5.98 (5.27% of price)", "Significant daily swings"],
        ["ATR Stop Loss (2x)", "$11.96", "Suggested risk management level"],
        ["Bollinger %B", "-0.072", "Price below lower band (oversold)"],
        ["Bandwidth", "25.31%", "Wide bands confirm high volatility"],
    ]
    story.append(create_table(vol_data, [2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Momentum Indicators (90-Day)</b>", styles['SubHeading']))
    momentum_data = [
        ["Indicator", "Value", "Signal", "Interpretation"],
        ["RSI (14)", "23.39", "OVERSOLD", "Potential buy signal (< 30)"],
        ["MACD Line", "-6.52", "BEARISH", "Below signal line"],
        ["MACD Signal", "-5.02", "—", "Downward momentum"],
        ["Histogram", "-1.50", "BEARISH", "Negative divergence"],
        ["Stochastic %K", "6.17", "OVERSOLD", "Extreme oversold (< 20)"],
        ["Stochastic %D", "8.12", "OVERSOLD", "Potential reversal up"],
        ["Williams %R", "-93.83", "OVERSOLD", "Extreme oversold (< -80)"],
        ["ROC", "-15.13%", "BEARISH", "Negative momentum"],
    ]
    story.append(create_table(momentum_data, [1.5*inch, 1.3*inch, 1.3*inch, 2.4*inch]))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "<b>Momentum Confluence: 3 Bullish / 2 Bearish (STRONG BULLISH CONFLUENCE)</b><br/>"
        "Three oversold indicators (RSI, Stochastic, Williams %R) suggest potential mean reversion, but MACD and ROC "
        "remain bearish. This creates a mixed technical picture: oversold conditions may signal a bounce, but downward "
        "momentum persists.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Portfolio Correlation Analysis</b>", styles['SubHeading']))
    corr_data = [
        ["Asset Pair", "Correlation", "Assessment"],
        ["ARM / VOO", "+0.710", "VERY HIGH - Limited diversification"],
        ["ARM / NVDA", "+0.671", "HIGH - Sector correlation"],
        ["ARM / TSLA", "+0.525", "MODERATE - Some diversification"],
        ["ARM / PLTR", "+0.468", "MODERATE - Best diversification in portfolio"],
    ]
    story.append(create_table(corr_data, [2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "<b>Diversification Score: 0.398 (MODERATE)</b><br/>"
        "ARM exhibits high correlation with VOO (+0.710) and NVDA (+0.671), limiting diversification benefits. Adding "
        "ARM to a tech-heavy portfolio (PLTR, TSLA, NVDA, VOO) provides marginal diversification and increases concentration "
        "risk in semiconductor/AI exposure.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== STRATEGIC CATALYSTS ==========
    story.append(Paragraph("5. Strategic Catalysts & Risks", styles['SectionHeading']))

    story.append(Paragraph("<b>2026 Growth Catalysts</b>", styles['SubHeading']))
    catalysts = [
        "• <b>Data Center Penetration:</b> ARM targeting 50% market share of hyperscaler CPUs by end of 2025. AWS Graviton, Google Axion, Microsoft Cobalt all ramping.",
        "• <b>Armv9 Migration:</b> Higher royalty rates (2x Armv8) as mobile and DC customers adopt AI-optimized architecture.",
        "• <b>CSS Adoption:</b> Compute Subsystems command 4x royalty vs Armv8. Customers paying premium for pre-integrated IP.",
        "• <b>South Korea Partnership:</b> December 2025 agreement for ARM School to train 1,400 chip designers (2026-2030), expanding ecosystem.",
        "• <b>Own Chip Revenue (FY2027+):</b> Server-class AI accelerators for hyperscale data centers. Jefferies expects material revenue by FY2027.",
        "• <b>Smartphone Recovery:</b> Global smartphone market stabilizing after multi-year decline. Royalty base expanding.",
    ]
    for catalyst in catalysts:
        story.append(Paragraph(catalyst, styles['BulletPoint']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Key Risks</b>", styles['SubHeading']))
    risk_table_data = [
        ["Risk Category", "Description", "Severity"],
        ["Valuation", "P/E ~180x (FY2025), 80x (FY2026), 60x (FY2027) — premium priced", "HIGH"],
        ["RISC-V Competition", "Open-source architecture at 10.4% penetration (2024), could reach 20%+ by 2027", "MEDIUM-HIGH"],
        ["Qualcomm Litigation", "Ongoing lawsuit re: Nuvia license breach, trial set for March 2026", "MEDIUM"],
        ["Customer Concentration", "56% revenue from top 5 customers — Apple/Qualcomm dependency", "MEDIUM"],
        ["Own Chip Cannibalization", "Competing with customers (e.g., AWS, NVIDIA) may strain relationships", "MEDIUM"],
        ["Volatility", "61.87% annual volatility, -52.3% max drawdown — extreme price swings", "EXTREME"],
        ["Macro Sensitivity", "Beta 2.22 — highly leveraged to market downturns", "HIGH"],
        ["Goldman Downgrade (Dec 18)", "Analyst concerns about valuation, near-term catalysts", "MEDIUM"],
    ]
    story.append(create_table(risk_table_data, [1.8*inch, 3*inch, 1.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Competitive Landscape</b>", styles['SubHeading']))
    story.append(Paragraph(
        "<b>Primary Threat: RISC-V</b><br/>"
        "RISC-V is an open-standard CPU architecture that requires no licensing fees or royalties. It reached 10.4% "
        "market penetration by chip value in 2024 and is gaining traction in AI/edge computing. If adoption accelerates, "
        "ARM's pricing power and market share could erode. However, ARM's ecosystem maturity (software, tools, developer "
        "base) provides a significant moat.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== STRATEGY RECOMMENDATIONS ==========
    story.append(Paragraph("6. Strategy Recommendations", styles['SectionHeading']))

    story.append(Paragraph("<b>Investment Verdict: CONDITIONAL BUY (Speculative Growth)</b>", styles['SubHeading']))

    verdict_table = [
        ["Factor", "Assessment"],
        ["Overall Rating", "CONDITIONAL BUY"],
        ["Conviction Level", "MODERATE (60/100)"],
        ["Position Size", "2-3% of portfolio (high volatility regime)"],
        ["Time Horizon", "12-24 months (2026-2027 catalysts)"],
        ["Risk Profile", "AGGRESSIVE - Extreme volatility, high beta"],
    ]
    story.append(create_table(verdict_table, [2*inch, 4.5*inch], header=False))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Rationale</b>", styles['SubHeading']))
    story.append(Paragraph(
        "ARM is a <b>high-conviction AI infrastructure play wrapped in a high-beta, high-multiple stock</b>. The business "
        "fundamentals are exceptional: dominant market position, expanding into data centers, premium pricing power via "
        "Armv9/CSS, and direct exposure to AI compute buildout. However, the stock is:<br/><br/>"
        "1. <b>Extremely volatile</b> (61.87% annual volatility, -52.3% max drawdown)<br/>"
        "2. <b>Richly valued</b> (P/E ~180x, though falling to 60x by 2027 if forecasts hold)<br/>"
        "3. <b>Heavily correlated</b> with your existing holdings (VOO +0.710, NVDA +0.671)<br/>"
        "4. <b>Facing execution risks</b> (Qualcomm litigation, own chip strategy, RISC-V competition)<br/><br/>"
        "The recent selloff has pushed ARM into deeply oversold territory (RSI 23.39, Williams %R -93.83), creating a "
        "potential mean reversion opportunity. However, MACD remains bearish, indicating caution.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Entry Strategy</b>", styles['SubHeading']))
    entry_data = [
        ["Approach", "Details"],
        ["Position Size", "2-3% maximum (high volatility regime, diversification concerns)"],
        ["Entry Method", "Scaled entry via 2-3 tranches over 4-8 weeks"],
        ["Initial Tranche", "1% at current levels (~$113) — oversold bounce play"],
        ["Second Tranche", "1% on pullback to $105-108 OR breakout above $120 (MACD cross)"],
        ["Third Tranche", "0.5-1% if Qualcomm resolution or FY2027 chip traction confirmed"],
        ["Stop Loss", "2x ATR = $11.96 below entry (~$101 from current $113)"],
        ["Take Profit Target", "$150-160 (mean reversion to 50-day MA zone)"],
        ["Long-term Target", "$180-200 (Jefferies target, requires AI thesis validation)"],
    ]
    story.append(create_table(entry_data, [2*inch, 4.5*inch], header=False))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Risk Management</b>", styles['SubHeading']))
    risk_mgmt = [
        "• <b>Position Limit:</b> Do NOT exceed 3% of portfolio given 61.87% volatility and 2.22 beta.",
        "• <b>Correlation Hedge:</b> Consider reducing NVDA position if adding ARM to avoid over-concentration in semiconductor exposure.",
        "• <b>Stop Loss Discipline:</b> Use 2x ATR stop ($11.96 below entry) or 15% trailing stop, whichever is tighter.",
        "• <b>Catalyst Dependency:</b> If Qualcomm litigation resolves negatively OR RISC-V adoption accelerates, exit immediately.",
        "• <b>Valuation Monitor:</b> If P/E remains above 100x into 2026 without earnings acceleration, re-evaluate.",
    ]
    for item in risk_mgmt:
        story.append(Paragraph(item, styles['BulletPoint']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Fit with Portfolio Strategy</b>", styles['SubHeading']))
    fit_data = [
        ["Strategy Layer", "Fit", "Rationale"],
        ["Layer 1 (Growth)", "GOOD", "AI infrastructure exposure, 20%+ revenue growth"],
        ["Layer 2 (Income)", "NOT SUITABLE", "No dividend, extreme volatility"],
        ["Diversification", "POOR", "High correlation with VOO (+0.71), NVDA (+0.67)"],
        ["Tech/AI Exposure", "EXCELLENT", "Pure-play AI compute infrastructure via royalties"],
        ["Risk Budget", "CAUTION", "Extreme volatility consumes significant risk budget"],
    ]
    story.append(create_table(fit_data, [2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Alternative Consideration</b>", styles['SubHeading']))
    story.append(Paragraph(
        "Given ARM's extreme volatility (61.87%) and high correlation with existing holdings, consider whether incremental "
        "exposure to NVDA (which you already own) or a basket of semiconductor ETF (e.g., SOXX, SMH) provides similar AI "
        "upside with better diversification. ARM is a concentrated bet on CPU architecture licensing—NVDA offers broader "
        "AI infrastructure exposure (GPUs, networking, software).",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== FINAL VERDICT ==========
    story.append(Paragraph("7. Final Verdict & Action Items", styles['SectionHeading']))

    story.append(Paragraph("<b>Recommendation: CONDITIONAL BUY</b>", styles['SubHeading']))
    story.append(Paragraph(
        "ARM Holdings is a <b>high-quality business at a high-volatility price</b>. The company's dominance in mobile "
        "CPU architecture, rapid expansion into data centers, and premium pricing power via Armv9/CSS position it as a "
        "compelling AI infrastructure play. Q2 FY2026 results (+34% revenue growth) validate the growth thesis.<br/><br/>"
        "However, the stock's extreme volatility (61.87%), negative risk-adjusted returns (Sharpe -0.06, Alpha -22.74%), "
        "and -52.3% max drawdown demand disciplined position sizing and risk management. The current oversold technical "
        "setup (RSI 23.39) creates a potential entry opportunity, but MACD remains bearish.<br/><br/>"
        "<b>This is NOT a core holding</b>—it is a <b>speculative growth allocation</b> with 12-24 month time horizon, "
        "dependent on AI adoption, Qualcomm resolution, and execution of the own-chip strategy.",
        styles['BodyText']
    ))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Action Items</b>", styles['SubHeading']))
    actions = [
        "• <b>IMMEDIATE:</b> If adding ARM, start with 1% position at current levels (~$113) to capture oversold bounce.",
        "• <b>WEEK 2-4:</b> Add second 1% tranche on pullback to $105-108 OR breakout above $120 with MACD bullish cross.",
        "• <b>Q1 2026:</b> Monitor Qualcomm trial (March 2026). Exit if outcome is materially negative for ARM.",
        "• <b>Q2 2026:</b> Evaluate Q3/Q4 FY2026 earnings. If royalty growth slows below 15% or data center momentum stalls, reduce position.",
        "• <b>FY2027:</b> Assess own-chip revenue contribution. If material ($100M+ quarterly), consider adding third tranche.",
        "• <b>ONGOING:</b> Set 2x ATR stop loss ($11.96) or 15% trailing stop. Review monthly for risk management.",
    ]
    for action in actions:
        story.append(Paragraph(action, styles['BulletPoint']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Watch List Status</b>", styles['SubHeading']))
    watchlist_data = [
        ["Attribute", "Rating"],
        ["2026 Watchlist Status", "APPROVED - Conditional Buy"],
        ["Priority", "TIER 2 (Speculative Growth)"],
        ["Monitoring Frequency", "Monthly (or after major news/earnings)"],
        ["Re-Evaluation Triggers", "Qualcomm verdict, FY2026 Q3/Q4 earnings, RISC-V share >15%, own chip launch"],
    ]
    story.append(create_table(watchlist_data, [2.5*inch, 4*inch], header=False))

    story.append(PageBreak())

    # ========== SOURCES ==========
    story.append(Paragraph("8. Sources & Data", styles['SectionHeading']))

    sources_data = [
        ["Source", "Data Used", "Date"],
        ["Yahoo Finance (yfinance)", "Price data, historical market data", "Dec 18, 2025"],
        ["ARM Holdings IR", "Q2 FY2026 earnings, business metrics", "Nov 5, 2025"],
        ["TS2 Tech News", "Goldman downgrade, 2026 forecasts, South Korea partnership", "Dec 6-18, 2025"],
        ["Investing.com", "Earnings call transcript, Q2 analysis", "Nov 2025"],
        ["The Motley Fool", "Strategic analysis, own chip plans, Q2/Q3 commentary", "Nov-Dec 2025"],
        ["WebProNews", "Data center market share predictions", "Dec 2025"],
        ["Simply Wall St", "Growth partnerships, rally analysis", "Dec 2025"],
        ["MarketBeat", "Analyst targets, institutional activity", "Dec 2025"],
        ["Finance Guru CLI Tools", "Risk metrics, momentum, volatility, correlation", "Dec 18, 2025"],
    ]
    story.append(create_table(sources_data, [2*inch, 2.5*inch, 1.5*inch]))

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("<b>Web Sources</b>", styles['SubHeading']))
    web_sources = [
        "• <font size='8'>https://ts2.tech/en/arm-holdings-stock-nasdaq-arm-news-today-goldman-downgrade-ai-momentum-and-fresh-2026-forecasts-dec-18-2025/</font>",
        "• <font size='8'>https://www.investing.com/news/transcripts/earnings-call-transcript-arms-q2-2025-revenue-jumps-34-amid-ai-surge-93CH-4335848</font>",
        "• <font size='8'>https://www.webpronews.com/arm-holdings-ceo-predicts-50-data-center-cpu-market-share-by-2025/</font>",
        "• <font size='8'>https://www.fool.com/investing/2025/11/10/arm-beats-estimates-but-its-new-plan-to-build-chip/</font>",
        "• <font size='8'>https://www.fool.com/investing/2025/12/06/is-arm-stock-a-buying-opportunity-for-2026/</font>",
        "• <font size='8'>https://simplywall.st/stocks/us/semiconductors/nasdaq-arm/arm-holdings/news/does-arm-holdings-33-rally-in-2025-match-its-latest-growth-p</font>",
    ]
    for source in web_sources:
        story.append(Paragraph(source, styles['BulletPoint']))

    story.append(Spacer(1, 0.5*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
    story.append(Spacer(1, 0.2*inch))

    # Footer
    footer_text = """<b>COMPLIANCE DISCLAIMERS</b><br/>
    • <b>Educational Analysis:</b> This report is for educational purposes only and does not constitute personalized investment advice.<br/>
    • <b>No Guarantee:</b> Past performance does not guarantee future results. All investments involve risk of loss, including total loss of principal.<br/>
    • <b>Professional Advice:</b> Consult a licensed financial advisor, tax professional, and legal counsel before making any investment decisions.<br/>
    • <b>Accuracy:</b> While efforts are made to ensure accuracy, no warranty is provided. Data may contain errors or omissions.<br/><br/>
    <b>Report ID:</b> ARM-2025-12-18-001 | <b>Version:</b> 1.0.0<br/>
    Generated by Finance Guru™ v2.0.0 | BMAD-CORE™ v6.0.0<br/>
    December 18, 2025"""
    story.append(Paragraph(footer_text, styles['Footer']))

    # Build the PDF
    doc.build(story)
    print(f"✅ PDF Report generated: {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    build_report()
