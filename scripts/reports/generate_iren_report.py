#!/usr/bin/env python3
"""
Generate comprehensive IREN analysis PDF report
Finance Guru - Private Family Office Analysis
Date: 2025-12-18
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

def create_iren_report():
    """Generate comprehensive IREN analysis PDF"""

    # Output path
    output_path = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports/IREN-analysis-2025-12-18.pdf"

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        alignment=TA_LEFT
    )

    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['BodyText'],
        fontSize=8,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )

    # ============================================================
    # TITLE PAGE
    # ============================================================

    elements.append(Spacer(1, 0.5*inch))

    elements.append(Paragraph("IREN LIMITED (IREN)", title_style))
    elements.append(Paragraph("Full Research Analysis - Speculative Bitcoin Mining & AI Play", heading1_style))
    elements.append(Spacer(1, 0.3*inch))

    # Executive Summary Box
    summary_data = [
        ['Analyst Team:', 'Finance Guru Research Division'],
        ['Current Price:', '$35.80 (Dec 18, 2025)'],
        ['YTD Performance:', '+269%'],
        ['52-Week Range:', '$4.20 - $68.23'],
        ['Market Cap:', '~$7.4B (est.)'],
        ['Sector:', 'Bitcoin Mining & AI Cloud Services']
    ]

    summary_table = Table(summary_data, colWidths=[2.5*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))

    # Verdict Box
    verdict_data = [
        ['INVESTMENT VERDICT:', 'SPECULATIVE BUY - 1-2% MAX POSITION'],
        ['Rating:', 'HIGH RISK / HIGH REWARD'],
        ['Recommended Position Size:', '$2,500 - $5,000 (1-2% of $250K portfolio)'],
        ['Entry Strategy:', 'Scale in over 2-3 weeks during weakness']
    ]

    verdict_table = Table(verdict_data, colWidths=[2.5*inch, 3*inch])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#856404')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#ffc107'))
    ]))

    elements.append(verdict_table)
    elements.append(Spacer(1, 0.2*inch))

    # Critical Alert
    alert_text = """<b><font color='red'>CRITICAL RISK ALERT:</font></b> IREN is an EXTREME VOLATILITY position
    with 97.75% annual volatility, -65.56% max drawdown, and 2.16 beta. Recent correction from $68 to $35 (-49%)
    demonstrates the brutal volatility. This is a speculative "moonshot" allocation - only invest what you can
    afford to lose completely. Position sizing discipline is MANDATORY."""
    elements.append(Paragraph(alert_text, body_style))

    elements.append(PageBreak())

    # ============================================================
    # PHASE 1: MARKET RESEARCH
    # ============================================================

    elements.append(Paragraph("PHASE 1: Market Research & Company Analysis", heading1_style))
    elements.append(Paragraph("Dr. Aleksandr Petrov - Market Intelligence", heading2_style))

    elements.append(Paragraph("<b>Company Overview:</b>", body_style))
    overview = """IREN Limited (formerly Iris Energy) is a Sydney-based vertically integrated data center
    company operating Bitcoin mining and AI cloud computing infrastructure. Founded in 2018, IREN built its
    brand on 100% renewable energy-powered Bitcoin mining but is now aggressively pivoting to AI cloud services.
    The company operates facilities in British Columbia (Canada) and Texas (USA), leveraging low-cost hydroelectric
    and renewable power ($0.038/kWh average)."""
    elements.append(Paragraph(overview, body_style))
    elements.append(Spacer(1, 0.1*inch))

    elements.append(Paragraph("<b>The Dual-Engine Business Model:</b>", body_style))

    business_data = [
        ['Business Segment', 'Current Status', 'Target', 'Strategic Focus'],
        ['Bitcoin Mining', '50 EH/s capacity', '$1B+ annual revenue', 'Low-cost renewable mining'],
        ['AI Cloud Services', '23,000 GPUs deployed', '$500M+ ARR by Q1 2026', 'Hyperscale AI infrastructure'],
        ['Data Centers', '1.4 GW pipeline (Sweetwater)', 'April 2026 energization', 'Direct-to-chip liquid cooling'],
        ['Energy Foundation', '100% renewable power', '$0.038/kWh cost', 'ESG advantage & cost efficiency']
    ]

    business_table = Table(business_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.7*inch])
    business_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(business_table)
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph("<b>2025 Financial Performance - The Breakout Year:</b>", body_style))
    performance = """Fiscal Year 2025 marked IREN's first profitable year with stunning results:
    <br/>• <b>Total Revenue:</b> $501M (+168% YoY)
    <br/>• <b>Net Income:</b> $86.9M (profitable for first time)
    <br/>• <b>Q1 FY2026 Revenue:</b> $240.3M (+355% YoY)
    <br/>• <b>Q1 EBITDA:</b> $91.5M (36x YoY growth)
    <br/>• <b>Stock Performance:</b> +269% YTD (up ~800% from 2022 lows)
    <br/>• <b>Recent Correction:</b> -49% from November 2025 high of $68.23
    """
    elements.append(Paragraph(performance, body_style))
    elements.append(Spacer(1, 0.1*inch))

    elements.append(Paragraph("<b>The Strategic Pivot: Solving the Bitcoin Halving Problem</b>", body_style))
    pivot = """Bitcoin mining faces a structural challenge - rewards drop 50% every 4 years at "halving" events.
    IREN's dual-engine strategy addresses this by diversifying into the AI boom:
    <br/>• <b>NVIDIA Partnership:</b> Preferred Partner status, orders for B300, B200, GB300, AMD MI350X GPUs
    <br/>• <b>GPU Fleet:</b> Expanded to 23,000 GPUs (September 2025), targeting $500M+ AI ARR
    <br/>• <b>Microsoft Deal:</b> Multi-billion dollar AI cloud services agreement (with delivery risks)
    <br/>• <b>Infrastructure:</b> 75MW liquid-cooled facility (Horizon 1) coming Q4 2025
    <br/>• <b>Sweetwater Pipeline:</b> 1.4 GW mega-facility scheduled for April 2026
    <br/><br/>
    This strategy tackles Bitcoin's "halving problem" by tapping into AI's global boom while maintaining
    low-cost mining economics that favor efficient operators post-halving."""
    elements.append(Paragraph(pivot, body_style))

    elements.append(PageBreak())

    elements.append(Paragraph("<b>2026 Catalysts - What Could Drive the Stock:</b>", heading2_style))

    catalysts_data = [
        ['Catalyst', 'Timeline', 'Potential Impact', 'Risk Factor'],
        ['AI Cloud ARR Target', 'Q1 2026', '$500M+ annual revenue run rate', 'Execution dependent'],
        ['Sweetwater Facility', 'April 2026', '1.4 GW capacity energization', 'Delivery schedule risk'],
        ['Microsoft Contract', 'Ongoing', 'Multi-billion $ revenue potential', 'Termination if delays'],
        ['Bitcoin Halving Effects', '2024-2026', 'Low-cost miners gain market share', 'BTC price volatility'],
        ['GPU Deployments', 'Q4 2025-Q1 2026', '23,000+ GPUs generating revenue', 'Installation pace'],
        ['Profitability Scale', '2026 Target', '$500M annualized EBITDA', 'Margin pressure risks']
    ]

    catalysts_table = Table(catalysts_data, colWidths=[1.4*inch, 1.2*inch, 1.8*inch, 1.8*inch])
    catalysts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#d5f4e6')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(catalysts_table)
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph("<b>Analyst Sentiment & Price Targets:</b>", body_style))
    analyst = """Wall Street is increasingly bullish on IREN's AI pivot, though recent weakness has created divergence:
    <br/>• <b>Consensus Rating:</b> BUY (9-10 analysts)
    <br/>• <b>Average Price Target:</b> $72.56 (+103% from current $35.80)
    <br/>• <b>High Target:</b> $136 (Cantor Fitzgerald, November 2025)
    <br/>• <b>Bull Case Range:</b> $75-136 (based on AI scaling)
    <br/>• <b>Recent Activity:</b> Multiple upgrades in Q4 2025 as AI strategy gained traction
    <br/>• <b>Skeptical View:</b> Some analysts cite stagnant GPU installations and rising electricity costs
    <br/><br/>
    <b>Roth Capital:</b> $82 target (Buy rating), citing dual-engine model
    <br/><b>Bernstein:</b> $75 target, bullish on AI cloud revenue potential
    <br/><b>Projections (Bull Case):</b> $2.7B revenue, $1.2B EBITDA by FY2028
    """
    elements.append(Paragraph(analyst, body_style))

    elements.append(PageBreak())

    elements.append(Paragraph("<b>Key Risks - What Could Go Wrong:</b>", heading2_style))

    risks_data = [
        ['Risk Category', 'Specific Risk', 'Severity', 'Mitigation'],
        ['Bitcoin Volatility', 'BTC price crash would hurt mining revenue', 'EXTREME', 'AI diversification'],
        ['Execution Risk', 'Microsoft deal termination if delivery delays', 'HIGH', 'Accelerated GPU deployment'],
        ['Energy Costs', 'Rising electricity costs despite renewables', 'MEDIUM', '$0.038/kWh cost advantage'],
        ['Competition', 'Other miners pivoting to AI (MARA, RIOT, etc.)', 'HIGH', 'First-mover advantage'],
        ['Stock Volatility', '97.75% annual vol, -49% recent correction', 'EXTREME', 'Position size discipline'],
        ['Capital Intensity', '$842M in GPU orders (Sept 2025)', 'MEDIUM', 'Strong balance sheet'],
        ['Regulatory', 'Crypto/AI regulation uncertainty', 'MEDIUM', 'Multi-jurisdiction operations']
    ]

    risks_table = Table(risks_data, colWidths=[1.2*inch, 2*inch, 1*inch, 2*inch])
    risks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fadbd8')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(risks_table)
    elements.append(Spacer(1, 0.15*inch))

    risk_summary = """<font color='red'><b>RISK VERDICT:</b></font> IREN carries EXTREME risk due to Bitcoin
    price sensitivity, execution challenges (Microsoft contract), and brutal stock volatility. The -49% correction
    from November highs ($68 to $35) in just 6 weeks demonstrates how fast this can move against you. However,
    the AI pivot is REAL (not vaporware), the company is profitable, and analysts see 100%+ upside IF execution
    continues."""
    elements.append(Paragraph(risk_summary, body_style))

    elements.append(PageBreak())

    # ============================================================
    # PHASE 2: QUANTITATIVE ANALYSIS
    # ============================================================

    elements.append(Paragraph("PHASE 2: Quantitative Analysis", heading1_style))
    elements.append(Paragraph("Dr. Priya Desai - Risk & Performance Metrics", heading2_style))

    elements.append(Paragraph("<b>Risk Metrics (252-Day Analysis vs SPY):</b>", heading2_style))

    risk_data = [
        ['Metric', 'Value', 'Interpretation', 'Rating'],
        ['Annual Return', '+133.13%', 'Exceptional performance', '⭐⭐⭐⭐⭐'],
        ['Sharpe Ratio', '1.32', 'Good risk-adjusted returns', '⭐⭐⭐⭐'],
        ['Sortino Ratio', '2.07', 'Strong downside protection', '⭐⭐⭐⭐⭐'],
        ['Max Drawdown', '-65.56%', 'CATASTROPHIC worst-case decline', '⛔⛔⛔'],
        ['Calmar Ratio', '2.03', 'Strong return vs drawdown', '⭐⭐⭐⭐'],
        ['Annual Volatility', '97.75%', 'EXTREME volatility', '⛔⛔⛔'],
        ['95% VaR (Daily)', '-9.61%', '5% chance of >9.61% loss/day', '⚠️⚠️'],
        ['95% CVaR (Daily)', '-12.92%', 'Average tail loss is brutal', '⚠️⚠️⚠️'],
        ['Beta vs SPY', '2.16', '2.16x market volatility', '⚠️⚠️⚠️'],
        ['Alpha vs SPY', '+110.46%', 'Massive outperformance', '⭐⭐⭐⭐⭐']
    ]

    risk_table = Table(risk_data, colWidths=[1.5*inch, 1.2*inch, 2.2*inch, 1.3*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold')
    ]))

    elements.append(risk_table)
    elements.append(Spacer(1, 0.15*inch))

    risk_summary = """<b>CRITICAL RISK INTERPRETATION:</b> IREN delivers spectacular returns (+110.46% alpha,
    +133% annual return) BUT with bone-crushing volatility. The -65.56% max drawdown means you could lose 2/3
    of your investment at any time. The 97.75% annual volatility is EXTREME - for context, SPY has ~15-20%
    volatility. The 2.16 beta means IREN moves 2x the market on average. CVaR of -12.92% means when bad days
    happen, they're REALLY bad (average loss >12% on worst days).
    <br/><br/>
    <b>Bottom Line:</b> This is NOT a core holding. This is a speculative "asymmetric bet" where you size small
    enough to survive the volatility but large enough to matter if it works."""
    elements.append(Paragraph(risk_summary, body_style))

    elements.append(PageBreak())

    elements.append(Paragraph("<b>Momentum Analysis (90-Day):</b>", heading2_style))

    momentum_data = [
        ['Indicator', 'Value', 'Signal', 'Interpretation'],
        ['RSI', '32.81', 'Neutral', 'No extreme condition'],
        ['MACD', '-4.19 / -3.30', 'Bearish', 'MACD below signal (downward momentum)'],
        ['Stochastic', '2.42 / 7.02', 'OVERSOLD', '%K < 20, potential reversal up'],
        ['Williams %R', '-97.58', 'OVERSOLD', '%R < -80, potential buy signal'],
        ['ROC', '-30.34%', 'Bearish', 'Negative momentum (30% loss)'],
        ['Confluence', '2/5 Bullish', 'MIXED', 'No clear directional bias']
    ]

    momentum_table = Table(momentum_data, colWidths=[1.5*inch, 1.3*inch, 1.2*inch, 2.2*inch])
    momentum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))

    elements.append(momentum_table)
    elements.append(Spacer(1, 0.15*inch))

    momentum_summary = """<b>Momentum Assessment:</b> IREN is deeply OVERSOLD after the brutal -49% correction
    from $68 to $35. Stochastic at 2.42 and Williams %R at -97.58 are screaming oversold - these are extreme
    readings that often precede bounces. However, MACD is bearish and ROC shows -30% momentum, indicating the
    downtrend hasn't fully reversed yet.
    <br/><br/>
    <b>Tactical View:</b> This is a classic "falling knife" scenario. The oversold readings suggest we're near
    a bounce zone, but you don't want to catch the knife on the way down. A scale-in approach over 2-3 weeks
    makes sense - buy some here at $35, more if it dips to $30-32, and more on a confirmed reversal above $40-42."""
    elements.append(Paragraph(momentum_summary, body_style))

    elements.append(PageBreak())

    elements.append(Paragraph("<b>Volatility Analysis (90-Day):</b>", heading2_style))

    vol_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['Current Price', '$35.80', 'Down -49% from $68.23 ATH'],
        ['Volatility Regime', 'EXTREME', 'Maximum caution - 1-2% position only'],
        ['ATR (14-day)', '$4.09 (11.41%)', 'Massive daily range'],
        ['2x ATR Stop', '$8.17', 'Suggested stop-loss distance'],
        ['Annual Volatility', '113.12%', 'Off-the-charts volatility'],
        ['Bollinger Bands', '$33.85 - $52.70', 'Price at lower band (support)'],
        ['%B Position', '0.103 (10%)', 'Near bottom of range'],
        ['Bandwidth', '43.56%', 'Very wide bands - high vol environment']
    ]

    vol_table = Table(vol_data, colWidths=[2*inch, 1.8*inch, 2.4*inch])
    vol_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))

    elements.append(vol_table)
    elements.append(Spacer(1, 0.15*inch))

    vol_summary = """<b>Volatility Context:</b> IREN is in EXTREME volatility regime (113.12% annual vol).
    The 11.41% ATR means typical daily swings of $4.09 - that's massive. Price is currently at the lower
    Bollinger Band ($33.85), which often acts as support. The %B at 0.103 (10% of band range) confirms we're
    at the bottom of the recent trading range.
    <br/><br/>
    <b>Trading Range:</b> Support at $30-33 (lower BB), resistance at $42-45 (middle BB), strong resistance
    at $50-53 (upper BB). The wide 43.56% bandwidth tells you this stock can swing violently - $8-10 daily
    moves are normal."""
    elements.append(Paragraph(vol_summary, body_style))

    elements.append(PageBreak())

    # ============================================================
    # PHASE 3: STRATEGY RECOMMENDATION
    # ============================================================

    elements.append(Paragraph("PHASE 3: Strategic Recommendation", heading1_style))
    elements.append(Paragraph("Elena Rodriguez-Park - Portfolio Strategy", heading2_style))

    elements.append(Paragraph("<b>Investment Thesis - Why Consider IREN?</b>", heading2_style))

    thesis = """Despite the extreme volatility and risks, IREN presents a compelling asymmetric opportunity
    for a SMALL speculative allocation:
    <br/><br/>
    <b>BULLISH FACTORS:</b>
    <br/>1. <b>Dual Revenue Streams:</b> Bitcoin mining ($1B+ ARR) + AI cloud ($500M+ ARR target) = diversified model
    <br/>2. <b>Profitable & Scaling:</b> First profitable year (FY25), $501M revenue (+168% YoY)
    <br/>3. <b>AI Infrastructure Real:</b> 23,000 GPUs, NVIDIA Preferred Partner, Microsoft contract
    <br/>4. <b>Cost Advantage:</b> $0.038/kWh renewable energy = lowest-cost miner, favored post-halving
    <br/>5. <b>Analyst Support:</b> $72 average target (+103%), $136 high target (+280%)
    <br/>6. <b>Oversold Technicals:</b> -49% from highs, stochastic/Williams %R screaming oversold
    <br/>7. <b>Growth Pipeline:</b> 1.4 GW Sweetwater (April 2026), 75MW Horizon 1 (Q4 2025)
    <br/><br/>
    <b>BEARISH FACTORS:</b>
    <br/>1. <b>Catastrophic Volatility:</b> -65.56% max drawdown, 97.75% annual vol, 2.16 beta
    <br/>2. <b>Bitcoin Dependency:</b> BTC crash would devastate mining revenue despite diversification
    <br/>3. <b>Execution Risk:</b> Microsoft deal can be terminated if deliveries delayed
    <br/>4. <b>Recent Correction:</b> -49% from $68 to $35 shows how brutal this can get
    <br/>5. <b>Competitive Threat:</b> All Bitcoin miners pivoting to AI (MARA, RIOT, CLSK, etc.)
    <br/>6. <b>Capital Intensity:</b> $842M GPU orders strain balance sheet
    <br/>7. <b>Regulatory Uncertainty:</b> Crypto/AI regulation could impact business model
    """
    elements.append(Paragraph(thesis, body_style))

    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>FINAL RECOMMENDATION: SPECULATIVE BUY</b>", heading1_style))

    recommendation = """
    <font color='#16a085'><b>VERDICT: SPECULATIVE BUY - 1-2% MAX POSITION SIZE</b></font><br/><br/>

    <b>Recommended Allocation for $250,000 Portfolio:</b><br/>
    • <b>Conservative (1%):</b> $2,500 investment = ~70 shares at $35.80<br/>
    • <b>Moderate (1.5%):</b> $3,750 investment = ~105 shares at $35.80<br/>
    • <b>Aggressive (2%):</b> $5,000 investment = ~140 shares at $35.80<br/>
    <br/>
    <b>Entry Strategy - Scale In Over 2-3 Weeks:</b><br/>
    1. <b>Tranche 1 (40%):</b> Buy NOW at $35-36 (current oversold level)<br/>
    2. <b>Tranche 2 (30%):</b> Buy if dips to $30-32 (deeper correction)<br/>
    3. <b>Tranche 3 (30%):</b> Buy on confirmed reversal above $40-42 (momentum confirmation)<br/>
    <br/>
    <b>Example for $3,750 Moderate Allocation:</b><br/>
    • <b>Buy 1:</b> $1,500 at $35.80 = 42 shares (NOW)<br/>
    • <b>Buy 2:</b> $1,125 at $31.00 = 36 shares (IF drops)<br/>
    • <b>Buy 3:</b> $1,125 at $41.00 = 27 shares (IF bounces)<br/>
    • <b>Total:</b> ~105 shares, $35.71 average (if all tranches execute)<br/>
    <br/>
    <b>Risk Management (NON-NEGOTIABLE):</b><br/>
    • <b>Stop Loss:</b> 2x ATR = $27.63 (exit if breaks below this)<br/>
    • <b>Portfolio Cap:</b> NEVER exceed 2% allocation (this is speculative money)<br/>
    • <b>Rebalance Trigger:</b> If IREN grows to >3% of portfolio, trim back to 2%<br/>
    • <b>Profit Taking:</b> Sell 50% if it hits $72 (analyst avg target), let rest ride<br/>
    • <b>Moon Shot:</b> Sell another 25% at $100-110 (lock in gains), hold 25% for $136+ target<br/>
    <br/>
    <b>Why This Approach Works:</b><br/>
    1. <b>Asymmetric Bet:</b> Risk 1-2% to potentially gain 100-200% if AI pivot succeeds<br/>
    2. <b>Oversold Entry:</b> Buying after -49% correction reduces downside risk<br/>
    3. <b>Defined Risk:</b> 1-2% position means max loss is $2,500-5,000 (painful but not catastrophic)<br/>
    4. <b>Upside Optionality:</b> If IREN hits $136 target, your $3,750 becomes $14,280 (+280%)<br/>
    5. <b>Catalyst Timeline:</b> Q4 2025 (Horizon 1) and Q1 2026 (Sweetwater, $500M AI ARR) provide near-term catalysts<br/>
    """
    elements.append(Paragraph(recommendation, body_style))

    elements.append(PageBreak())

    elements.append(Paragraph("<b>Scenario Analysis: What Could Happen in 2026?</b>", heading2_style))

    scenario_data = [
        ['Scenario', 'Probability', 'Price Target', '$3,750 Position Value', 'Return'],
        ['Moon Shot', '15%', '$100-136', '$10,500-14,280', '+180% to +280%'],
        ['Bull Case', '25%', '$60-80', '$6,300-8,400', '+68% to +124%'],
        ['Base Case', '30%', '$45-55', '$4,725-5,775', '+26% to +54%'],
        ['Bear Case', '20%', '$25-35', '$2,625-3,675', '-30% to -2%'],
        ['Crash Case', '10%', '$10-20', '$1,050-2,100', '-72% to -44%']
    ]

    scenario_table = Table(scenario_data, colWidths=[1.2*inch, 1*inch, 1.2*inch, 1.6*inch, 1.2*inch])
    scenario_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#d4edda')),  # Moon
        ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#d4edda')),  # Bull
        ('BACKGROUND', (0, 3), (0, 3), colors.HexColor('#fff3cd')),  # Base
        ('BACKGROUND', (0, 4), (0, 4), colors.HexColor('#f8d7da')),  # Bear
        ('BACKGROUND', (0, 5), (0, 5), colors.HexColor('#f5c6cb')),  # Crash
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(scenario_table)
    elements.append(Spacer(1, 0.15*inch))

    scenario_note = """<b>Expected Value Calculation:</b><br/>
    (0.15 × $12,390) + (0.25 × $7,350) + (0.30 × $5,250) + (0.20 × $3,150) + (0.10 × $1,575)
    = <b>~$5,580</b> (+49% expected return)
    <br/><br/>
    The math suggests positive expected value, driven by the asymmetric payoff structure. You risk losing
    $2,625-3,750 (bear/crash cases, 30% combined probability) to potentially gain $4,725-10,890 (bull/moon
    cases, 40% combined probability). This is the definition of an asymmetric bet."""
    elements.append(Paragraph(scenario_note, body_style))

    elements.append(PageBreak())

    # ============================================================
    # POSITION SIZING & EXECUTION
    # ============================================================

    elements.append(Paragraph("<b>Position Sizing Details ($250,000 Portfolio)</b>", heading2_style))

    sizing_data = [
        ['Allocation', '% of Portfolio', '$ Amount', 'Shares at $35.80', 'Max Loss (to $27.63)', 'Upside to $72'],
        ['Conservative', '1.0%', '$2,500', '70', '-$571 (-23%)', '+$2,534 (+101%)'],
        ['Moderate', '1.5%', '$3,750', '105', '-$857 (-23%)', '+$3,801 (+101%)'],
        ['Aggressive', '2.0%', '$5,000', '140', '-$1,143 (-23%)', '+$5,068 (+101%)']
    ]

    sizing_table = Table(sizing_data, colWidths=[1.1*inch, 1.1*inch, 0.9*inch, 1.1*inch, 1.3*inch, 1.1*inch])
    sizing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#d5f4e6')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(sizing_table)
    elements.append(Spacer(1, 0.15*inch))

    sizing_note = """<b>Position Sizing Logic:</b> The max loss column assumes a stop-loss at $27.63 (2x ATR
    below current price). This would represent a -23% loss from entry. For a 1.5% allocation ($3,750), that's
    a -$857 portfolio impact (0.34% of total portfolio). This is manageable pain.
    <br/><br/>
    The upside to analyst average target ($72) is +101%, which would turn $3,750 into $7,551 (+$3,801). That's
    a 1.5% portfolio boost. The asymmetry (risk 0.34% to gain 1.5%) makes this attractive at small size."""
    elements.append(Paragraph(sizing_note, body_style))

    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>Execution Checklist:</b>", heading2_style))

    checklist = """
    <b>Before You Buy:</b><br/>
    ☐ Confirm you can stomach a -30% to -50% drawdown on this position<br/>
    ☐ Set limit orders (don't chase): $35-36 for Tranche 1, $30-32 for Tranche 2, $40-42 for Tranche 3<br/>
    ☐ Fund brokerage account with cash (don't use margin for this speculative position)<br/>
    ☐ Calculate exact share quantities based on your chosen allocation (1%, 1.5%, or 2%)<br/>
    ☐ Set stop-loss alert at $27.63 (2x ATR below entry)<br/>
    <br/>
    <b>After You Buy:</b><br/>
    ☐ Document purchase price and date for tax records<br/>
    ☐ Set price alerts: $27 (stop loss trigger), $42 (resistance), $60 (bull case), $72 (target), $100 (moon shot)<br/>
    ☐ Add IREN to portfolio tracking (update allocation %)<br/>
    ☐ Calendar reminders: Q4 2025 earnings (Horizon 1 update), Q1 2026 earnings (AI ARR milestone)<br/>
    ☐ Monitor Bitcoin price (IREN correlates heavily with BTC)<br/>
    <br/>
    <b>Rebalancing Triggers:</b><br/>
    ☐ If IREN grows to >3% of portfolio: Trim back to 2% (take profits)<br/>
    ☐ If IREN hits $72: Sell 50% of position (lock in 2x gain, let rest ride)<br/>
    ☐ If IREN hits $100-110: Sell another 25% (lock in 3x gain on that tranche)<br/>
    ☐ If IREN breaks below $27: EXIT entire position (stop loss triggered)<br/>
    ☐ If Bitcoin crashes >30%: Re-evaluate position (IREN will likely follow BTC down)
    """
    elements.append(Paragraph(checklist, body_style))

    elements.append(PageBreak())

    # ============================================================
    # MONITORING & CATALYSTS
    # ============================================================

    elements.append(Paragraph("<b>What to Monitor (Post-Purchase):</b>", heading2_style))

    monitoring = """
    <b>Quarterly Earnings (Critical):</b><br/>
    • <b>Q4 FY2026:</b> Watch for Horizon 1 facility progress (75MW liquid-cooled)<br/>
    • <b>Q1 FY2026:</b> AI Cloud ARR milestone - did they hit $500M+ target?<br/>
    • <b>GPU Deployment Pace:</b> Are they actually installing the 23,000+ GPUs or stalling?<br/>
    • <b>Mining Revenue:</b> Track Bitcoin hashrate and production (should be 50 EH/s+)<br/>
    • <b>EBITDA Margins:</b> Watch for margin compression (energy costs, competition)<br/>
    <br/>
    <b>News Catalysts:</b><br/>
    • <b>Microsoft Contract Updates:</b> Any delivery milestones or termination warnings<br/>
    • <b>Sweetwater Timeline:</b> Delays or acceleration of the 1.4 GW facility (April 2026 target)<br/>
    • <b>Bitcoin Halving Effects:</b> Post-halving dynamics favoring low-cost miners<br/>
    • <b>NVIDIA Partnership:</b> New GPU orders, Preferred Partner status developments<br/>
    • <b>Regulatory News:</b> Crypto mining regulations, energy policy changes<br/>
    <br/>
    <b>Technical Levels:</b><br/>
    • <b>Support:</b> $30-33 (lower Bollinger Band, previous lows)<br/>
    • <b>Resistance:</b> $42-45 (middle BB), $50-53 (upper BB), $60 (psychological), $68 (ATH)<br/>
    • <b>Stop Loss:</b> $27.63 (2x ATR below entry - non-negotiable exit)<br/>
    <br/>
    <b>Macro Factors:</b><br/>
    • <b>Bitcoin Price:</b> IREN heavily correlates with BTC - if BTC crashes, IREN crashes harder<br/>
    • <b>AI Hype Cycle:</b> Is AI infrastructure spending accelerating or decelerating?<br/>
    • <b>Energy Prices:</b> Renewable energy cost trends (IREN's advantage is low-cost power)<br/>
    • <b>Competitor Activity:</b> Are MARA, RIOT, CLSK gaining AI traction? (competitive threat)
    """
    elements.append(Paragraph(monitoring, body_style))

    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>Exit Scenarios - When to Sell:</b>", heading2_style))

    exit_scenarios = """
    <b>MANDATORY EXIT (Stop Loss):</b><br/>
    • <b>Price breaks $27.63:</b> Sell entire position immediately, no questions asked. This is a -23% loss
    from $35.80 entry. Accept the L and move on. Don't baghold a speculative position that's broken support.<br/>
    <br/>
    <b>PROFIT-TAKING EXITS:</b><br/>
    • <b>$72 (Analyst Average Target):</b> Sell 50% of position. You've doubled your money - lock it in.
    Let the other 50% ride for moon shot potential.<br/>
    • <b>$100-110 (3x Return):</b> Sell another 25% of remaining position. You've tripled your money on that
    tranche. Keep 25% of original position for the $136 bull case.<br/>
    • <b>$136 (Cantor Fitzgerald High Target):</b> Sell remaining 25%. You've 3.8x'd your original investment.
    Declare victory and move on.<br/>
    <br/>
    <b>FUNDAMENTAL EXIT TRIGGERS:</b><br/>
    • <b>Microsoft Contract Terminated:</b> Sell entire position immediately. This would be catastrophic for
    the AI cloud thesis.<br/>
    • <b>GPU Deployment Stalls:</b> If quarterly earnings show slow/no progress on GPU installations for
    2+ quarters, re-evaluate.<br/>
    • <b>Bitcoin Crashes >50%:</b> If BTC drops from $100K to <$50K, IREN will likely get obliterated.
    Consider exiting or reducing position.<br/>
    • <b>Profitability Reversal:</b> If IREN returns to losses due to margin compression, re-evaluate thesis.<br/>
    • <b>Analyst Downgrades Cluster:</b> If 3+ analysts downgrade to Hold/Sell, something's broken - investigate.<br/>
    <br/>
    <b>REBALANCING EXIT:</b><br/>
    • <b>Position grows to >3% of portfolio:</b> Trim back to 2% allocation. This is a speculative position -
    don't let it become a core holding just because it's working.
    """
    elements.append(Paragraph(exit_scenarios, body_style))

    elements.append(PageBreak())

    # ============================================================
    # KEY METRICS SUMMARY
    # ============================================================

    elements.append(Paragraph("<b>Key Metrics Summary (For Reference):</b>", heading2_style))

    metrics_data = [
        ['Category', 'Metric', 'Value', 'Assessment'],
        ['Valuation', 'Market Cap', '$7.4B (est.)', 'Mid-cap'],
        ['Valuation', 'Price/Sales', 'TBD', 'Growth story, not value'],
        ['Growth', 'FY25 Revenue', '$501M (+168% YoY)', 'Exceptional'],
        ['Growth', 'Q1 FY26 Revenue', '$240M (+355% YoY)', 'Exceptional'],
        ['Growth', 'AI ARR Target', '$500M+ by Q1 2026', 'Ambitious'],
        ['Profitability', 'FY25 Net Income', '$86.9M (first profitable year)', 'Milestone'],
        ['Profitability', 'Q1 FY26 EBITDA', '$91.5M (36x YoY)', 'Strong'],
        ['Risk', 'Annual Volatility', '97.75%', 'EXTREME'],
        ['Risk', 'Max Drawdown (1Y)', '-65.56%', 'CATASTROPHIC'],
        ['Risk', 'Beta vs SPY', '2.16', 'Very High'],
        ['Risk', 'Recent Correction', '-49% from ATH', 'Brutal'],
        ['Performance', 'YTD 2025', '+269%', 'Outstanding'],
        ['Performance', 'Alpha vs SPY', '+110.46%', 'Exceptional'],
        ['Performance', 'Sharpe Ratio', '1.32', 'Good'],
        ['Technicals', 'RSI', '32.81', 'Neutral'],
        ['Technicals', 'Stochastic', '2.42', 'OVERSOLD'],
        ['Technicals', 'Williams %R', '-97.58', 'OVERSOLD'],
        ['Analyst', 'Consensus Rating', 'BUY (9-10 analysts)', 'Bullish'],
        ['Analyst', 'Average Price Target', '$72.56 (+103%)', 'Bullish'],
        ['Analyst', 'High Target', '$136 (+280%)', 'Very Bullish']
    ]

    metrics_table = Table(metrics_data, colWidths=[1.2*inch, 1.8*inch, 1.5*inch, 1.1*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(metrics_table)

    elements.append(PageBreak())

    # ============================================================
    # FINAL VERDICT & SOURCES
    # ============================================================

    elements.append(Paragraph("<b>FINAL VERDICT - TL;DR</b>", heading1_style))

    final_verdict = """
    <font size=12><b>SPECULATIVE BUY - 1-2% MAXIMUM ALLOCATION</b></font><br/><br/>

    <b>THE BULL CASE (40% probability):</b><br/>
    IREN successfully executes the AI pivot, hits $500M+ AI ARR by Q1 2026, Sweetwater comes online in
    April 2026, Microsoft contract delivers, Bitcoin stays elevated, and the stock climbs to $60-136
    (analyst targets). Your $3,750 becomes $6,300-14,280 (+68% to +280%).<br/><br/>

    <b>THE BEAR CASE (30% probability):</b><br/>
    Execution stumbles (GPU deployment delays, Microsoft contract issues), Bitcoin crashes, competition
    intensifies, margins compress, or macro headwinds hit. Stock drops to $20-30. Your $3,750 becomes
    $2,100-3,150 (-16% to -44%). You either stop out at $27.63 (-23%) or baghold hoping for recovery.<br/><br/>

    <b>THE BASE CASE (30% probability):</b><br/>
    IREN muddles through - makes progress but not spectacular. Stock trades sideways to modestly higher
    at $45-55. Your $3,750 becomes $4,725-5,775 (+26% to +54%). Decent return for high risk taken.<br/><br/>

    <b>BOTTOM LINE:</b><br/>
    This is a classic asymmetric bet - risk 1-2% of portfolio to potentially gain 2-6x returns if the AI
    pivot succeeds. The oversold technicals (stochastic at 2.42, down -49% from highs) create an attractive
    entry point. The fundamentals are REAL (profitable, growing, NVIDIA partnership, Microsoft deal). But
    the risks are EXTREME (volatility, Bitcoin dependency, execution uncertainty).
    <br/><br/>
    <b>ONLY BUY IF:</b> (1) You can stomach -50% drawdowns, (2) You'll respect the stop loss at $27.63,
    (3) You won't panic-sell if it drops another 20%, (4) You understand this is speculative "Vegas money"
    not core portfolio allocation.
    <br/><br/>
    <font color='#16a085'><b>Recommended Action:</b></font> Buy $3,750 (1.5% allocation) in 3 tranches
    over 2-3 weeks. Set stop loss at $27.63. Take 50% profit at $72. Hold 25% for moon shot to $136+.
    Monitor quarterly earnings religiously. Don't fall in love with the position - this is a trade, not
    a marriage.
    """
    elements.append(Paragraph(final_verdict, body_style))

    elements.append(Spacer(1, 0.3*inch))

    # ============================================================
    # SOURCES & DISCLAIMER
    # ============================================================

    elements.append(Paragraph("<b>Sources & Research:</b>", heading2_style))

    sources = """
    • <b>Market Data:</b> Yahoo Finance (yfinance API), December 17-18, 2025<br/>
    • <b>IREN Company Analysis:</b> Disruption Banking, "Why IREN is Shifting Away from Bitcoin Mining to Data Centers"<br/>
    • <b>Dual-Engine Growth Analysis:</b> FinancialContent, "Iris Energy Limited (IREN): A Deep Dive into Bitcoin Mining and AI Cloud Services"<br/>
    • <b>Stock Performance:</b> TS2 Space, "Bitcoin Miner to AI Cloud Sensation: Why Iris Energy (IREN) Stock Is Soaring in 2025"<br/>
    • <b>Revenue Milestones:</b> The Block, "IREN on track to $1 billion in annualized bitcoin mining revenue"<br/>
    • <b>AI Pivot Strategy:</b> Seeking Alpha, "IREN Stock: Bright Future Ahead - Low-Cost Bitcoin Mining And AI Tailwinds"<br/>
    • <b>2026 Catalysts:</b> TS2 Space, "IREN Limited Stock (NASDAQ: IREN) News Today: Microsoft AI Deal Shapes 2026"<br/>
    • <b>Analyst Ratings:</b> MarketBeat, TipRanks, Benzinga - Analyst Ratings and Price Targets (December 2025)<br/>
    • <b>Price Targets:</b> Cantor Fitzgerald ($136), Roth Capital ($82), Bernstein ($75)<br/>
    • <b>Financial Performance:</b> QuiverQuant, "Iris Energy Limited Stock (IREN) Opinions on Fiscal Year 2025 Results and AI Expansion"<br/>
    • <b>Quantitative Analysis:</b> Finance Guru proprietary risk metrics, momentum, volatility tools (252-day and 90-day analysis)<br/>
    • <b>Technical Analysis:</b> yfinance market data, Finance Guru CLI tools (risk_metrics_cli.py, momentum_cli.py, volatility_cli.py)
    """
    elements.append(Paragraph(sources, body_style))

    elements.append(Spacer(1, 0.4*inch))

    # Disclaimer
    disclaimer = """DISCLAIMER: This analysis is for educational purposes only and does not constitute
    investment advice. The information presented is based on publicly available data and proprietary
    quantitative analysis as of December 18, 2025. Past performance does not guarantee future results.
    IREN Limited (formerly Iris Energy) is an EXTREMELY VOLATILE, SPECULATIVE stock with significant risks
    including Bitcoin price volatility, execution uncertainty, catastrophic drawdowns, and competitive threats.
    This position should NEVER exceed 1-2% of your portfolio. You could lose your entire investment.
    This report is prepared for Ossie's private family office and should not be distributed or relied upon
    by third parties. Always consult with licensed financial advisors before making investment decisions.
    The author may or may not hold positions in IREN. Cryptocurrency and AI-related investments are subject
    to extreme volatility and regulatory uncertainty."""
    elements.append(Paragraph(disclaimer, disclaimer_style))

    elements.append(Spacer(1, 0.1*inch))

    footer = """<b>Finance Guru™ - Private Family Office Analysis</b><br/>
    Report Generated: December 18, 2025<br/>
    Analyst Team: Dr. Aleksandr Petrov (Market Research), Dr. Priya Desai (Quantitative Analysis),
    Elena Rodriguez-Park (Strategy)<br/>
    Powered by BMAD-CORE™ v6.0.0<br/>
    Report Version: 1.0 | Classification: Speculative High-Risk Analysis"""
    elements.append(Paragraph(footer, disclaimer_style))

    # Build PDF
    doc.build(elements)

    print(f"\n✅ PDF Report Generated Successfully!")
    print(f"📁 Location: {output_path}")
    print(f"📄 File size: {os.path.getsize(output_path) / 1024:.1f} KB")
    print(f"\n📊 VERDICT: SPECULATIVE BUY - 1-2% MAX POSITION")
    print(f"💰 Recommended Allocation: $2,500-$5,000 (1-2% of $250K portfolio)")
    print(f"📈 Entry: Scale in at $35-36, $30-32, $40-42 over 2-3 weeks")
    print(f"🛑 Stop Loss: $27.63 (2x ATR - NON-NEGOTIABLE)")
    print(f"🎯 Target: $72 (analyst avg), $136 (bull case)")

if __name__ == "__main__":
    create_iren_report()
