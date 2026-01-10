#!/usr/bin/env python3
"""
Generate comprehensive PLTR analysis PDF report
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

def create_pltr_report():
    """Generate comprehensive PLTR analysis PDF"""

    # Output path
    output_path = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports/PLTR-analysis-2025-12-18.pdf"

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

    elements.append(Paragraph("PLTR (Palantir Technologies)", title_style))
    elements.append(Paragraph("Comprehensive Position Analysis", heading1_style))
    elements.append(Spacer(1, 0.3*inch))

    # Executive Summary Box
    summary_data = [
        ['Current Holdings:', '369.746 shares'],
        ['Position Value:', '$68,576'],
        ['Total Gain:', '+613.64% (+$59,001)'],
        ['Portfolio Weight:', '~27% (LARGEST POSITION)'],
        ['Current Price:', '$185.69 (Dec 18, 2025)'],
        ['52-Week Range:', '$26.00 - $207.00']
    ]

    summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
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

    # Critical Alert
    alert_text = """<b>CRITICAL POSITION MANAGEMENT ALERT:</b> This represents your largest holding at 27%
    portfolio concentration with a 614% gain. This report addresses position sizing, tax implications,
    and risk management for this massive winner."""
    elements.append(Paragraph(alert_text, body_style))

    elements.append(PageBreak())

    # ============================================================
    # PHASE 1: MARKET RESEARCH
    # ============================================================

    elements.append(Paragraph("PHASE 1: Market Research & Outlook", heading1_style))
    elements.append(Paragraph("Dr. Aleksandr Petrov - Market Intelligence", heading2_style))

    elements.append(Paragraph("<b>Company Overview:</b>", body_style))
    overview = """Palantir Technologies (PLTR) is the leading operational AI platform provider, serving
    government and commercial clients with its Gotham (government) and Foundry (commercial) platforms.
    The company's AIP (Artificial Intelligence Platform) launched in mid-2023 has catalyzed explosive
    commercial growth."""
    elements.append(Paragraph(overview, body_style))
    elements.append(Spacer(1, 0.1*inch))

    elements.append(Paragraph("<b>2025 Performance Highlights:</b>", body_style))
    perf_bullets = """
    • <b>Stock Performance:</b> +160% YTD in 2025, +2,700% since 2023
    • <b>All-Time High:</b> $207 on November 3, 2025
    • <b>Current Price:</b> $185.69 (down ~10% from peak)
    • <b>Market Cap:</b> One of the best-performing stocks in S&P 500
    """
    elements.append(Paragraph(perf_bullets, body_style))
    elements.append(Spacer(1, 0.1*inch))

    elements.append(Paragraph("<b>Revenue Growth Trajectory:</b>", body_style))

    revenue_data = [
        ['Period', 'Revenue', 'Growth Rate', 'Key Driver'],
        ['2025 (Est.)', '$4.4B', '+45% YoY', 'AIP commercial acceleration'],
        ['2026 (Proj.)', '$5.5-6.0B', '+30-40% YoY', 'AIP global scaling'],
        ['2027 (Proj.)', '$7.55B', '+34% YoY', 'Enterprise adoption']
    ]

    revenue_table = Table(revenue_data, colWidths=[1.3*inch, 1.3*inch, 1.3*inch, 2.3*inch])
    revenue_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))

    elements.append(revenue_table)
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph("<b>AIP Platform Success:</b>", body_style))
    aip_text = """The Artificial Intelligence Platform (AIP) has been the game-changer. It's not just
    an LLM wrapper - it's a cloud-agnostic, model-agnostic platform that embeds AI into existing workflows
    and operations. Key metrics:"""
    elements.append(Paragraph(aip_text, body_style))

    aip_bullets = """
    • <b>US Commercial Revenue:</b> +121% YoY in Q3 2025 ($397M)
    • <b>Total Commercial Revenue:</b> +73% YoY in Q3 ($548M)
    • <b>Contract Value (TCV):</b> +342% YoY to $1.31B in Q3
    • <b>Sequential Growth:</b> 20% quarter-over-quarter consistency
    """
    elements.append(Paragraph(aip_bullets, body_style))
    elements.append(Spacer(1, 0.1*inch))

    elements.append(Paragraph("<b>Government Revenue Strength:</b>", body_style))
    gov_bullets = """
    • <b>Q3 2025 Government Revenue:</b> +55% YoY to $633M
    • <b>US Army Contract:</b> $10B over 10 years for data software
    • <b>US Navy Partnership:</b> ShipOS initiative, up to $448M authorized
    • <b>Trump Administration:</b> Expanded data compilation role across agencies
    • <b>DoD Integration:</b> Widely deployed across Department of Defense
    """
    elements.append(Paragraph(gov_bullets, body_style))
    elements.append(Spacer(1, 0.1*inch))

    elements.append(Paragraph("<b>2026 Catalysts:</b>", body_style))
    catalysts = """
    • Continued AIP adoption in Fortune 500 companies
    • International commercial expansion (currently US-heavy)
    • New government contracts under Trump administration
    • Potential inclusion in more indices (already in S&P 500, NASDAQ-100)
    • Enterprise AI becoming mission-critical (not experimental)
    """
    elements.append(Paragraph(catalysts, body_style))

    elements.append(PageBreak())

    # ============================================================
    # VALUATION CONCERNS
    # ============================================================

    elements.append(Paragraph("<b>The Valuation Elephant in the Room:</b>", heading2_style))

    val_intro = """<font color='red'><b>WARNING:</b></font> PLTR is trading at the most extreme
    valuation multiples ever recorded for a company of its market cap. This is the primary risk factor."""
    elements.append(Paragraph(val_intro, body_style))
    elements.append(Spacer(1, 0.1*inch))

    val_data = [
        ['Metric', 'Current Multiple', 'Historical Context'],
        ['Price-to-Sales', '118x', 'Highest P/S ever for this market cap'],
        ['Forward P/E', '251x', 'Extreme vs. software peers (20-40x)'],
        ['Price Gain vs Revenue', 'Massive', 'Stock rose faster than business']
    ]

    val_table = Table(val_data, colWidths=[2*inch, 1.8*inch, 2.4*inch])
    val_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fadbd8')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))

    elements.append(val_table)
    elements.append(Spacer(1, 0.15*inch))

    val_concern = """<b>Analyst Perspective:</b> Multiple analysts warn of potential "serious correction"
    in 2026 due to overvaluation. Even bullish analysts acknowledge the stock has run far ahead of
    fundamentals. However, Bank of America maintains a Street-high $255 target, implying further 37%
    upside IF execution continues."""
    elements.append(Paragraph(val_concern, body_style))

    elements.append(Spacer(1, 0.1*inch))

    price_targets = """
    <b>2026 Price Target Range:</b>
    • <b>Bear Case:</b> $150-170 (correction to more reasonable multiples)
    • <b>Base Case:</b> $187 (analyst consensus, slight upside)
    • <b>Bull Case:</b> $250-300 (BofA target, sustained execution)
    """
    elements.append(Paragraph(price_targets, body_style))

    elements.append(PageBreak())

    # ============================================================
    # PHASE 2: QUANTITATIVE ANALYSIS
    # ============================================================

    elements.append(Paragraph("PHASE 2: Quantitative Analysis", heading1_style))
    elements.append(Paragraph("Dr. Priya Desai - Risk & Performance Metrics", heading2_style))

    elements.append(Paragraph("<b>Risk Metrics (252-Day Analysis vs SPY):</b>", heading2_style))

    risk_data = [
        ['Metric', 'Value', 'Interpretation', 'Rating'],
        ['Annual Return', '+110.5%', 'Exceptional performance', '⭐⭐⭐⭐⭐'],
        ['Sharpe Ratio', '1.58', 'Good risk-adjusted returns', '⭐⭐⭐⭐'],
        ['Sortino Ratio', '2.35', 'Strong downside protection', '⭐⭐⭐⭐⭐'],
        ['Max Drawdown', '-40.61%', 'Severe worst-case decline', '⚠️'],
        ['Calmar Ratio', '2.72', 'Strong return vs drawdown', '⭐⭐⭐⭐'],
        ['Annual Volatility', '67.33%', 'Very high volatility', '⚠️⚠️'],
        ['95% VaR (Daily)', '-6.58%', '5% chance of >6.58% loss/day', '⚠️'],
        ['95% CVaR (Daily)', '-9.34%', 'Average tail loss', '⚠️⚠️'],
        ['Beta vs SPY', '2.06', '2x market volatility', '⚠️⚠️'],
        ['Alpha vs SPY', '+88.62%', 'Massive outperformance', '⭐⭐⭐⭐⭐']
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

    risk_summary = """<b>Key Takeaway:</b> PLTR delivers exceptional returns (+88.62% alpha) with good
    risk-adjusted performance (Sharpe 1.58, Sortino 2.35). However, it comes with very high volatility
    (67.33% annual) and 2x market beta. The -40.61% max drawdown shows this can correct brutally."""
    elements.append(Paragraph(risk_summary, body_style))

    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>Momentum Analysis (90-Day):</b>", heading2_style))

    momentum_data = [
        ['Indicator', 'Value', 'Signal', 'Interpretation'],
        ['RSI', '48.75', 'Neutral', 'No extreme overbought/oversold'],
        ['MACD', '2.02 / 0.83', 'Bullish', 'MACD above signal (upward momentum)'],
        ['Stochastic', '51.96 / 73.73', 'Neutral', '%K in mid-range'],
        ['Williams %R', '-48.04', 'Neutral', 'Mid-range positioning'],
        ['ROC', '+5.85%', 'Bullish', 'Positive momentum'],
        ['Confluence', '2/5 Bullish', 'Mixed', 'No clear directional bias']
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

    momentum_summary = """<b>Momentum Assessment:</b> PLTR is in a consolidation phase after the massive
    run-up. RSI at 48.75 (neutral) suggests the stock has cooled off from overbought levels. MACD remains
    bullish, but mixed signals overall indicate no strong trend currently. This is actually healthy after
    a +160% YTD gain - the stock needs to digest gains."""
    elements.append(Paragraph(momentum_summary, body_style))

    elements.append(PageBreak())

    elements.append(Paragraph("<b>Volatility Analysis (90-Day):</b>", heading2_style))

    vol_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['Current Price', '$185.69', 'Down ~10% from $207 ATH'],
        ['Volatility Regime', 'Normal', 'Standard position sizing appropriate'],
        ['ATR (14-day)', '$8.18 (4.40%)', 'Average daily range'],
        ['2x ATR Stop', '$16.35', 'Suggested stop-loss distance'],
        ['Annual Volatility', '44.85%', 'High but manageable'],
        ['Bollinger Bands', '$153.69 - $196.39', 'Price at 75% of band (upper)'],
        ['Bandwidth', '24.39%', 'Moderate volatility currently']
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

    vol_summary = """<b>Volatility Context:</b> PLTR is in "normal" volatility regime currently (not extreme).
    The 4.40% ATR means typical daily swings of $8.18. Price is at 75% of Bollinger Band range, suggesting
    it's leaning toward the upper bound but not stretched. The $169 level (current price minus 2x ATR)
    would be a technical support zone."""
    elements.append(Paragraph(vol_summary, body_style))

    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>Portfolio Correlation Analysis (252-Day):</b>", heading2_style))

    corr_intro = """Your portfolio shows <b>HIGH correlation across all holdings</b>, which significantly
    reduces diversification benefits:"""
    elements.append(Paragraph(corr_intro, body_style))
    elements.append(Spacer(1, 0.1*inch))

    corr_data = [
        ['Asset Pair', 'Correlation', 'Level', 'Implication'],
        ['PLTR - VOO', '+0.607', 'HIGH', 'Moves with market'],
        ['PLTR - NVDA', '+0.576', 'HIGH', 'Tech sector correlation'],
        ['PLTR - TSLA', '+0.529', 'HIGH', 'Growth stock correlation'],
        ['NVDA - VOO', '+0.730', 'VERY HIGH', 'NVDA drives market'],
        ['TSLA - VOO', '+0.693', 'HIGH', 'TSLA market sensitivity']
    ]

    corr_table = Table(corr_data, colWidths=[1.6*inch, 1.3*inch, 1.2*inch, 2.1*inch])
    corr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fadbd8')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))

    elements.append(corr_table)
    elements.append(Spacer(1, 0.15*inch))

    corr_summary = """<b>Diversification Score: 0.390 (MODERATE - Limited Diversification)</b><br/><br/>
    <font color='red'><b>RISK ALERT:</b></font> Your portfolio has limited diversification with average
    correlation of 0.610. All holdings (PLTR, TSLA, NVDA, VOO) are highly correlated, meaning they tend
    to move together. In a market correction, you could see all positions decline simultaneously. The
    high PLTR concentration (27%) amplifies this risk."""
    elements.append(Paragraph(corr_summary, body_style))

    elements.append(PageBreak())

    # ============================================================
    # PHASE 3: STRATEGY RECOMMENDATION
    # ============================================================

    elements.append(Paragraph("PHASE 3: Strategic Recommendation", heading1_style))
    elements.append(Paragraph("Elena Rodriguez-Park - Portfolio Strategy", heading2_style))

    elements.append(Paragraph("<b>The Big Picture: Managing a 614% Winner</b>", heading2_style))

    big_picture = """This is a unique position management challenge. You've turned $9,575 into $68,576 -
    an exceptional outcome. The question isn't "Is PLTR a good company?" (it clearly is). The question
    is: "At 27% portfolio concentration with extreme valuation multiples, what's the right risk management
    strategy?" Here's the strategic framework:"""
    elements.append(Paragraph(big_picture, body_style))

    elements.append(Spacer(1, 0.15*inch))

    # Strategic Options Table
    options_data = [
        ['Strategy', 'Action', 'Rationale', 'Risk/Reward'],
        ['HOLD ALL', 'Keep 369.746 shares', 'Ride momentum, AIP story intact', 'High risk/reward'],
        ['TRIM 50%', 'Sell ~185 shares ($34K)', 'Lock in gains, reduce concentration', 'Moderate/Moderate'],
        ['TRIM TO 15%', 'Sell ~150 shares ($28K)', 'Rebalance to safer allocation', 'Lower risk/reward'],
        ['TACTICAL TRIM', 'Sell on strength to $200+', 'Wait for bounce, then trim', 'Moderate/High']
    ]

    options_table = Table(options_data, colWidths=[1.4*inch, 1.6*inch, 2*inch, 1.2*inch])
    options_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#d5f4e6')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(options_table)
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>Tax Implications (Critical Consideration):</b>", heading2_style))

    tax_calc = """
    <b>If you sell shares today:</b><br/>
    • <b>Cost Basis:</b> ~$25.89/share (estimated from $9,575 / 370 shares)<br/>
    • <b>Current Price:</b> $185.69/share<br/>
    • <b>Capital Gain:</b> $159.80/share<br/>
    • <b>Holding Period:</b> Long-term (assuming >1 year hold)<br/>
    • <b>Tax Rate:</b> 15-20% federal long-term capital gains + state tax<br/>
    <br/>
    <b>Example: Selling 185 shares (50% trim):</b><br/>
    • <b>Proceeds:</b> $34,352<br/>
    • <b>Capital Gain:</b> $29,563<br/>
    • <b>Estimated Federal Tax (20%):</b> $5,913<br/>
    • <b>Net After Tax:</b> ~$28,439<br/>
    <br/>
    <font color='red'><b>TAX EFFICIENCY ALERT:</b></font> You'll owe ~$6K in federal taxes per $30K in
    gains realized. This is the price of locking in profits. However, avoiding a 50% correction would
    save you $34K, far exceeding the tax bill.
    """
    elements.append(Paragraph(tax_calc, body_style))

    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("<b>Scenario Analysis: What Could Happen in 2026?</b>", heading2_style))

    scenario_data = [
        ['Scenario', 'Probability', 'Price Target', 'Your Position Value', 'Outcome'],
        ['Bull Case', '25%', '$250-300', '$92K-111K', '+34% to +62%'],
        ['Base Case', '40%', '$180-200', '$66K-74K', '-4% to +8%'],
        ['Bear Case', '25%', '$130-150', '$48K-55K', '-30% to -20%'],
        ['Crash Case', '10%', '$80-100', '$30K-37K', '-56% to -46%']
    ]

    scenario_table = Table(scenario_data, colWidths=[1.2*inch, 1.1*inch, 1.2*inch, 1.5*inch, 1.2*inch])
    scenario_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#d4edda')),  # Bull
        ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#fff3cd')),  # Base
        ('BACKGROUND', (0, 3), (0, 3), colors.HexColor('#f8d7da')),  # Bear
        ('BACKGROUND', (0, 4), (0, 4), colors.HexColor('#f5c6cb')),  # Crash
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(scenario_table)
    elements.append(Spacer(1, 0.15*inch))

    scenario_note = """<b>Expected Value Calculation:</b> (0.25 × $101K) + (0.40 × $70K) + (0.25 × $51K)
    + (0.10 × $33K) = <b>~$66.5K</b> (slightly below current $68.6K value). The math suggests the risk/reward
    is roughly balanced at current levels."""
    elements.append(Paragraph(scenario_note, body_style))

    elements.append(PageBreak())

    # ============================================================
    # FINAL RECOMMENDATION
    # ============================================================

    elements.append(Paragraph("<b>FINAL STRATEGIC RECOMMENDATION</b>", heading1_style))

    recommendation = """
    <font color='#c0392b'><b>TRIM 40-50% OF POSITION (Sell 145-185 shares)</b></font><br/><br/>

    <b>Recommended Action:</b><br/>
    • <b>SELL:</b> 150-185 shares (~40-50% of holdings)<br/>
    • <b>TARGET SALE PRICE:</b> $190-200 (wait for a bounce from current $185.69)<br/>
    • <b>PROCEEDS:</b> $28K-37K (before taxes)<br/>
    • <b>REMAINING POSITION:</b> 185-220 shares (~15-17% of portfolio)<br/>
    • <b>TAX BILL:</b> ~$5K-7K federal (budget for this)<br/>
    <br/>
    <b>Why Trim (Not Hold or Sell All)?</b><br/>
    1. <b>Lock in Life-Changing Gains:</b> You've 7x'd your money. Taking $28K+ off the table is prudent
    risk management, especially with the tax bill manageable.<br/>
    2. <b>Reduce Concentration Risk:</b> 27% in one stock is aggressive, especially one trading at 118x
    sales. Even aggressive investors should cap single positions at 15-20%.<br/>
    3. <b>Valuation Risk is Real:</b> Multiple analysts warn of correction risk. Even if PLTR is a great
    company, the stock is priced for perfection. Any disappointment could trigger a 30-50% correction.<br/>
    4. <b>Keep Upside Exposure:</b> You'll still own 185-220 shares (~$34K-41K). If PLTR hits $250-300,
    you'll participate in that upside (~$46K-66K value).<br/>
    5. <b>Sleep Better:</b> Watching a $68K position swing $8K/day (based on ATR) is stressful. Trimming
    reduces emotional volatility.<br/>
    <br/>
    <b>What to Do With Proceeds?</b><br/>
    • <b>Rebalance into VOO:</b> Add to your S&P 500 position for diversification<br/>
    • <b>Build Cash Reserve:</b> Keep dry powder for opportunities (market could correct in 2026)<br/>
    • <b>Tax-Loss Harvesting:</b> If you have any losers, harvest them to offset PLTR gains<br/>
    <br/>
    <b>When to Sell Remaining Position:</b><br/>
    • <b>IF</b> PLTR hits $250-300: Trim another 30-50% (lock in more gains)<br/>
    • <b>IF</b> PLTR falls below $150: Re-evaluate (might add back if fundamentals intact)<br/>
    • <b>IF</b> Valuation compresses to 50-70x P/S: Consider it fairly valued for long-term hold<br/>
    <br/>
    <font color='#16a085'><b>Bottom Line:</b></font> You've won. Lock in some chips from the table. Keep
    enough exposure to participate in upside, but don't let a 27% concentration blow up your portfolio
    if PLTR corrects. This is about risk management, not pessimism on the company.
    """
    elements.append(Paragraph(recommendation, body_style))

    elements.append(Spacer(1, 0.3*inch))

    # ============================================================
    # KEY METRICS SUMMARY
    # ============================================================

    elements.append(Paragraph("<b>Key Metrics Summary (For Reference):</b>", heading2_style))

    metrics_data = [
        ['Category', 'Metric', 'Value', 'Assessment'],
        ['Valuation', 'P/S Ratio', '118x', 'Extreme'],
        ['Valuation', 'Forward P/E', '251x', 'Extreme'],
        ['Growth', '2025 Revenue Growth', '+45% YoY', 'Excellent'],
        ['Growth', '2026 Revenue (Est.)', '$5.5-6B', 'Strong'],
        ['Risk', 'Annual Volatility', '67.33%', 'Very High'],
        ['Risk', 'Max Drawdown (1Y)', '-40.61%', 'Severe'],
        ['Risk', 'Beta', '2.06', 'High'],
        ['Performance', 'Alpha vs SPY', '+88.62%', 'Outstanding'],
        ['Performance', 'Sharpe Ratio', '1.58', 'Good'],
        ['Portfolio', 'Concentration', '27%', 'Too High'],
        ['Portfolio', 'Correlation to VOO', '+0.607', 'High']
    ]

    metrics_table = Table(metrics_data, colWidths=[1.2*inch, 1.8*inch, 1.2*inch, 1.2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))

    elements.append(metrics_table)

    elements.append(PageBreak())

    # ============================================================
    # EXECUTION CHECKLIST
    # ============================================================

    elements.append(Paragraph("<b>Execution Checklist:</b>", heading2_style))

    checklist = """
    <b>Before You Sell:</b><br/>
    ☐ Confirm holding period is >1 year (for long-term capital gains tax rate)<br/>
    ☐ Check current year tax situation (could you defer to 2026 if beneficial?)<br/>
    ☐ Set limit order at $190-200 (don't chase the stock down)<br/>
    ☐ Decide where proceeds will go (VOO? Cash? Other opportunity?)<br/>
    ☐ Budget for tax payment (~$5K-7K federal for 150-185 shares sold)<br/>
    <br/>
    <b>After You Sell:</b><br/>
    ☐ Document cost basis and sale date for tax records<br/>
    ☐ Set aside tax payment in high-yield savings (don't spend it!)<br/>
    ☐ Rebalance proceeds into lower-correlation assets<br/>
    ☐ Set calendar reminder to review PLTR quarterly (Q1 2026 earnings, etc.)<br/>
    ☐ Update your portfolio tracking spreadsheet<br/>
    <br/>
    <b>Monitoring Plan for Remaining Position:</b><br/>
    ☐ Set alert at $250 (consider trimming more)<br/>
    ☐ Set alert at $150 (re-evaluate position)<br/>
    ☐ Watch Q1 2026 earnings (late Jan/early Feb) for AIP momentum trends<br/>
    ☐ Monitor analyst downgrades (could signal sentiment shift)<br/>
    ☐ Track US commercial revenue growth (needs to stay >80% YoY)
    """
    elements.append(Paragraph(checklist, body_style))

    elements.append(Spacer(1, 0.3*inch))

    # ============================================================
    # SOURCES & DISCLAIMER
    # ============================================================

    elements.append(Paragraph("<b>Sources & Research:</b>", heading2_style))

    sources = """
    • <b>Market Data:</b> Yahoo Finance (yfinance API)<br/>
    • <b>Palantir Stock Forecast 2025:</b> io-fund.com/ai-stocks/palantir-stock-forecast-2025-valuation<br/>
    • <b>Palantir Deep-Dive (Dec 2025):</b> markets.financialcontent.com/wral/article/predictstreet-2025-12-18<br/>
    • <b>Motley Fool Stock Predictions:</b> fool.com/investing/how-to-invest/stocks/palantir-stock-forecast<br/>
    • <b>Yahoo Finance Price Prediction:</b> finance.yahoo.com/news/palantir-price-prediction-heading-2026-173022116.html<br/>
    • <b>24/7 Wall St. Analysis:</b> 247wallst.com/investing/2025/12/01/palantirs-price-prediction-heading-into-2026<br/>
    • <b>TS2 Space PLTR News:</b> ts2.tech/en/palantir-pltr-stock-news-today-dgsi-renewal-navy-shipos-deal<br/>
    • <b>Quantitative Analysis:</b> Finance Guru proprietary risk metrics, momentum, volatility, correlation tools
    """
    elements.append(Paragraph(sources, body_style))

    elements.append(Spacer(1, 0.4*inch))

    # Disclaimer
    disclaimer = """DISCLAIMER: This analysis is for educational purposes only and does not constitute
    investment advice. The information presented is based on publicly available data and proprietary
    quantitative analysis as of December 18, 2025. Past performance does not guarantee future results.
    Stock investing involves risk, including the potential loss of principal. Palantir Technologies (PLTR)
    is a volatile, high-growth stock with significant valuation risk. Tax implications vary by individual
    circumstance - consult a qualified tax professional before making any investment decisions. This report
    is prepared for Ossie's private family office and should not be distributed or relied upon by third parties.
    Always consult with licensed financial advisors and tax professionals before making investment decisions."""
    elements.append(Paragraph(disclaimer, disclaimer_style))

    elements.append(Spacer(1, 0.1*inch))

    footer = """<b>Finance Guru™ - Private Family Office Analysis</b><br/>
    Report Generated: December 18, 2025<br/>
    Analyst Team: Dr. Aleksandr Petrov (Market Research), Dr. Priya Desai (Quantitative Analysis),
    Elena Rodriguez-Park (Strategy)<br/>
    Powered by BMAD-CORE™ v6.0.0"""
    elements.append(Paragraph(footer, disclaimer_style))

    # Build PDF
    doc.build(elements)

    print(f"\n✅ PDF Report Generated Successfully!")
    print(f"📁 Location: {output_path}")
    print(f"📄 File size: {os.path.getsize(output_path) / 1024:.1f} KB")

if __name__ == "__main__":
    create_pltr_report()
