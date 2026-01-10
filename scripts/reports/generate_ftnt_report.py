#!/usr/bin/env python3
"""
FTNT (Fortinet Inc.) Comprehensive Analysis Report Generator
Finance Guru™ - Private Family Office Analysis
Generated: 2025-12-18
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from datetime import datetime

def create_ftnt_report():
    """Generate comprehensive FTNT analysis PDF report"""

    output_path = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports/FTNT-analysis-2025-12-18.pdf"

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for PDF elements
    story = []

    # Define custom styles
    styles = getSampleStyleSheet()

    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    # Subtitle style
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
        alignment=TA_CENTER
    )

    # Section heading style
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    # Subsection heading style
    subsection_style = ParagraphStyle(
        'SubsectionHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )

    # Body text style
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8,
        alignment=TA_JUSTIFY
    )

    # Bullet style
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        leftIndent=20,
        spaceAfter=6
    )

    # ============================================================
    # TITLE PAGE
    # ============================================================

    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("FORTINET INC. (FTNT)", title_style))
    story.append(Paragraph("Comprehensive Investment Analysis for 2026 Watchlist", subtitle_style))
    story.append(Spacer(1, 0.3*inch))

    # Branding
    brand_text = """
    <para align=center>
    <b>Finance Guru™</b><br/>
    Private Family Office Analysis<br/>
    Prepared for: Ossie Irondi<br/>
    Report Date: December 18, 2025
    </para>
    """
    story.append(Paragraph(brand_text, body_style))
    story.append(Spacer(1, 0.5*inch))

    # Executive Summary Box
    exec_summary_data = [
        ['EXECUTIVE SUMMARY'],
        ['Current Price:', '$79.75'],
        ['Market Cap:', '$66.60B'],
        ['Industry:', 'Cybersecurity / Network Security'],
        ['Analyst Rating:', 'BUY (6.6/10)'],
        ['Price Target (Avg):', '$91.90 (+15.2%)'],
        ['Risk Tolerance:', 'Aggressive (Tech-Heavy Portfolio)']
    ]

    exec_table = Table(exec_summary_data, colWidths=[3*inch, 3*inch])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f9f9f9'), colors.white])
    ]))

    story.append(exec_table)
    story.append(PageBreak())

    # ============================================================
    # PHASE 1: MARKET RESEARCH & COMPANY OVERVIEW
    # ============================================================

    story.append(Paragraph("PHASE 1: MARKET RESEARCH & COMPANY OVERVIEW", section_style))
    story.append(Paragraph("Agent: Dr. Aleksandr Petrov (Market Researcher)", subsection_style))

    company_overview = """
    <b>Company Profile:</b> Fortinet Inc. (NASDAQ: FTNT) is a global leader in cybersecurity solutions,
    specializing in next-generation firewalls, unified threat management, and integrated security
    platforms. The company differentiates itself through proprietary custom chip technology (FortiASIC)
    that delivers superior performance-per-watt and lower total cost of ownership compared to competitors.
    """
    story.append(Paragraph(company_overview, body_style))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("Key Products & Solutions:", subsection_style))
    products = [
        "• <b>FortiGate Firewalls:</b> Core hardware product line with major refresh cycle expected late 2025-2026",
        "• <b>Unified SASE (Secure Access Service Edge):</b> Cloud-delivered security, 85% YoY growth in Q4 2024",
        "• <b>FortiAI Security Operations Center:</b> AI-powered autonomous threat hunting (launched June 2025)",
        "• <b>SD-WAN Solutions:</b> Software-defined wide area networking with integrated security",
        "• <b>Security Fabric:</b> End-to-end integrated security platform spanning network, endpoint, cloud"
    ]
    for item in products:
        story.append(Paragraph(item, bullet_style))

    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("Competitive Position:", subsection_style))
    competitive_text = """
    Fortinet operates in the highly competitive cybersecurity market alongside CrowdStrike (CRWD),
    Palo Alto Networks (PANW), and Check Point. The company holds a strong position in the traditional
    firewall market while aggressively expanding into cloud-native SASE solutions. Unlike CrowdStrike's
    pure cloud-based approach, Fortinet offers a hybrid model combining on-premise appliances with cloud
    services, providing flexibility for enterprises with mixed infrastructure needs.
    """
    story.append(Paragraph(competitive_text, body_style))

    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("2026 Catalysts:", subsection_style))
    catalysts = [
        "• <b>FortiGate Hardware Refresh Cycle:</b> Expected to accelerate in late 2025 through 2026, driving product revenue growth",
        "• <b>SASE Market Expansion:</b> Unified SASE billings grew 13% in Q4 2024, now 23% of total business",
        "• <b>AI-Powered Security:</b> FortiAI autonomous threat hunting reducing manual intervention and operational costs",
        "• <b>Proprietary Chip Advantage:</b> FortiASIC technology provides cost and performance edge in large enterprise deals",
        "• <b>Subscription Revenue Growth:</b> High-margin recurring revenue from security services increasing to 70%+ of total revenue"
    ]
    for item in catalysts:
        story.append(Paragraph(item, bullet_style))

    story.append(PageBreak())

    # ============================================================
    # FINANCIAL PERFORMANCE
    # ============================================================

    story.append(Paragraph("Financial Performance & Outlook", section_style))

    # Revenue table
    revenue_data = [
        ['Metric', 'Q3 2025', 'TTM (Sept 2025)', 'FY 2025E'],
        ['Revenue', '$1.72B', '$6.55B', '$6.65-6.85B'],
        ['YoY Growth', '+14.4%', '+14.8%', '+12-15%'],
        ['Service Revenue', '-', '-', '$4.575-4.595B'],
        ['Billings Guidance', '-', '-', '$7.37-7.47B']
    ]

    revenue_table = Table(revenue_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    revenue_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))

    story.append(revenue_table)
    story.append(Spacer(1, 0.2*inch))

    # Profitability metrics
    profit_data = [
        ['Profitability Metric', 'Current Value', 'Industry Context'],
        ['Gross Margin', '80.87%', 'Excellent (software-driven)'],
        ['Operating Margin', '30.86%', 'Strong for cybersecurity'],
        ['Net Profit Margin', '28.58%', 'Top-tier profitability'],
        ['Non-GAAP Operating Margin (Q4 2024)', '39%', 'Company record, +720 bps YoY'],
        ['Return on Equity (ROE)', '228.04%', 'Exceptional capital efficiency'],
        ['Return on Invested Capital (ROIC)', '66.39%', 'Superior capital allocation']
    ]

    profit_table = Table(profit_data, colWidths=[2.5*inch, 1.75*inch, 2.25*inch])
    profit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))

    story.append(profit_table)
    story.append(Spacer(1, 0.2*inch))

    # Valuation metrics
    valuation_data = [
        ['Valuation Metric', 'FTNT Value', 'Assessment'],
        ['P/E Ratio (Trailing)', '33.77x', 'Premium to market (SPY ~21x)'],
        ['P/E Ratio (Forward)', '29.07x', 'Growing into valuation'],
        ['PEG Ratio', '2.08', 'Slightly expensive vs growth'],
        ['EV/EBITDA', '27.08x', 'In line with cybersecurity peers'],
        ['Price/Sales', '10.16x', 'Premium SaaS multiple']
    ]

    valuation_table = Table(valuation_data, colWidths=[2.25*inch, 1.75*inch, 2.5*inch])
    valuation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))

    story.append(valuation_table)
    story.append(PageBreak())

    # ============================================================
    # PHASE 2: QUANTITATIVE ANALYSIS
    # ============================================================

    story.append(Paragraph("PHASE 2: QUANTITATIVE RISK & TECHNICAL ANALYSIS", section_style))
    story.append(Paragraph("Agent: Dr. Priya Desai (Quantitative Analyst)", subsection_style))

    story.append(Paragraph("Risk Metrics (252-Day Analysis vs SPY Benchmark):", subsection_style))

    risk_data = [
        ['Risk Metric', 'Value', 'Interpretation'],
        ['95% VaR (Daily)', '-3.66%', '95% of days, losses won\'t exceed 3.66%'],
        ['95% CVaR (Daily)', '-6.77%', 'Average loss when VaR is exceeded'],
        ['Sharpe Ratio', '-0.41', 'Poor risk-adjusted returns (< 1.0)'],
        ['Sortino Ratio', '-0.42', 'Poor downside risk-adjusted returns'],
        ['Maximum Drawdown', '-35.07%', 'Significant peak-to-trough decline'],
        ['Calmar Ratio', '-0.35', 'Negative return/drawdown relationship'],
        ['Annual Volatility', '41.15%', 'High volatility (40%-80% range)'],
        ['Beta (vs SPY)', '1.22', 'Above-market systematic risk'],
        ['Alpha (vs SPY)', '-27.00%', 'Underperforming benchmark by 27% annually']
    ]

    risk_table = Table(risk_data, colWidths=[2*inch, 1.5*inch, 3*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))

    story.append(risk_table)
    story.append(Spacer(1, 0.2*inch))

    risk_commentary = """
    <b>Risk Analysis Commentary:</b> FTNT exhibits high volatility (41.15% annualized) with negative
    alpha of -27%, indicating significant underperformance vs SPY over the past year. The maximum drawdown
    of -35.07% reflects the stock's decline from recent highs. Beta of 1.22 suggests above-average market
    sensitivity. The negative Sharpe ratio (-0.41) indicates poor risk-adjusted returns in the trailing
    period, likely due to the cybersecurity sector rotation and competitive pressures in 2024-2025.
    """
    story.append(Paragraph(risk_commentary, body_style))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Momentum Indicators (90-Day Analysis):", subsection_style))

    momentum_data = [
        ['Indicator', 'Current Value', 'Signal', 'Interpretation'],
        ['RSI', '40.97', 'Neutral', 'No extreme overbought/oversold condition'],
        ['MACD Line', '-0.28', 'Bearish', 'Below signal line (-0.10), downward momentum'],
        ['Stochastic %K', '0.00', 'Oversold', 'Potential reversal upward'],
        ['Williams %R', '-100.00', 'Oversold', 'Potential buy signal from extreme oversold'],
        ['Rate of Change', '-2.98%', 'Bearish', 'Negative momentum over period'],
        ['Confluence', '2/5 Bullish, 2/5 Bearish', 'MIXED', 'No clear directional consensus']
    ]

    momentum_table = Table(momentum_data, colWidths=[1.5*inch, 1.5*inch, 1.25*inch, 2.25*inch])
    momentum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))

    story.append(momentum_table)
    story.append(Spacer(1, 0.2*inch))

    momentum_commentary = """
    <b>Momentum Analysis Commentary:</b> FTNT shows mixed technical signals with extreme oversold
    conditions in Stochastic and Williams %R, suggesting potential for a bounce. However, bearish MACD
    and negative ROC indicate continued downward pressure. The RSI at 40.97 is approaching oversold
    territory but hasn't reached extreme levels. This mixed picture suggests the stock may be forming
    a base before a potential reversal, but confirmation from other indicators is needed.
    """
    story.append(Paragraph(momentum_commentary, body_style))

    story.append(PageBreak())

    story.append(Paragraph("Volatility Analysis (90-Day Period):", subsection_style))

    volatility_data = [
        ['Metric', 'Value', 'Guidance'],
        ['Volatility Regime', 'NORMAL', 'Standard position sizing (5-10% portfolio)'],
        ['ATR (Absolute)', '$2.16', 'Average daily range'],
        ['ATR (%)', '2.71%', 'Relative to current price'],
        ['Suggested Stop Loss', '$4.32', '2x ATR for risk management'],
        ['Daily Volatility', '0.0183', 'Daily price variation'],
        ['Annual Volatility', '29.08%', 'Annualized from 90-day period'],
        ['Bollinger Band %B', '0.264', 'Price in lower portion of bands'],
        ['Bollinger Bandwidth', '10.45%', 'Band width as % of middle band']
    ]

    volatility_table = Table(volatility_data, colWidths=[2*inch, 1.75*inch, 2.75*inch])
    volatility_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))

    story.append(volatility_table)
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Portfolio Correlation Analysis (252-Day Period):", subsection_style))

    correlation_commentary = """
    <b>Correlation with Existing Holdings:</b> FTNT shows moderate positive correlation with your
    current portfolio holdings, providing some diversification benefits:
    """
    story.append(Paragraph(correlation_commentary, body_style))

    correlations = [
        "• <b>FTNT vs PLTR:</b> +0.412 (Moderate) - Less correlated than other holdings",
        "• <b>FTNT vs TSLA:</b> +0.376 (Moderate) - Lowest correlation, good diversification",
        "• <b>FTNT vs NVDA:</b> +0.446 (Moderate) - Similar to PLTR correlation",
        "• <b>FTNT vs VOO:</b> +0.577 (High) - Higher correlation with broad market",
    ]
    for item in correlations:
        story.append(Paragraph(item, bullet_style))

    story.append(Spacer(1, 0.15*inch))

    diversification_text = """
    <b>Diversification Score: 0.453 (GOOD)</b><br/>
    FTNT would add moderate diversification to your tech-heavy portfolio. While it still moves with
    the broader market (VOO correlation of 0.577), its lower correlations with TSLA (0.376) and PLTR
    (0.412) suggest it follows somewhat different market dynamics. As a cybersecurity/enterprise
    software play, FTNT's performance drivers differ from your semiconductor (NVDA) and automotive/AI
    (TSLA) exposure, providing useful sector diversification within tech.
    """
    story.append(Paragraph(diversification_text, body_style))

    story.append(PageBreak())

    # ============================================================
    # FORTINET VS CROWDSTRIKE COMPARISON
    # ============================================================

    story.append(Paragraph("FORTINET vs CROWDSTRIKE: HEAD-TO-HEAD COMPARISON", section_style))

    comparison_intro = """
    Both FTNT and CRWD are on your 2026 watchlist. Here's a detailed comparison to determine which
    represents the better investment opportunity for your aggressive, tech-focused portfolio:
    """
    story.append(Paragraph(comparison_intro, body_style))
    story.append(Spacer(1, 0.15*inch))

    # Comparison table
    comparison_data = [
        ['Category', 'Fortinet (FTNT)', 'CrowdStrike (CRWD)', 'Winner'],
        ['Market Approach', 'Hybrid: On-premise + Cloud', 'Pure Cloud (Falcon platform)', 'Depends on use case'],
        ['Current Price', '$79.75', '~$370-400', 'N/A'],
        ['Stock Performance (1Y)', '+30.8%', '+5.3%', 'FTNT'],
        ['Revenue Growth', '+14% YoY (Q3 2025)', 'Slower due to July outage', 'FTNT'],
        ['2026 Earnings Outlook', '+3.8% YoY growth', '-13.5% YoY decline', 'FTNT'],
        ['Profitability', 'Highly profitable (29% margin)', 'Facing margin compression', 'FTNT'],
        ['Analyst Rating', 'Buy (Zacks Rank #2)', 'Sell (Zacks Rank #4)', 'FTNT'],
        ['Key Catalyst', 'Hardware refresh 2026', 'Recovery from July outage', 'FTNT'],
        ['Market Position', 'Leader in firewalls/SASE', 'Leader in endpoint/cloud', 'Tie'],
        ['Subscription Revenue', '70%+ recurring', '95% subscription-based', 'CRWD'],
        ['Recent Headwinds', 'Competitive pricing pressure', 'July 2024 global IT outage', 'FTNT'],
        ['Innovation Focus', 'FortiAI, SASE expansion', 'Falcon Cloud Security Suite', 'Tie']
    ]

    comparison_table = Table(comparison_data, colWidths=[1.5*inch, 1.75*inch, 1.75*inch, 1.5*inch])
    comparison_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f9f9f9'), colors.white])
    ]))

    story.append(comparison_table)
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Detailed Comparison Analysis:", subsection_style))

    comparison_points = [
        "<b>1. Recent Performance:</b> FTNT has significantly outperformed CRWD over the past year (+30.8% vs +5.3%), "
        "with CRWD hampered by the July 2024 global IT outage that damaged customer confidence.",

        "<b>2. Financial Momentum:</b> FTNT shows positive earnings growth trajectory for 2026 (+3.8% YoY) while "
        "CRWD faces a projected 13.5% earnings decline due to Customer Commitment Package discounts and retention efforts.",

        "<b>3. Business Model:</b> CRWD's pure cloud model (95% subscription revenue) provides better recurring revenue "
        "predictability, but FTNT's hybrid approach offers flexibility and the upcoming hardware refresh cycle could drive "
        "significant near-term revenue growth.",

        "<b>4. Valuation:</b> FTNT trades at more reasonable valuation multiples with P/E of 33.77x vs CRWD's typically "
        "higher premium. FTNT's PEG of 2.08 is elevated but justified by strong fundamentals and upcoming catalysts.",

        "<b>5. Market Position:</b> Both are leaders in their segments - FTNT dominates traditional firewalls and is "
        "gaining in SASE (85% growth in SSE billings), while CRWD leads in endpoint detection and cloud workload protection. "
        "FTNT's proprietary chip technology provides competitive moat in hardware performance.",

        "<b>6. 2026 Catalysts:</b> FTNT's hardware refresh cycle starting late 2025 is a more concrete near-term catalyst "
        "compared to CRWD's recovery from reputational damage, which may take longer to materialize.",

        "<b>7. Risk Factors:</b> FTNT faces pricing pressure in cloud-centric SASE market and tariff exposure. CRWD "
        "must rebuild customer trust post-outage and faces revenue recognition headwinds from discount packages."
    ]

    for point in comparison_points:
        story.append(Paragraph(point, body_style))
        story.append(Spacer(1, 0.1*inch))

    story.append(Spacer(1, 0.15*inch))

    winner_box = """
    <para align=center>
    <b><font size=12 color="#2c5aa0">VERDICT: FORTINET (FTNT) IS THE STRONGER BUY FOR 2026</font></b><br/><br/>
    <font size=10>
    FTNT presents better risk-reward dynamics with stronger momentum, positive earnings growth outlook,
    concrete hardware refresh catalyst, and superior recent performance. CRWD remains a quality company
    but needs more time to fully recover from the July 2024 outage impact. For aggressive growth investors
    seeking cybersecurity exposure in 2026, FTNT offers more attractive entry point and near-term upside potential.
    </font>
    </para>
    """
    story.append(Paragraph(winner_box, body_style))

    story.append(PageBreak())

    # ============================================================
    # PHASE 3: STRATEGY RECOMMENDATION
    # ============================================================

    story.append(Paragraph("PHASE 3: INVESTMENT STRATEGY & RECOMMENDATIONS", section_style))
    story.append(Paragraph("Agent: Elena Rodriguez-Park (Strategy Advisor)", subsection_style))

    story.append(Paragraph("Investment Thesis Summary:", subsection_style))

    thesis_points = [
        "<b>Bull Case (70% Weight):</b>",
        "• Hardware refresh cycle beginning late 2025 will drive product revenue acceleration through 2026",
        "• SASE market expansion with 85% YoY SSE billing growth demonstrates successful cloud transition",
        "• Proprietary FortiASIC technology provides sustainable competitive advantage in enterprise deals",
        "• Strong profitability (29% net margin) with improving operating leverage (39% non-GAAP op margin)",
        "• Exceptional capital efficiency (228% ROE, 66% ROIC) indicates superior business quality",
        "• Trading at reasonable valuation post-correction (forward P/E 29x vs historical premium)",
        "• Positive relative strength vs cybersecurity peers, especially CrowdStrike",
        "",
        "<b>Bear Case (30% Weight):</b>",
        "• Intense competition in cloud-centric SASE market with aggressive pricing from Palo Alto, Zscaler",
        "• High current volatility (41% annualized) and recent underperformance (negative alpha -27%)",
        "• Supply chain exposure to Taiwan manufacturing with potential tariff impacts",
        "• Hardware refresh cycle timing uncertainty - could be delayed by macro headwinds",
        "• PEG ratio of 2.08 suggests valuation already pricing in significant growth acceleration"
    ]

    for point in thesis_points:
        if point.startswith("<b>"):
            story.append(Paragraph(point, body_style))
        elif point == "":
            story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph(point, bullet_style))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Investment Ratings:", subsection_style))

    ratings_data = [
        ['Rating Category', 'Score (1-10)', 'Commentary'],
        ['Business Quality', '9/10', 'Exceptional margins, ROE, and competitive moats'],
        ['Growth Potential', '7/10', 'Solid 12-15% revenue growth with SASE upside'],
        ['Valuation', '6/10', 'Fair but not cheap; forward P/E 29x reasonable'],
        ['Momentum', '5/10', 'Mixed technicals, oversold but downtrend intact'],
        ['Risk/Reward', '7/10', 'Positive asymmetry with hardware cycle catalyst'],
        ['Portfolio Fit', '8/10', 'Good diversification for tech-heavy holdings'],
        ['', '<b>OVERALL: 7.0/10</b>', '<b>STRONG BUY with timing considerations</b>']
    ]

    ratings_table = Table(ratings_data, colWidths=[2*inch, 1.5*inch, 3*inch])
    ratings_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 9),
        ('FONTSIZE', (0, -1), (-1, -1), 10),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d4e4f7')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))

    story.append(ratings_table)
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Position Sizing Recommendation:", subsection_style))

    position_text = """
    <b>Recommended Portfolio Allocation: 5-7% initial position</b><br/><br/>

    Given your aggressive risk tolerance and tech-heavy portfolio, FTNT warrants a meaningful position
    but not overweight status. The recommendation is to build a 5-7% position over 2-3 entries to
    dollar-cost average through current volatility. This sizing provides significant upside exposure
    while limiting downside risk given the stock's recent underperformance and high volatility regime.
    <br/><br/>
    <b>Rationale for sizing:</b><br/>
    • Current volatility (41% annual, ATR 2.71%) suggests gradual entry approach<br/>
    • Correlation analysis shows good diversification vs existing holdings<br/>
    • 5-7% allows meaningful performance contribution without concentration risk<br/>
    • Can scale up to 10% if hardware refresh cycle shows early traction in Q1 2026
    """
    story.append(Paragraph(position_text, body_style))

    story.append(PageBreak())

    story.append(Paragraph("Entry Strategy & Execution Plan:", subsection_style))

    entry_strategy = [
        "<b>TIER 1 Entry (2.5-3% position) - IMMEDIATE</b>",
        "• Price Range: $77-82 (current levels)",
        "• Rationale: Extreme oversold conditions (Stochastic 0.0, Williams %R -100) suggest near-term bounce",
        "• This establishes base position to capture any year-end rally or early 2026 strength",
        "",
        "<b>TIER 2 Entry (1.5-2% position) - Q1 2026</b>",
        "• Price Range: $72-77 (if further weakness) OR $85-90 (on breakout confirmation)",
        "• Trigger: Either technical breakdown below $75 (buy dip) or RSI > 50 + MACD crossover (buy strength)",
        "• Rationale: Average down if macro selloff or add on confirmed momentum reversal",
        "",
        "<b>TIER 3 Entry (1-2% position) - Q2 2026</b>",
        "• Price Range: Based on hardware refresh cycle evidence",
        "• Trigger: Q1 2026 earnings showing acceleration in product billings/revenue",
        "• Rationale: Confirmation of thesis catalyst materializing, willing to pay higher price",
        "",
        "<b>Alternative: Single Entry Approach</b>",
        "• If you prefer simplicity, enter full 5-7% position at current levels ($77-82)",
        "• Set 2x ATR stop loss at $71.11 (current $79.75 - $8.64)",
        "• Re-evaluate at Q1 2026 earnings for potential scale-up decision"
    ]

    for point in entry_strategy:
        if point.startswith("<b>"):
            story.append(Paragraph(point, body_style))
        elif point == "":
            story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph(point, bullet_style))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Risk Management Framework:", subsection_style))

    risk_mgmt = [
        "<b>Stop Loss Levels:</b>",
        "• Initial: $71 (2x ATR = $8.64 below entry, ~11% max loss)",
        "• Trailing: Raise to breakeven once position gains 8-10%",
        "• Final: Use 20-day EMA as dynamic trailing stop once in profit",
        "",
        "<b>Profit Targets:</b>",
        "• Target 1 (40% of position): $92 (analyst consensus, +15% from current)",
        "• Target 2 (40% of position): $108-115 (2026 forecast range, +35-45%)",
        "• Target 3 (20% of position): $130-140 (bull case, +60-75%) - let winners run",
        "",
        "<b>Position Management Rules:</b>",
        "• Trim 25% if position gains >30% in < 3 months (take profits on euphoria)",
        "• Add to position if drops >15% on no company-specific bad news (buy dip)",
        "• Exit fully if breaks below $65 or if competitive position materially deteriorates",
        "• Re-evaluate thesis quarterly based on SASE growth metrics and hardware refresh progress",
        "",
        "<b>Portfolio Correlation Monitoring:</b>",
        "• Monitor correlation with VOO - exit if rises above 0.75 (losing diversification benefit)",
        "• Track relative strength vs CRWD - if CRWD significantly outperforms, reassess thesis",
        "• Rebalance if FTNT exceeds 10% of portfolio due to appreciation"
    ]

    for point in risk_mgmt:
        if point.startswith("<b>"):
            story.append(Paragraph(point, body_style))
        elif point == "":
            story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph(point, bullet_style))

    story.append(PageBreak())

    story.append(Paragraph("Key Metrics to Monitor:", subsection_style))

    monitoring = [
        "<b>Quarterly Earnings (Critical):</b>",
        "• SASE/SSE billing growth rate - target >50% YoY to confirm cloud traction",
        "• Product revenue acceleration - looking for sequential improvement as refresh cycle starts",
        "• Non-GAAP operating margin - should stay >35% to validate operating leverage thesis",
        "• Deferred revenue growth - leading indicator of future revenue strength",
        "",
        "<b>Technical Indicators (Weekly Review):</b>",
        "• RSI: Watch for move above 50 to confirm momentum reversal",
        "• MACD: Bullish crossover (MACD > signal line) would validate entry timing",
        "• 50-day / 200-day MA: Monitor for golden cross formation (bullish)",
        "• Volume: Above-average volume on up days confirms institutional accumulation",
        "",
        "<b>Market & Sector Trends (Monthly):</b>",
        "• Cybersecurity sector rotation - track XLK and HACK ETF relative performance",
        "• Competitive dynamics - monitor PANW, CRWD, ZS quarterly commentary on SASE",
        "• Enterprise IT spending - watch CIO surveys and macro indicators",
        "• Interest rates - cybersecurity multiples sensitive to rate expectations"
    ]

    for point in monitoring:
        if point.startswith("<b>"):
            story.append(Paragraph(point, body_style))
        elif point == "":
            story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph(point, bullet_style))

    story.append(Spacer(1, 0.3*inch))

    # Final Verdict Box
    verdict_box = """
    <para align=center>
    <b><font size=14 color="#2c5aa0">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</font></b><br/>
    <b><font size=16 color="#1a1a1a">FINAL VERDICT: STRONG BUY</font></b><br/>
    <b><font size=14 color="#2c5aa0">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</font></b><br/><br/>

    <font size=11>
    <b>Recommendation:</b> Initiate 5-7% position in FTNT for 2026 portfolio<br/><br/>

    <b>Target Entry:</b> $77-82 (current levels) with tiered approach preferred<br/><br/>

    <b>12-Month Price Target:</b> $108-115 (+35-45% upside)<br/><br/>

    <b>Risk/Reward Ratio:</b> 3.5:1 (Favorable)<br/><br/>

    <b>Confidence Level:</b> 75% (High conviction with normal execution risk)<br/><br/>

    <b>Key Catalyst:</b> Hardware refresh cycle + SASE market share gains<br/><br/>

    <b>Primary Risk:</b> Competitive pricing pressure delaying margin expansion<br/><br/>

    <b>Vs CRWD:</b> FTNT is superior choice for 2026 given stronger momentum and catalysts
    </font>
    </para>
    """
    story.append(Paragraph(verdict_box, body_style))

    story.append(PageBreak())

    # ============================================================
    # APPENDIX: MARKET OUTLOOK & DISCLAIMERS
    # ============================================================

    story.append(Paragraph("APPENDIX: CYBERSECURITY MARKET OUTLOOK 2025-2026", section_style))

    market_outlook = """
    The global cybersecurity market is projected to grow from $224.55 billion in 2024 to $555.98 billion
    by 2032, representing a 12% CAGR. The Next-Generation Cybersecurity Market specifically is expected
    to expand from $21.24 billion in 2024 to $62.54 billion by 2030 (19.72% CAGR).
    <br/><br/>
    <b>Key Market Drivers:</b><br/>
    • Accelerating cloud migration driving demand for SASE and cloud-native security solutions<br/>
    • AI-powered threats requiring AI-powered defense mechanisms (FortiAI positioning)<br/>
    • Zero Trust architecture adoption across enterprises<br/>
    • Increasing regulatory compliance requirements (GDPR, CCPA, industry-specific)<br/>
    • Hybrid work models expanding attack surface and security perimeter<br/>
    • Rising cost of data breaches (average $4.45M per incident) justifying security spend<br/>
    <br/>
    <b>North America Market:</b><br/>
    The United States dominated with 83.1% of the North America cybersecurity market in 2024. Leading
    suppliers including Palo Alto Networks, CrowdStrike, and Fortinet continue to post double-digit
    subscription ARR gains in this region.
    <br/><br/>
    <b>Competitive Landscape:</b><br/>
    The market is characterized by both consolidation and fragmentation - established giants (FTNT, PANW,
    CRWD, CHKP) compete against specialized pure-plays (ZS, OKTA, NET) and cloud hyperscalers (MSFT,
    GOOGL, AMZN) adding native security features. This creates both opportunities (market growth) and
    challenges (pricing pressure, product overlap).
    """
    story.append(Paragraph(market_outlook, body_style))

    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("REPORT METHODOLOGY & DATA SOURCES", section_style))

    methodology = """
    This analysis was conducted using Finance Guru™'s multi-agent framework with the following methodology:
    <br/><br/>
    <b>Phase 1 - Market Research (Dr. Aleksandr Petrov):</b><br/>
    • Market data retrieved via yfinance API (December 17-18, 2025)<br/>
    • Web research across 25+ financial news sources and analyst reports<br/>
    • Competitive analysis comparing FTNT vs CRWD business models and performance<br/>
    <br/>
    <b>Phase 2 - Quantitative Analysis (Dr. Priya Desai):</b><br/>
    • Risk metrics: 252-day analysis vs SPY benchmark using proprietary risk_metrics_cli.py<br/>
    • Momentum indicators: 90-day technical analysis using momentum_cli.py<br/>
    • Volatility assessment: 90-day regime analysis using volatility_cli.py<br/>
    • Correlation matrix: 252-day correlation with portfolio holdings (PLTR, TSLA, NVDA, VOO)<br/>
    <br/>
    <b>Phase 3 - Strategy Formulation (Elena Rodriguez-Park):</b><br/>
    • Integration of quantitative metrics with qualitative market research<br/>
    • Risk-adjusted position sizing based on portfolio correlation and volatility<br/>
    • Multi-tier entry strategy development with clear triggers and risk management<br/>
    • Comparative analysis vs CRWD to determine optimal cybersecurity allocation
    """
    story.append(Paragraph(methodology, body_style))

    story.append(PageBreak())

    story.append(Paragraph("IMPORTANT DISCLAIMERS & RISK WARNINGS", section_style))

    disclaimer_text = """
    <b>Educational Purpose Only:</b> This report is prepared for educational and informational purposes
    only. It is NOT investment advice, financial advice, or a recommendation to buy, sell, or hold any
    security. The analysis represents the opinions of Finance Guru™ analysts as of the report date and
    is subject to change without notice.
    <br/><br/>
    <b>Consult Professional Advisors:</b> Before making any investment decisions, you should consult with
    qualified financial advisors, tax professionals, and legal counsel who understand your specific
    financial situation, objectives, and risk tolerance. Past performance does not guarantee future results.
    <br/><br/>
    <b>Risk Disclosure:</b> Investing in individual stocks involves substantial risk, including the
    potential loss of principal. Fortinet stock exhibits high volatility (41% annualized) and has
    experienced significant drawdowns (maximum -35.07%). The stock price may fluctuate dramatically based
    on earnings results, competitive dynamics, market sentiment, macroeconomic conditions, and other
    factors beyond investor control.
    <br/><br/>
    <b>Forward-Looking Statements:</b> This report contains forward-looking statements regarding price
    targets, growth projections, and market trends. These statements are based on current information and
    assumptions that may prove incorrect. Actual results may differ materially from projections due to
    competitive pressures, technological changes, regulatory developments, economic conditions, and
    execution risks.
    <br/><br/>
    <b>Data Accuracy:</b> While we strive for accuracy, financial data is sourced from third-party
    providers (yfinance, public filings, analyst reports) and may contain errors or be subject to revision.
    Always verify critical data points independently before making investment decisions.
    <br/><br/>
    <b>No Guarantee of Results:</b> The price targets, entry strategies, and position sizing recommendations
    in this report are analytical opinions, not guarantees. Market conditions can change rapidly, rendering
    analysis outdated. Investors should continuously monitor positions and adjust strategies as needed.
    <br/><br/>
    <b>Conflicts of Interest:</b> This is a private family office analysis. The author/investor may hold
    positions in FTNT or related securities at the time of this report and may trade these securities
    without notice.
    <br/><br/>
    <b>Cybersecurity Sector Risks:</b> The cybersecurity industry faces rapid technological change,
    intense competition, potential for disruptive new entrants, customer concentration risk, and sensitivity
    to IT spending cycles. Companies in this sector often trade at premium valuations that may compress
    during market downturns.
    <br/><br/>
    <b>Company-Specific Risks:</b> FTNT faces specific risks including: competitive pricing pressure in
    SASE market, supply chain exposure to Taiwan manufacturing and tariff impacts, dependence on hardware
    refresh cycle timing, customer concentration in enterprise segment, and execution risk in cloud
    transition strategy.
    """
    story.append(Paragraph(disclaimer_text, body_style))

    story.append(Spacer(1, 0.3*inch))

    # Footer with report metadata
    footer_text = """
    <para align=center>
    <font size=8 color="#666666">
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>
    <b>Finance Guru™</b> - Private Family Office Investment Research<br/>
    Report Generated: December 18, 2025 | Document Version: 1.0<br/>
    Analysis Period: December 2024 - December 2025 | Forward Outlook: 12-18 Months<br/>
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>
    © 2025 Irondi Family Office. For Private Use Only. Do Not Distribute.
    </font>
    </para>
    """
    story.append(Paragraph(footer_text, body_style))

    # Build PDF
    doc.build(story)

    print(f"\n✅ PDF Report Generated Successfully!")
    print(f"📄 Location: {output_path}")
    print(f"📊 Report Size: {len(story)} elements")
    print(f"🎯 Analysis Complete: FTNT - STRONG BUY for 2026")

if __name__ == "__main__":
    create_ftnt_report()
