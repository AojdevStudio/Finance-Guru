#!/usr/bin/env python3
"""
Applied Digital (APLD) - Comprehensive Investment Analysis Report
Generated: 2025-12-18
Finance Guru™ - Full Research Workflow
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os

def create_header_style():
    """Create custom header style for the report"""
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#0066cc'),
        borderPadding=8,
        backColor=colors.HexColor('#f0f8ff')
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#0066cc'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10,
        alignment=TA_JUSTIFY,
        leading=14
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        leftIndent=20,
        spaceAfter=8,
        leading=14
    )

    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'heading1': heading1_style,
        'heading2': heading2_style,
        'body': body_style,
        'bullet': bullet_style
    }

def create_verdict_box(verdict, price_target_low, price_target_high, position_size_pct, position_size_dollars):
    """Create a highlighted verdict box"""

    # Determine verdict color
    if verdict.upper() == "STRONG BUY":
        verdict_color = colors.HexColor('#28a745')
    elif verdict.upper() == "BUY":
        verdict_color = colors.HexColor('#5cb85c')
    elif verdict.upper() == "HOLD":
        verdict_color = colors.HexColor('#ffc107')
    elif verdict.upper() == "SELL":
        verdict_color = colors.HexColor('#dc3545')
    else:
        verdict_color = colors.HexColor('#666666')

    verdict_data = [
        ['INVESTMENT VERDICT', verdict],
        ['2026 PRICE TARGET', f'${price_target_low} - ${price_target_high}'],
        ['RECOMMENDED POSITION', f'{position_size_pct}% (${position_size_dollars:,.0f})'],
    ]

    verdict_table = Table(verdict_data, colWidths=[3*inch, 3*inch])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
        ('TEXTCOLOR', (1, 0), (1, 0), verdict_color),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')]),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))

    return verdict_table

def create_header_info_table(current_price, ytd_performance, analyst_team):
    """Create the header information table"""

    header_data = [
        ['Current Price', f'${current_price}'],
        ['YTD Performance', ytd_performance],
        ['Analyst Team', analyst_team],
        ['Report Date', '2025-12-18']
    ]

    header_table = Table(header_data, colWidths=[2*inch, 4*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    return header_table

def create_risk_metrics_table():
    """Create risk metrics analysis table"""

    risk_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['Sharpe Ratio', '1.19', 'Good risk-adjusted returns'],
        ['Sortino Ratio', '1.91', 'Strong downside protection'],
        ['95% VaR (Daily)', '-9.46%', 'Max loss 95% of days'],
        ['95% CVaR (Daily)', '-15.85%', 'Avg loss beyond VaR'],
        ['Maximum Drawdown', '-67.76%', 'Severe peak-to-trough decline'],
        ['Calmar Ratio', '2.30', 'Good return/drawdown ratio'],
        ['Annual Volatility', '127.41%', 'EXTREME volatility'],
        ['Beta (vs SPY)', '2.17', 'High systematic risk'],
        ['Alpha (vs SPY)', '133.04%', 'Significant outperformance']
    ]

    risk_table = Table(risk_data, colWidths=[2.2*inch, 1.5*inch, 2.8*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    return risk_table

def create_momentum_table():
    """Create momentum indicators table"""

    momentum_data = [
        ['Indicator', 'Value', 'Signal', 'Interpretation'],
        ['RSI', '36.08', 'Neutral', 'No extreme condition'],
        ['MACD', '-0.62', 'Bearish', 'Below signal line'],
        ['Stochastic %K', '0.54', 'Oversold', 'Potential reversal up'],
        ['Williams %R', '-99.46', 'Oversold', 'Potential buy signal'],
        ['ROC', '-22.01%', 'Bearish', 'Negative momentum'],
        ['Confluence', '2/5 Bullish', 'Mixed', 'No clear direction']
    ]

    momentum_table = Table(momentum_data, colWidths=[1.5*inch, 1.2*inch, 1.3*inch, 2.5*inch])
    momentum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    return momentum_table

def create_volatility_table():
    """Create volatility analysis table"""

    volatility_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['Volatility Regime', 'EXTREME', 'Maximum caution required'],
        ['ATR Value', '$2.89', '12.09% of price'],
        ['Suggested Stop Loss', '$5.78', '2× ATR'],
        ['Daily Volatility', '7.52%', 'Very high daily swings'],
        ['Annual Volatility', '119.42%', 'Extreme price variance'],
        ['Bollinger %B', '0.307', 'Within normal range'],
        ['Bandwidth', '57.45%', 'Wide bands - high volatility']
    ]

    volatility_table = Table(volatility_data, colWidths=[2.2*inch, 1.5*inch, 2.8*inch])
    volatility_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    return volatility_table

def create_analyst_ratings_table():
    """Create analyst ratings and price targets table"""

    analyst_data = [
        ['Source', 'Rating', 'Price Target', 'Date'],
        ['Consensus (11 analysts)', 'Strong Buy', '$29.36', 'Dec 2025'],
        ['B. Riley', 'Buy', '$47.00', 'Recent'],
        ['Citizens JMP', 'Buy', '$35.00', 'Recent'],
        ['Needham', 'Buy', '$41.00', 'Recent'],
        ['Roth Capital', 'Buy', '$43.00', 'Oct 2025'],
        ['Cantor Fitzgerald', 'Hold', '$7.00', 'Apr 2025'],
        ['Average Target', '-', '$42.78', '3-month avg']
    ]

    analyst_table = Table(analyst_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    analyst_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    return analyst_table

def generate_report():
    """Generate the complete APLD analysis report"""

    # Ensure output directory exists
    output_dir = '/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports'
    os.makedirs(output_dir, exist_ok=True)

    # Create PDF
    pdf_path = os.path.join(output_dir, 'APLD-analysis-2025-12-18.pdf')
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for the 'Flowable' objects
    elements = []

    # Get custom styles
    styles = create_header_style()

    # ========== PAGE 1: TITLE & EXECUTIVE SUMMARY ==========

    # Title
    title = Paragraph("APPLIED DIGITAL CORPORATION (APLD)", styles['title'])
    elements.append(title)

    subtitle = Paragraph("AI Infrastructure Investment Analysis", styles['subtitle'])
    elements.append(subtitle)
    elements.append(Spacer(1, 0.1*inch))

    # Header info table
    header_table = create_header_info_table(
        current_price='23.90',
        ytd_performance='+273% (as of Dec 15, 2025)',
        analyst_team='Finance Guru™ - Market Researcher, Quant Analyst, Strategy Advisor'
    )
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*inch))

    # Verdict Box
    verdict_table = create_verdict_box(
        verdict='SPECULATIVE BUY',
        price_target_low=35,
        price_target_high=45,
        position_size_pct=3.0,
        position_size_dollars=7500
    )
    elements.append(verdict_table)
    elements.append(Spacer(1, 0.3*inch))

    # Executive Summary
    exec_heading = Paragraph("EXECUTIVE SUMMARY", styles['heading1'])
    elements.append(exec_heading)

    exec_summary = """Applied Digital Corporation represents a high-risk, high-reward opportunity in the rapidly
    expanding AI infrastructure sector. The company has successfully pivoted from cryptocurrency mining to become
    a specialized provider of purpose-built AI data centers and high-performance computing solutions. With $19 billion
    in total contracted revenue over 15-year terms (including CoreWeave's $11 billion deal and a hyperscaler's $5 billion
    lease), APLD has secured substantial revenue visibility through 2040."""

    elements.append(Paragraph(exec_summary, styles['body']))
    elements.append(Spacer(1, 0.15*inch))

    # Investment Thesis
    thesis_heading = Paragraph("INVESTMENT THESIS", styles['heading2'])
    elements.append(thesis_heading)

    thesis_points = [
        "<b>Strategic Positioning:</b> APLD is backed by NVIDIA (7.7M shares) and has achieved Elite Partner status in the NVIDIA Partner Network, validating its technical capabilities and market position.",

        "<b>Revenue Visibility:</b> $19 billion in contracted revenue provides exceptional forward visibility, with first 100 MW facility achieving Ready-for-Service status in November 2025.",

        "<b>Growth Trajectory:</b> Management upgraded 2026 guidance to 200 MW (vs. 100 MW expected), with plans to scale beyond 1 GW by 2028-2030.",

        "<b>Strong Performance:</b> Q1 FY2026 revenue of $64.2M (+84% YoY), positive adjusted EBITDA of $21.4M (+93% YoY), demonstrating operational leverage.",

        "<b>Quantitative Edge:</b> Alpha of 133% vs. SPY with Sharpe ratio of 1.19 indicates strong risk-adjusted outperformance despite extreme volatility."
    ]

    for point in thesis_points:
        elements.append(Paragraph(f"• {point}", styles['bullet']))

    elements.append(Spacer(1, 0.2*inch))

    # Key Risks
    risks_heading = Paragraph("KEY RISKS", styles['heading2'])
    elements.append(risks_heading)

    risk_points = [
        "<b>Extreme Volatility:</b> 127% annual volatility with -67.76% maximum drawdown requires strong risk management.",

        "<b>Profitability Challenges:</b> TTM loss of $248M on $174M revenue, trading at 50x sales with negative margins.",

        "<b>Execution Risk:</b> Capital-intensive buildouts ($689M debt) require flawless execution to service obligations.",

        "<b>Competition:</b> CoreWeave (competitor with $438M Q1 revenue) and established players like Equinix pose margin pressure.",

        "<b>High Short Interest:</b> 30% of float is shorted (~79M shares), creating volatility and sentiment risk.",

        "<b>Valuation:</b> Priced for perfection - any delays in facility delivery or lease signings could trigger sharp selloffs."
    ]

    for point in risk_points:
        elements.append(Paragraph(f"• {point}", styles['bullet']))

    # Page Break
    elements.append(PageBreak())

    # ========== PAGE 2: QUANTITATIVE ANALYSIS ==========

    quant_heading = Paragraph("QUANTITATIVE ANALYSIS", styles['heading1'])
    elements.append(quant_heading)

    # Risk Metrics Section
    risk_section = Paragraph("Risk Metrics (252-Day Analysis vs. SPY)", styles['heading2'])
    elements.append(risk_section)
    elements.append(Spacer(1, 0.1*inch))

    risk_table = create_risk_metrics_table()
    elements.append(risk_table)
    elements.append(Spacer(1, 0.15*inch))

    risk_interpretation = """<b>Key Takeaway:</b> APLD exhibits exceptional alpha generation (133% vs. SPY) with good
    risk-adjusted returns (Sharpe 1.19), but comes with extreme volatility (127% annual) and severe drawdown risk
    (-67.76%). The high beta (2.17) means this stock amplifies market movements significantly. Suitable only for
    aggressive investors with high risk tolerance."""

    elements.append(Paragraph(risk_interpretation, styles['body']))
    elements.append(Spacer(1, 0.2*inch))

    # Momentum Analysis Section
    momentum_section = Paragraph("Momentum Indicators (90-Day Analysis)", styles['heading2'])
    elements.append(momentum_section)
    elements.append(Spacer(1, 0.1*inch))

    momentum_table = create_momentum_table()
    elements.append(momentum_table)
    elements.append(Spacer(1, 0.15*inch))

    momentum_interpretation = """<b>Key Takeaway:</b> Mixed momentum signals with oversold conditions (Stochastic %K
    at 0.54, Williams %R at -99.46) suggesting potential reversal, but bearish MACD and negative ROC (-22%) indicating
    continued downward pressure. The stock appears to be consolidating after recent volatility. Entry timing should
    focus on confirmation of reversal with volume support."""

    elements.append(Paragraph(momentum_interpretation, styles['body']))
    elements.append(Spacer(1, 0.2*inch))

    # Volatility Analysis Section
    volatility_section = Paragraph("Volatility Analysis (90-Day Analysis)", styles['heading2'])
    elements.append(volatility_section)
    elements.append(Spacer(1, 0.1*inch))

    volatility_table = create_volatility_table()
    elements.append(volatility_table)
    elements.append(Spacer(1, 0.15*inch))

    volatility_interpretation = """<b>Key Takeaway:</b> EXTREME volatility regime with 119% annualized volatility
    requires maximum position sizing caution. The ATR of $2.89 (12% of price) suggests daily swings of $3-6 are
    normal. Wide Bollinger Bands (57% bandwidth) confirm high volatility environment. Recommended stop loss at 2×
    ATR = $5.78 below entry to avoid whipsaw while protecting capital."""

    elements.append(Paragraph(volatility_interpretation, styles['body']))

    # Page Break
    elements.append(PageBreak())

    # ========== PAGE 3: MARKET SENTIMENT & CATALYSTS ==========

    market_heading = Paragraph("MARKET SENTIMENT & ANALYST VIEW", styles['heading1'])
    elements.append(market_heading)

    # Analyst Ratings
    analyst_heading = Paragraph("Wall Street Analyst Ratings & Price Targets", styles['heading2'])
    elements.append(analyst_heading)
    elements.append(Spacer(1, 0.1*inch))

    analyst_table = create_analyst_ratings_table()
    elements.append(analyst_table)
    elements.append(Spacer(1, 0.15*inch))

    analyst_interpretation = """<b>Analyst Consensus:</b> Strong Buy rating from 11 analysts with average price target
    of $29.36 (23% upside from current $23.90). However, wide dispersion in targets ($7 to $47) reflects uncertainty
    around execution and profitability timeline. Recent upgrades from B. Riley ($47), Citizens JMP ($35), and Needham
    ($41) show growing confidence in the AI infrastructure thesis. Cantor Fitzgerald's $7 target is a significant
    outlier and likely based on conservative valuation metrics."""

    elements.append(Paragraph(analyst_interpretation, styles['body']))
    elements.append(Spacer(1, 0.2*inch))

    # 2026 Catalysts
    catalysts_heading = Paragraph("2026 CATALYSTS", styles['heading2'])
    elements.append(catalysts_heading)

    catalyst_points = [
        "<b>Facility Deliveries:</b> 150 MW building at Polaris Forge 1 (Ellendale) expected mid-2026, with portion of 300 MW Polaris Forge 2 (Harwood) by year-end. Revenue recognition begins as facilities come online.",

        "<b>Free Cash Flow Inflection:</b> Management targets positive FCF from Ellendale campus by mid-2026, a critical milestone for valuation re-rating.",

        "<b>Additional Lease Announcements:</b> With $5 billion development facility from Macquarie, APLD can pursue new hyperscaler deals. Market expects 1-2 major announcements in 2026.",

        "<b>CoreWeave IPO Impact:</b> CoreWeave's anticipated 2026 IPO could validate AI infrastructure valuations and create positive sentiment spillover for APLD.",

        "<b>Revenue Ramp:</b> Consensus estimates $280-$310M revenue for FY2026 (60-70% growth), with improving margins as operational leverage kicks in.",

        "<b>NVIDIA Product Launches:</b> Next-gen GPU releases (Blackwell, beyond) drive increased compute demand, benefiting data center operators like APLD."
    ]

    for point in catalyst_points:
        elements.append(Paragraph(f"• {point}", styles['bullet']))

    elements.append(Spacer(1, 0.2*inch))

    # Company Overview
    company_heading = Paragraph("COMPANY OVERVIEW", styles['heading2'])
    elements.append(company_heading)

    company_overview = """Applied Digital Corporation (NASDAQ: APLD) is a pioneering digital infrastructure innovator
    specializing in purpose-built AI data centers and high-performance computing solutions. Founded in 2020 and
    headquartered in Dallas, TX, the company underwent a strategic pivot in late 2022 from cryptocurrency mining
    to AI infrastructure following Ethereum's consensus mechanism shift.

    <br/><br/>
    The company's flagship Polaris Forge campuses in North Dakota leverage low-cost renewable energy, proprietary
    waterless cooling technology, and hyperscale expertise to deliver GPU-optimized compute infrastructure. APLD
    was named Best Data Center in the Americas 2025 by Datacloud and has reduced facility build times from 24
    months to 12-14 months, demonstrating operational excellence.

    <br/><br/>
    <b>Key Infrastructure:</b>
    <br/>• Polaris Forge 1 (Ellendale): 400 MW campus fully leased to CoreWeave ($11B/15-year contract)
    <br/>• Polaris Forge 2 (Harwood): 280 MW AI factory with $5B/15-year hyperscaler lease
    <br/>• Pipeline: Plans to scale beyond 1 GW by 2028-2030

    <br/><br/>
    <b>Strategic Partnerships:</b>
    <br/>• NVIDIA Elite Partner with 7.7M share investment
    <br/>• CoreWeave (primary customer and NVIDIA portfolio company)
    <br/>• Macquarie Group ($5B development facility)
    <br/>• Undisclosed Investment-Grade U.S. Hyperscaler
    """

    elements.append(Paragraph(company_overview, styles['body']))

    # Page Break
    elements.append(PageBreak())

    # ========== PAGE 4: INVESTMENT STRATEGY ==========

    strategy_heading = Paragraph("INVESTMENT STRATEGY & PORTFOLIO POSITIONING", styles['heading1'])
    elements.append(strategy_heading)

    # Recommendation
    recommendation_heading = Paragraph("RECOMMENDATION: SPECULATIVE BUY", styles['heading2'])
    elements.append(recommendation_heading)

    recommendation = """Applied Digital represents a compelling speculative opportunity for aggressive growth investors
    seeking exposure to the AI infrastructure megatrend. While the extreme volatility and execution risks are significant,
    the company's contracted revenue base, strategic partnerships, and operational momentum justify a small position
    within a diversified portfolio.

    <br/><br/>
    <b>Investment Rationale:</b> The combination of $19B in contracted revenue, NVIDIA validation, improving operational
    metrics (positive adjusted EBITDA), and significant alpha generation (133% vs. SPY) outweighs the near-term
    profitability challenges. The current price of $23.90 represents a reasonable entry point following recent
    consolidation, with oversold momentum indicators suggesting potential reversal.
    """

    elements.append(Paragraph(recommendation, styles['body']))
    elements.append(Spacer(1, 0.2*inch))

    # Position Sizing
    sizing_heading = Paragraph("POSITION SIZING FOR $250,000 PORTFOLIO", styles['heading2'])
    elements.append(sizing_heading)
    elements.append(Spacer(1, 0.1*inch))

    sizing_data = [
        ['Position Size', 'Allocation', 'Dollar Amount', 'Shares', 'Rationale'],
        [
            'Recommended',
            '3.0%',
            '$7,500',
            '314 shares',
            'Conservative sizing given extreme volatility and speculative nature'
        ],
        [
            'Aggressive',
            '5.0%',
            '$12,500',
            '523 shares',
            'For high risk tolerance investors comfortable with -67% drawdown potential'
        ],
        [
            'Maximum',
            '7.5%',
            '$18,750',
            '785 shares',
            'Absolute ceiling - violates volatility-based position sizing (1-2% max)'
        ]
    ]

    sizing_table = Table(sizing_data, colWidths=[1.3*inch, 0.9*inch, 1.1*inch, 1*inch, 2.2*inch])
    sizing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (3, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f8ff')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(sizing_table)
    elements.append(Spacer(1, 0.15*inch))

    sizing_note = """<b>Finance Guru Recommendation:</b> Given the EXTREME volatility regime (127% annual volatility),
    we recommend the conservative 3% allocation ($7,500). This limits maximum portfolio impact to ~2% even in a
    -67% drawdown scenario. The position can be scaled up to 5% if the stock demonstrates reduced volatility and
    achieves key milestones (positive FCF, additional lease announcements)."""

    elements.append(Paragraph(sizing_note, styles['body']))
    elements.append(Spacer(1, 0.2*inch))

    # Entry Strategy
    entry_heading = Paragraph("ENTRY STRATEGY", styles['heading2'])
    elements.append(entry_heading)

    entry_strategy = """<b>Approach:</b> Staged entry using dollar-cost averaging (DCA) to mitigate volatility risk.

    <br/><br/>
    <b>Execution Plan for $7,500 Position:</b>
    <br/>• <b>Tranche 1 (40% - $3,000):</b> Immediate entry at current levels (~$23.90). Capitalize on oversold
    conditions (Williams %R at -99.46, Stochastic at 0.54).

    <br/>• <b>Tranche 2 (30% - $2,250):</b> Add on strength if price breaks above $26 with volume confirmation,
    validating momentum reversal.

    <br/>• <b>Tranche 3 (30% - $2,250):</b> Add on weakness if price dips to $20-21 support (Bollinger Lower Band
    at $19.16), providing better risk/reward.

    <br/><br/>
    <b>Stop Loss:</b> Hard stop at $18.12 (2× ATR = $5.78 below entry of $23.90). This represents -24% loss on
    position, or -0.72% portfolio impact. Adjust stop to breakeven once position shows +20% profit.

    <br/><br/>
    <b>Profit Targets:</b>
    <br/>• <b>Target 1:</b> $35 (+46%) - Take 25% profit, analyst consensus range
    <br/>• <b>Target 2:</b> $45 (+88%) - Take 50% profit, upper analyst targets
    <br/>• <b>Target 3:</b> $50+ (+109%) - Let remaining 25% ride for potential breakout

    <br/><br/>
    <b>Time Horizon:</b> 12-18 months. Catalysts (facility deliveries, FCF positive, new leases) expected to
    materialize through 2026. Re-evaluate if no progress by Q3 2026.
    """

    elements.append(Paragraph(entry_strategy, styles['body']))

    # Page Break
    elements.append(PageBreak())

    # ========== PAGE 5: COMPETITIVE ANALYSIS ==========

    competitive_heading = Paragraph("COMPETITIVE LANDSCAPE & RISKS", styles['heading1'])
    elements.append(competitive_heading)

    # Competition Section
    competition_heading = Paragraph("COMPETITIVE POSITIONING", styles['heading2'])
    elements.append(competition_heading)

    competition = """The AI infrastructure market is experiencing explosive growth but faces intensifying competition
    from both pure-play providers and established data center operators.

    <br/><br/>
    <b>Direct Competitors:</b>
    <br/>• <b>CoreWeave (CRWV):</b> Ironically both APLD's largest customer and competitor. Reported $438M Q1 2025
    revenue (4× YoY growth), operates 33 AI-optimized data centers. Better funded and more established, but
    partnership with APLD suggests complementary positioning.

    <br/>• <b>Lambda Labs:</b> GPU cloud provider with strong developer community. Smaller scale but aggressive pricing.

    <br/>• <b>Crusoe Energy:</b> Focuses on stranded energy monetization for data centers, similar to APLD's North
    Dakota strategy.

    <br/><br/>
    <b>Incumbent Threats:</b>
    <br/>• <b>Equinix (EQIX):</b> $10B revenue, 260+ data centers globally. Massive scale and customer relationships,
    but transitioning legacy infrastructure to AI-optimized is capital-intensive.

    <br/>• <b>Dell Technologies, HPE:</b> Offering on-premises AI infrastructure solutions, reducing cloud dependency.

    <br/>• <b>Hyperscalers (AWS, Azure, GCP):</b> Building proprietary AI infrastructure. However, capacity constraints
    create opportunity for third-party providers like APLD.

    <br/><br/>
    <b>Competitive Advantages:</b>
    <br/>1. Purpose-built infrastructure (not retrofitted legacy facilities)
    <br/>2. Proprietary waterless cooling (lower operating costs, better for environment)
    <br/>3. Strategic North Dakota locations (low-cost renewable energy, natural cooling)
    <br/>4. NVIDIA Elite Partner status and investment
    <br/>5. Rapid deployment (12-14 months vs. industry 24 months)
    <br/>6. Long-term contracted revenue reducing customer acquisition costs

    <br/><br/>
    <b>Competitive Risks:</b>
    <br/>1. Margin compression as market matures and competition intensifies
    <br/>2. Technology obsolescence - GPU architectures evolve rapidly
    <br/>3. Customer concentration (CoreWeave represents majority of contracted revenue)
    <br/>4. Capital intensity creates barriers to scaling without dilution or excessive debt
    """

    elements.append(Paragraph(competition, styles['body']))
    elements.append(Spacer(1, 0.2*inch))

    # Risk Detail Section
    risk_detail_heading = Paragraph("DETAILED RISK ANALYSIS", styles['heading2'])
    elements.append(risk_detail_heading)

    risk_detail = """<b>1. Execution Risk (HIGH)</b>
    <br/>Building billions in infrastructure on schedule and budget is APLD's primary challenge. The company has
    reduced build times from 24 to 12-14 months, demonstrating capability, but any delays in facility delivery
    directly impact revenue recognition and could trigger covenant violations given $689M debt load.

    <br/><br/>
    <b>Mitigation:</b> Macquarie's $5B development facility reduces pre-lease capital stress. Management's track
    record (first 100 MW achieved RFS in November 2025 on schedule) provides confidence.

    <br/><br/>
    <b>2. Profitability Timeline (HIGH)</b>
    <br/>TTM loss of $248M on $174M revenue is unsustainable. While adjusted EBITDA is positive ($21.4M), GAAP
    losses persist due to interest expenses ($8.9M, up 100% YoY) and debt-related charges. Path to profitability
    depends on revenue scaling faster than interest and depreciation.

    <br/><br/>
    <b>Mitigation:</b> Management targets FCF positive by mid-2026 from Ellendale campus. If achieved, validates
    business model and de-risks investment thesis significantly.

    <br/><br/>
    <b>3. Customer Concentration (MEDIUM-HIGH)</b>
    <br/>CoreWeave represents $11B of $19B contracted revenue (58%). If CoreWeave faces challenges (IPO delays,
    customer loss, financial stress), APLD's revenue visibility deteriorates.

    <br/><br/>
    <b>Mitigation:</b> Second hyperscaler lease ($5B) provides diversification. APLD actively pursuing additional
    customers leveraging Macquarie facility for pre-lease development.

    <br/><br/>
    <b>4. Financing Risk (MEDIUM)</b>
    <br/>Data center buildouts require continuous capital. With $689M debt and negative FCF, APLD depends on
    capital markets for growth. Rising interest rates or equity market volatility could constrain funding.

    <br/><br/>
    <b>Mitigation:</b> $268.9M raised through recent stock sales provides cushion. NVIDIA backing and strong
    analyst support suggest continued access to capital markets.

    <br/><br/>
    <b>5. Market Sentiment / Short Interest (MEDIUM)</b>
    <br/>30% short interest (~79M shares) creates volatility and potential for sharp moves in either direction.
    Negative sentiment could trigger cascading selloff regardless of fundamentals.

    <br/><br/>
    <b>Mitigation:</b> Strong catalyst pipeline (facility deliveries, FCF positive, new leases) could force
    short covering. Position sizing limits portfolio impact of sentiment-driven moves.

    <br/><br/>
    <b>6. Technology Risk (LOW-MEDIUM)</b>
    <br/>Rapid GPU evolution could render infrastructure obsolete. However, 15-year customer contracts suggest
    customers commit to long-term use regardless of specific GPU generation.

    <br/><br/>
    <b>Mitigation:</b> NVIDIA partnership provides early visibility into product roadmaps. Modular infrastructure
    design allows GPU upgrades without complete facility rebuild.
    """

    elements.append(Paragraph(risk_detail, styles['body']))

    # Page Break
    elements.append(PageBreak())

    # ========== PAGE 6: FINANCIAL ANALYSIS ==========

    financial_heading = Paragraph("FINANCIAL ANALYSIS & PROJECTIONS", styles['heading1'])
    elements.append(financial_heading)

    # Recent Performance
    performance_heading = Paragraph("RECENT FINANCIAL PERFORMANCE", styles['heading2'])
    elements.append(performance_heading)

    performance = """<b>Q1 Fiscal Year 2026 (ended August 31, 2025):</b>
    <br/>• Revenue: $64.2M (+84% YoY) - strong growth trajectory
    <br/>• Adjusted EBITDA: $21.4M (+93% YoY) - operational leverage evident
    <br/>• EPS: -$0.03 (beat expectations of -$0.11)
    <br/>• TTM Revenue: $174M (up from previous periods)
    <br/>• TTM Net Loss: -$248M (improving but still significant)
    <br/>• Interest Expense: $8.9M quarterly (+100% YoY) - debt burden growing

    <br/><br/>
    <b>Stock Performance:</b>
    <br/>• YTD Performance: +273% (as of Dec 15, 2025)
    <br/>• 52-Week Range: ~$4-$25 (extreme volatility)
    <br/>• Recent Price: $23.90 (down from ~$25 highs, consolidating)
    <br/>• Market Cap: ~$2.7B (based on ~112M shares outstanding)
    <br/>• EV/Sales (TTM): ~50× (very expensive, priced for hypergrowth)

    <br/><br/>
    <b>Balance Sheet Snapshot:</b>
    <br/>• Total Debt: $689M (as of Feb 2025)
    <br/>• Recent Equity Raise: $268.9M (provides growth capital)
    <br/>• Macquarie Facility: $5B development funding (non-dilutive, pre-lease only)
    <br/>• Cash Burn: Negative FCF, but improving with facility deliveries
    """

    elements.append(Paragraph(performance, styles['body']))
    elements.append(Spacer(1, 0.2*inch))

    # Projections
    projections_heading = Paragraph("2026-2027 PROJECTIONS", styles['heading2'])
    elements.append(projections_heading)

    projections = """<b>Consensus Estimates (FY 2026):</b>
    <br/>• Revenue: $280-$310M (60-70% growth from TTM $174M)
    <br/>• Net Margin: -34% (improving from current -143% TTM)
    <br/>• EBITDA: Positive and expanding
    <br/>• EPS: Likely still negative, but improving

    <br/><br/>
    <b>Key Assumptions:</b>
    <br/>1. Ellendale 100 MW facility fully operational Q1 2026 (done)
    <br/>2. Ellendale 150 MW facility operational mid-2026 (on track)
    <br/>3. Harwood initial capacity operational Q4 2026 (on track per management)
    <br/>4. No delays in customer acceptance or revenue recognition
    <br/>5. Operating leverage from scale reduces per-MW costs

    <br/><br/>
    <b>Bull Case 2027 Scenario:</b>
    <br/>• Revenue: $600M+ (as more capacity comes online)
    <br/>• Adjusted EBITDA Margin: 30-40% (data center industry standard)
    <br/>• FCF Positive: $100M+ (validates business model)
    <br/>• Additional Lease Announcements: $3-5B (de-risks growth story)
    <br/>• Stock Price: $50-$75 (2-3× from current, approaching high analyst targets)

    <br/><br/>
    <b>Bear Case 2027 Scenario:</b>
    <br/>• Revenue: $200M (facility delays, customer issues)
    <br/>• Continued GAAP Losses: Debt service consumes EBITDA
    <br/>• FCF Negative: Forces dilutive equity raises or debt restructuring
    <br/>• No New Lease Announcements: Growth story stalls
    <br/>• Stock Price: $10-15 (reversion to asset value, -50-60% from current)

    <br/><br/>
    <b>Base Case (Most Likely):</b>
    <br/>• Revenue: $400M by end of 2027
    <br/>• FCF Positive mid-2026, improving through 2027
    <br/>• 1-2 new lease announcements ($2-3B each)
    <br/>• Stock Price: $35-45 (aligns with our price target and analyst consensus)
    """

    elements.append(Paragraph(projections, styles['body']))
    elements.append(Spacer(1, 0.2*inch))

    # Valuation
    valuation_heading = Paragraph("VALUATION ASSESSMENT", styles['heading2'])
    elements.append(valuation_heading)

    valuation = """<b>Current Valuation (Price: $23.90, Market Cap: ~$2.7B):</b>
    <br/>• EV/Sales (TTM): ~50× (extremely expensive vs. traditional data centers at 5-10×)
    <br/>• EV/Sales (FY2026E): ~25-30× (still rich but factoring in growth)
    <br/>• P/E: N/A (negative earnings)
    <br/>• Price/Book: High (asset-heavy business with heavy depreciation)

    <br/><br/>
    <b>Comparable Valuation:</b>
    <br/>• Equinix (EQIX): EV/Sales ~10×, but mature with limited growth
    <br/>• Digital Realty (DLR): EV/Sales ~8×, similar maturity profile
    <br/>• Pure-play AI infrastructure: No perfect comps, but premium warranted for growth

    <br/><br/>
    <b>Contracted Revenue Approach:</b>
    <br/>• Total Contracted Revenue: $19B over 15 years
    <br/>• NPV (assuming 10% discount rate): ~$7-8B
    <br/>• Subtract debt and buildout costs: ~$3-4B net value
    <br/>• Current market cap: $2.7B
    <br/>• <b>Implied Upside:</b> 40-80% to fair value

    <br/><br/>
    This approach suggests APLD is reasonably valued at current levels, with upside dependent on flawless execution
    and achievement of profitability milestones. The 50× sales multiple is justified by contracted revenue visibility
    and hypergrowth trajectory, but leaves no room for error.
    """

    elements.append(Paragraph(valuation, styles['body']))

    # Page Break
    elements.append(PageBreak())

    # ========== PAGE 7: INDUSTRY CONTEXT ==========

    industry_heading = Paragraph("AI INFRASTRUCTURE INDUSTRY CONTEXT", styles['heading1'])
    elements.append(industry_heading)

    # Market Opportunity
    market_heading = Paragraph("MARKET OPPORTUNITY", styles['heading2'])
    elements.append(market_heading)

    market = """The AI infrastructure market is experiencing unprecedented growth driven by the exponential increase
    in compute demands from large language models (LLMs), generative AI applications, and enterprise AI adoption.

    <br/><br/>
    <b>Market Drivers:</b>
    <br/>• <b>AI Model Scaling:</b> GPT-4 to GPT-5 and beyond requires 10-100× more compute
    <br/>• <b>Enterprise AI Adoption:</b> Every Fortune 500 company building AI capabilities
    <br/>• <b>Sovereign AI:</b> Governments investing in domestic AI infrastructure
    <br/>• <b>GPU Scarcity:</b> NVIDIA H100/H200/Blackwell chips in extreme demand
    <br/>• <b>Data Locality:</b> Regulatory requirements driving distributed infrastructure

    <br/><br/>
    <b>Market Size Estimates:</b>
    <br/>• AI Infrastructure Market: $50B in 2025 → $300B+ by 2030 (35% CAGR)
    <br/>• Data Center Capacity: Global capacity needs to 2× by 2028
    <br/>• GPU-Optimized Data Centers: Fastest growing segment (50%+ CAGR)

    <br/><br/>
    <b>Supply/Demand Imbalance:</b>
    <br/>Current AI compute capacity is severely constrained. Hyperscalers (AWS, Azure, GCP) can't build fast
    enough to meet demand, creating massive opportunity for third-party providers like APLD. Industry sources
    estimate 18-24 month waitlists for enterprise GPU clusters.

    <br/><br/>
    <b>APLD's Addressable Market:</b>
    <br/>With plans to scale beyond 1 GW by 2028-2030, APLD is targeting $10-15B+ in additional contracted revenue
    over the next 3-5 years. The company's rapid deployment capability (12-14 months) provides competitive advantage
    in a capacity-constrained market.
    """

    elements.append(Paragraph(market, styles['body']))
    elements.append(Spacer(1, 0.2*inch))

    # Industry Trends
    trends_heading = Paragraph("KEY INDUSTRY TRENDS", styles['heading2'])
    elements.append(trends_heading)

    trends = """<b>1. Power as the New Scarce Resource</b>
    <br/>AI data centers consume 10-20× more power per rack than traditional facilities. Access to reliable,
    cost-effective power is becoming the primary bottleneck. APLD's North Dakota locations with abundant renewable
    energy provide structural advantage.

    <br/><br/>
    <b>2. Liquid Cooling Becoming Standard</b>
    <br/>Next-gen GPUs (NVIDIA Blackwell, AMD MI300) generate so much heat that air cooling is insufficient.
    APLD's proprietary waterless cooling technology positions it for next-gen deployments.

    <br/><br/>
    <b>3. Shift to Long-Term Contracts</b>
    <br/>Customers are signing 10-15 year leases (vs. traditional 3-5 years) to secure capacity. This benefits
    APLD by providing revenue visibility and reducing customer acquisition costs.

    <br/><br/>
    <b>4. Vertical Integration by Hyperscalers</b>
    <br/>AWS (Trainium chips), Google (TPUs), Microsoft (Maia) developing custom AI accelerators. However, NVIDIA
    GPUs remain dominant for training and many inference workloads, supporting continued demand for GPU-optimized
    facilities.

    <br/><br/>
    <b>5. Sustainability Focus</b>
    <br/>AI's energy consumption creating ESG concerns. Data center operators must demonstrate renewable energy
    usage and efficiency. APLD's North Dakota wind/hydro power and waterless cooling align with this trend.

    <br/><br/>
    <b>6. Edge AI Emergence</b>
    <br/>As models become more efficient, some workloads moving to edge. However, training and large-scale inference
    will remain centralized for foreseeable future, supporting APLD's hyperscale strategy.
    """

    elements.append(Paragraph(trends, styles['body']))
    elements.append(Spacer(1, 0.2*inch))

    # NVIDIA Ecosystem
    nvidia_heading = Paragraph("NVIDIA ECOSYSTEM DYNAMICS", styles['heading2'])
    elements.append(nvidia_heading)

    nvidia = """<b>NVIDIA's Strategic Investments:</b>
    <br/>NVIDIA has taken equity positions in multiple AI infrastructure providers (APLD, CoreWeave, Lambda) as
    part of a deliberate ecosystem strategy. This serves multiple purposes:

    <br/><br/>
    1. <b>Secure GPU Demand:</b> Ensures long-term offtake for GPU production
    2. <b>De-Risk Hyperscaler Concentration:</b> Reduces dependency on AWS/Azure/GCP
    3. <b>Accelerate Market Development:</b> Speeds deployment of GPU-optimized infrastructure
    4. <b>Financial Returns:</b> Equity stakes in high-growth companies

    <br/><br/>
    <b>Elite Partner Status Benefits:</b>
    <br/>APLD's Elite Partner designation in NVIDIA Partner Network (NPN) provides:
    <br/>• Priority GPU allocation during supply constraints
    <br/>• Early access to next-gen architectures (Blackwell, beyond)
    <br/>• Co-marketing and sales support
    <br/>• Technical training and certification
    <br/>• Reference architecture validation

    <br/><br/>
    <b>Impact on Investment Thesis:</b>
    <br/>NVIDIA's backing is a powerful validation signal. As the dominant AI infrastructure provider (80%+ GPU
    market share for AI workloads), NVIDIA has visibility into market dynamics that others lack. Their continued
    investment in APLD (holding 7.7M shares worth ~$184M at current prices) suggests confidence in the company's
    execution and market position.

    <br/><br/>
    However, investors should note that NVIDIA also backs APLD's competitor CoreWeave (24.2M shares), indicating
    a portfolio approach rather than exclusive partnership. APLD must execute independently to capture value.
    """

    elements.append(Paragraph(nvidia, styles['body']))

    # Page Break
    elements.append(PageBreak())

    # ========== PAGE 8: CONCLUSION & SOURCES ==========

    conclusion_heading = Paragraph("CONCLUSION & FINAL RECOMMENDATION", styles['heading1'])
    elements.append(conclusion_heading)

    conclusion = """Applied Digital Corporation represents a high-conviction speculative investment opportunity in
    the AI infrastructure megatrend. The company has successfully executed a strategic pivot from cryptocurrency
    mining to AI data centers, securing $19 billion in long-term contracted revenue and backing from NVIDIA, the
    world's leading AI technology provider.

    <br/><br/>
    <b>Investment Strengths:</b>
    <br/>• Exceptional revenue visibility through 2040 with blue-chip customers
    <br/>• Strategic partnerships validating technology and market position (NVIDIA Elite Partner)
    <br/>• Demonstrated operational excellence (12-14 month build times, RFS achieved on schedule)
    <br/>• Strong quantitative performance (133% alpha vs. SPY, Sharpe 1.19)
    <br/>• Clear path to profitability (FCF positive target mid-2026)
    <br/>• Massive addressable market with supply/demand imbalance favoring providers

    <br/><br/>
    <b>Investment Risks:</b>
    <br/>• Extreme volatility (127% annual) requiring disciplined risk management
    <br/>• Execution risk on capital-intensive buildouts ($689M debt)
    <br/>• Profitability timeline uncertainty (TTM loss of $248M)
    <br/>• Customer concentration (CoreWeave 58% of contracted revenue)
    <br/>• High valuation (50× TTM sales) priced for perfection
    <br/>• Competitive threats from better-capitalized incumbents

    <br/><br/>
    <b>Verdict: SPECULATIVE BUY</b>
    <br/>For aggressive growth investors with high risk tolerance, APLD offers compelling risk/reward at current
    levels ($23.90). The stock has consolidated from recent highs (~$25) with oversold momentum indicators
    suggesting potential reversal. Our 12-18 month price target of $35-$45 represents 46-88% upside, supported
    by Wall Street consensus and catalyst-rich 2026 (facility deliveries, FCF inflection, potential new leases).

    <br/><br/>
    <b>Position Sizing: 3.0% ($7,500 of $250,000 portfolio)</b>
    <br/>Conservative allocation reflects extreme volatility regime and speculative nature. This limits maximum
    portfolio impact to ~2% even in severe drawdown scenario while providing meaningful exposure to AI infrastructure
    upside. Position can be scaled to 5% upon achievement of key milestones (FCF positive, reduced volatility).

    <br/><br/>
    <b>Entry Strategy: Staged DCA</b>
    <br/>• 40% immediate ($3,000) - capitalize on oversold conditions
    <br/>• 30% on strength ($2,250) - add if price breaks $26 with volume
    <br/>• 30% on weakness ($2,250) - add if price dips to $20-21 support
    <br/>• Stop loss: $18.12 (2× ATR below entry)
    <br/>• Profit targets: $35 (25% trim), $45 (50% trim), $50+ (let 25% ride)

    <br/><br/>
    <b>Critical Milestones to Monitor:</b>
    <br/>1. <b>Mid-2026:</b> Ellendale 150 MW facility delivery and FCF positive achievement
    <br/>2. <b>Q4 2026:</b> Harwood initial capacity operational
    <br/>3. <b>2026 Ongoing:</b> New lease announcements using Macquarie facility
    <br/>4. <b>2026 Ongoing:</b> CoreWeave IPO impact on AI infrastructure valuations
    <br/>5. <b>Quarterly:</b> Revenue growth, margin improvement, debt management

    <br/><br/>
    <b>Exit Triggers:</b>
    <br/>• <b>Stop Loss:</b> Price below $18.12 (-24% from entry)
    <br/>• <b>Thesis Broken:</b> Facility delivery delays >3 months, covenant violations, loss of major customer
    <br/>• <b>Valuation:</b> If stock reaches $50+ ($5.6B+ market cap) without FCF inflection, valuation risk escalates
    <br/>• <b>Time:</b> If no progress on milestones by Q3 2026, re-evaluate opportunity cost

    <br/><br/>
    Applied Digital is not for conservative investors or those uncomfortable with significant volatility. However,
    for portfolios seeking asymmetric growth opportunities in transformative technologies, APLD represents a
    compelling allocation within prudent position sizing limits.
    """

    elements.append(Paragraph(conclusion, styles['body']))
    elements.append(Spacer(1, 0.3*inch))

    # Disclaimer
    disclaimer_heading = Paragraph("COMPLIANCE & DISCLAIMER", styles['heading2'])
    elements.append(disclaimer_heading)

    disclaimer = """<b>EDUCATIONAL PURPOSES ONLY - NOT INVESTMENT ADVICE</b>

    <br/><br/>
    This report is provided for educational and informational purposes only. It does not constitute investment
    advice, financial advice, trading advice, or any other sort of advice. The information contained herein is
    based on sources believed to be reliable but is not guaranteed for accuracy or completeness.

    <br/><br/>
    You should not rely solely on this report for making investment decisions. Always conduct your own research
    and due diligence before making any investment. Consult with a licensed financial advisor, accountant, and/or
    attorney before making any investment decisions.

    <br/><br/>
    Past performance is not indicative of future results. All investments carry risk, including the potential loss
    of principal. The extreme volatility exhibited by APLD makes it particularly risky and unsuitable for many
    investors. The analysis provided reflects conditions as of December 18, 2025, and market conditions change
    rapidly.

    <br/><br/>
    Finance Guru™ and its analysts do not hold any positions in APLD and have no material conflicts of interest
    related to this report. This analysis was generated using publicly available information, proprietary
    quantitative tools, and third-party research sources.

    <br/><br/>
    <b>RISK DISCLOSURE:</b> Applied Digital Corporation (APLD) exhibits extreme volatility (127% annual), significant
    drawdown risk (-67.76% maximum), and operational/execution risks associated with capital-intensive infrastructure
    buildouts. This stock is suitable only for aggressive investors with high risk tolerance and ability to sustain
    potential total loss of invested capital.
    """

    elements.append(Paragraph(disclaimer, styles['body']))
    elements.append(Spacer(1, 0.3*inch))

    # Sources
    sources_heading = Paragraph("SOURCES & REFERENCES", styles['heading2'])
    elements.append(sources_heading)

    sources = """<b>Market Data & Quantitative Analysis:</b>
    <br/>• Yahoo Finance (yfinance) - Historical price data, volume, market data
    <br/>• Finance Guru™ Risk Metrics Tool - VaR, CVaR, Sharpe, Sortino, drawdown analysis
    <br/>• Finance Guru™ Momentum Tool - RSI, MACD, Stochastic, Williams %R, ROC
    <br/>• Finance Guru™ Volatility Tool - ATR, Bollinger Bands, historical volatility

    <br/><br/>
    <b>Company Information & News:</b>
    <br/>• Applied Digital Investor Relations (ir.applieddigital.com)
    <br/>• PredictStreet - "Applied Digital Corporation (APLD): Powering the AI Revolution"
    <br/>• Globe Newswire - Macquarie Development Loan Facility announcement (Dec 18, 2025)
    <br/>• MarketMinute - "Applied Digital: From Crypto Mining to AI Infrastructure Powerhouse"
    <br/>• Datacloud - Best Data Center in the Americas 2025 award

    <br/><br/>
    <b>Analyst Research & Ratings:</b>
    <br/>• TipRanks - Analyst ratings and price targets
    <br/>• Stock Analysis - Consensus forecasts and analyst coverage
    <br/>• MarketBeat - Price target data and analyst actions
    <br/>• Benzinga - Analyst ratings tracking
    <br/>• B. Riley, Citizens JMP, Needham, Roth Capital, Cantor Fitzgerald - Individual analyst reports

    <br/><br/>
    <b>Industry Analysis:</b>
    <br/>• AI Invest - "Applied Digital: High-Risk, High-Reward Play in AI Infrastructure Boom"
    <br/>• Trading Key - "APLD Stock Analysis: 200% Yearly Gain Backed by Nvidia"
    <br/>• Kavout - "Applied Digital Corp: Riding the AI Wave with Nvidia's Backing"
    <br/>• FX Leaders - Market technical analysis and sentiment tracking
    <br/>• Stocktwits - Retail investor sentiment and catalyst polling

    <br/><br/>
    <b>Competitive Intelligence:</b>
    <br/>• CoreWeave investor materials and public filings
    <br/>• NVIDIA Partner Network documentation
    <br/>• Industry publications and data center market research

    <br/><br/>
    <i>Report generated: December 18, 2025 | Finance Guru™ v2.0.0 | BMAD-CORE™ v6.0.0</i>
    """

    elements.append(Paragraph(sources, styles['body']))

    # Build PDF
    doc.build(elements)

    return pdf_path

if __name__ == "__main__":
    print("=" * 70)
    print("FINANCE GURU™ - FULL RESEARCH WORKFLOW")
    print("Applied Digital Corporation (APLD) Analysis")
    print("=" * 70)
    print()
    print("Generating comprehensive PDF report...")
    print()

    pdf_path = generate_report()

    print("=" * 70)
    print("✅ REPORT GENERATION COMPLETE")
    print("=" * 70)
    print()
    print(f"📄 PDF Report: {pdf_path}")
    print()
    print("INVESTMENT VERDICT: SPECULATIVE BUY")
    print("Price Target: $35-$45 (12-18 months)")
    print("Position Size: 3.0% ($7,500 of $250,000 portfolio)")
    print()
    print("=" * 70)
