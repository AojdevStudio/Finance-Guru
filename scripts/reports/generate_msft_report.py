#!/usr/bin/env python3
"""Generate comprehensive MSFT analysis PDF report."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from datetime import datetime

# Report configuration
OUTPUT_PATH = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports/MSFT-analysis-2025-12-18.pdf"
TICKER = "MSFT"
COMPANY_NAME = "Microsoft Corporation"
CURRENT_PRICE = 483.98
ANALYSIS_DATE = "2025-12-18"

# Create PDF document
doc = SimpleDocTemplate(
    OUTPUT_PATH,
    pagesize=letter,
    rightMargin=0.75*inch,
    leftMargin=0.75*inch,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch
)

# Container for the 'Flowable' objects
elements = []

# Define custom styles
styles = getSampleStyleSheet()

# Title style
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=12,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)

# Header style
header_style = ParagraphStyle(
    'CustomHeader',
    parent=styles['Heading2'],
    fontSize=16,
    textColor=colors.HexColor('#2c5aa0'),
    spaceAfter=10,
    spaceBefore=12,
    fontName='Helvetica-Bold'
)

# Subheader style
subheader_style = ParagraphStyle(
    'CustomSubHeader',
    parent=styles['Heading3'],
    fontSize=12,
    textColor=colors.HexColor('#444444'),
    spaceAfter=8,
    fontName='Helvetica-Bold'
)

# Body text style
body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['BodyText'],
    fontSize=10,
    textColor=colors.HexColor('#333333'),
    alignment=TA_JUSTIFY,
    spaceAfter=6
)

# Small text style
small_style = ParagraphStyle(
    'SmallText',
    parent=styles['BodyText'],
    fontSize=8,
    textColor=colors.HexColor('#666666'),
    alignment=TA_LEFT
)

# ==================== PAGE 1: TITLE & HEADER ====================

# Title
title = Paragraph(f"<b>FINANCE GURU™ INVESTMENT ANALYSIS</b>", title_style)
elements.append(title)
elements.append(Spacer(1, 0.1*inch))

# Company name and ticker
company_title = Paragraph(
    f"<b>{COMPANY_NAME} ({TICKER})</b>",
    ParagraphStyle('CompanyTitle', parent=title_style, fontSize=18)
)
elements.append(company_title)
elements.append(Spacer(1, 0.3*inch))

# Header information table
header_data = [
    ['Analysis Date:', ANALYSIS_DATE, 'Current Price:', f'${CURRENT_PRICE:.2f}'],
    ['Analyst Team:', 'Market Research & Quant', 'YTD Performance:', '+16.48%'],
    ['Report Type:', 'Full Research Workflow', '52-Week Range:', '$344.79 - $555.45'],
]

header_table = Table(header_data, colWidths=[1.5*inch, 2.0*inch, 1.5*inch, 2.0*inch])
header_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c5aa0')),
    ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#2c5aa0')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
elements.append(header_table)
elements.append(Spacer(1, 0.3*inch))

# ==================== EXECUTIVE SUMMARY ====================

elements.append(Paragraph("<b>EXECUTIVE SUMMARY</b>", header_style))

exec_summary = """
Microsoft continues to demonstrate exceptional execution across its Cloud, AI, and productivity
franchises. With Azure growing 40% YoY, AI business surpassing $13B annual run rate (+175% YoY),
and 900M monthly active AI users, the company is capitalizing on secular tailwinds in enterprise
digital transformation and artificial intelligence adoption.

<b>Investment Thesis:</b> MSFT represents a high-quality growth-at-scale opportunity. The company's
strategic OpenAI partnership, massive AI infrastructure investments ($94B+ in 2025), and pricing
power (M365 price increases in July 2026) position it for sustained 15-20% revenue growth through
2026. While trading at 25.8x forward P/E (elevated but justified), the risk/reward remains
favorable for long-term investors given the $392B backlog and strong competitive moat in enterprise
software and cloud infrastructure.

<b>Key Catalysts:</b> AI Copilot monetization acceleration, Azure market share gains (now 20% vs
AWS 30%), global expansion ($17.5B India, $5.4B Canada investments), and July 2026 M365 price
increases.

<b>Primary Risks:</b> Supply constraints limiting AI capacity through H1 2026, regulatory scrutiny
in EU cloud markets, competition from AWS/Google in AI services, and elevated valuation multiple
leaving little room for execution missteps.
"""

elements.append(Paragraph(exec_summary, body_style))
elements.append(Spacer(1, 0.2*inch))

# ==================== VERDICT BOX ====================

verdict_data = [
    ['INVESTMENT VERDICT', 'BUY - Strong Conviction'],
    ['Recommended Action', 'Accumulate on dips below $470'],
    ['Price Target (12-month)', '$625 (Consensus: $628, Range: $500-$730)'],
    ['Expected Return', '+29% to +51% upside potential'],
    ['Risk Level', 'Medium (24% annual volatility)'],
    ['Position Sizing', '5-7% of portfolio ($12,500 - $17,500 for $250K portfolio)'],
]

verdict_table = Table(verdict_data, colWidths=[2.5*inch, 4.5*inch])
verdict_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 11),
    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f4f8')),
    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2c5aa0')),
    ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
elements.append(verdict_table)
elements.append(PageBreak())

# ==================== PAGE 2: QUANTITATIVE ANALYSIS ====================

elements.append(Paragraph("<b>QUANTITATIVE ANALYSIS</b>", header_style))
elements.append(Paragraph("Risk Metrics (252-day analysis vs SPY benchmark)", subheader_style))

risk_data = [
    ['Metric', 'Value', 'Interpretation'],
    ['Value at Risk (95%)', '-2.34%', '95% of days, losses won\'t exceed 2.34%'],
    ['CVaR (95%)', '-3.20%', 'Average loss when VaR is exceeded'],
    ['Sharpe Ratio', '0.26', 'Poor risk-adjusted returns (< 1.0 target)'],
    ['Sortino Ratio', '0.40', 'Downside-focused risk metric'],
    ['Maximum Drawdown', '-21.83%', 'Worst peak-to-trough decline'],
    ['Calmar Ratio', '0.49', 'Return per unit of drawdown risk'],
    ['Annual Volatility', '24.32%', 'Medium volatility (20-40% range)'],
    ['Beta (vs SPY)', '0.88', 'Below-market systematic risk'],
    ['Alpha (vs SPY)', '-1.22%', 'Underperforming benchmark by 1.22% annually'],
]

risk_table = Table(risk_data, colWidths=[2*inch, 1.5*inch, 3.5*inch])
risk_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
elements.append(risk_table)
elements.append(Spacer(1, 0.2*inch))

# Momentum Analysis
elements.append(Paragraph("Momentum Indicators (90-day analysis)", subheader_style))

momentum_data = [
    ['Indicator', 'Value', 'Signal', 'Interpretation'],
    ['RSI (14-day)', '40.76', 'Neutral', 'No extreme overbought/oversold condition'],
    ['MACD', '-6.39', 'Bullish', 'MACD above signal line (+0.11 histogram)'],
    ['Stochastic %K', '23.17', 'Neutral', '%K between 20-80 range'],
    ['Williams %R', '-76.83', 'Neutral', 'Mid-range reading'],
    ['Rate of Change', '-2.18%', 'Bearish', 'Negative 90-day momentum'],
    ['Confluence', '1/5 Bullish, 1/5 Bearish', 'Mixed', 'No clear directional bias'],
]

momentum_table = Table(momentum_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 3.1*inch])
momentum_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
elements.append(momentum_table)
elements.append(Spacer(1, 0.2*inch))

# Volatility Analysis
elements.append(Paragraph("Volatility & Technical Indicators (90-day analysis)", subheader_style))

volatility_data = [
    ['Metric', 'Value', 'Interpretation'],
    ['Volatility Regime', 'LOW', 'Favorable for larger position sizes (10-20% max)'],
    ['Average True Range', '$9.11 (1.88%)', 'Daily price movement range'],
    ['ATR Stop Loss', '$18.21', 'Suggested stop: 2x ATR below entry'],
    ['Annual Volatility', '21.34%', 'Below long-term average, stable period'],
    ['Bollinger Band %B', '0.594', 'Price in upper half of bands'],
    ['Band Width', '5.20%', 'Narrow bands suggest potential breakout'],
    ['Upper BB', '$494.15', 'Resistance level'],
    ['Lower BB', '$469.09', 'Support level'],
]

volatility_table = Table(volatility_data, colWidths=[2.2*inch, 1.8*inch, 3*inch])
volatility_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
elements.append(volatility_table)
elements.append(PageBreak())

# ==================== PAGE 3: PORTFOLIO STRATEGY ====================

elements.append(Paragraph("<b>PORTFOLIO STRATEGY & POSITION SIZING</b>", header_style))

strategy_text = """
<b>Recommended Allocation:</b> For a $250,000 portfolio, we recommend a 5-7% allocation to MSFT,
representing a core technology holding with lower volatility than high-beta growth stocks. This
translates to <b>$12,500 - $17,500</b> initial position, with room to scale up to 10% ($25,000)
on strong execution or market pullbacks below $460.

<b>Position Size Rationale:</b>
• Low volatility regime (21.34% annual vol) supports larger position vs high-beta names
• Beta of 0.88 provides downside protection in market corrections
• ATR-based stop loss of $18.21 (2x ATR) limits downside to ~3.8% from current levels
• Strong fundamentals and $392B backlog reduce business risk
• Diversification: 5-7% allocation maintains balanced portfolio construction
"""

elements.append(Paragraph(strategy_text, body_style))
elements.append(Spacer(1, 0.2*inch))

# Position sizing table
sizing_data = [
    ['Portfolio Size', 'Conservative (5%)', 'Moderate (7%)', 'Aggressive (10%)'],
    ['$250,000', '$12,500 (26 shares)', '$17,500 (36 shares)', '$25,000 (52 shares)'],
    ['Position Risk (2x ATR SL)', '-$468 (-3.7%)', '-$656 (-3.7%)', '-$947 (-3.8%)'],
    ['Price Target Gain (+29%)', '+$3,625', '+$5,075', '+$7,250'],
]

sizing_table = Table(sizing_data, colWidths=[1.8*inch, 1.7*inch, 1.7*inch, 1.8*inch])
sizing_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')]),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
elements.append(sizing_table)
elements.append(Spacer(1, 0.3*inch))

# Entry strategy
elements.append(Paragraph("Entry Strategy & Risk Management", subheader_style))

entry_text = """
<b>Layered Entry Approach:</b>
1. <b>Initial Position (50%):</b> Buy $6,250-$8,750 at current levels ($483-$485)
2. <b>Scale-In Targets (25% each):</b>
   • $470-$475: Add 25% on technical support pullback
   • $460-$465: Add final 25% on deeper correction (near lower BB and 200-day MA support)

<b>Stop Loss:</b> 2x ATR stop at $465 (-3.8% from entry) or technical break below $455 (violated 200-day MA)

<b>Take Profit Levels:</b>
• <b>Target 1 ($550):</b> +14% - Trim 30% of position at prior resistance
• <b>Target 2 ($625):</b> +29% - Analyst consensus, trim another 40%
• <b>Target 3 ($700):</b> +45% - Bull case scenario, hold remaining 30% long-term

<b>Rebalancing:</b> If position exceeds 12% of portfolio due to appreciation, trim to 10% and
reallocate to underweight holdings or cash for new opportunities.
"""

elements.append(Paragraph(entry_text, body_style))
elements.append(PageBreak())

# ==================== PAGE 4: MARKET RESEARCH & CATALYSTS ====================

elements.append(Paragraph("<b>MARKET RESEARCH & 2026 CATALYSTS</b>", header_style))
elements.append(Paragraph("Company Overview", subheader_style))

overview_text = """
<b>Microsoft Corporation (NASDAQ: MSFT)</b> is a diversified technology leader with dominant
positions across cloud infrastructure (Azure), productivity software (Microsoft 365), enterprise
applications (Dynamics), gaming (Xbox), and artificial intelligence. With a $3.6T market
capitalization, MSFT is one of the world's most valuable companies.

<b>Business Segments:</b>
• <b>Intelligent Cloud (40% revenue):</b> Azure, Windows Server, SQL Server, GitHub
• <b>Productivity & Business Processes (31% revenue):</b> Office 365, LinkedIn, Dynamics 365
• <b>More Personal Computing (29% revenue):</b> Windows, Surface, Xbox, Search (Bing)

<b>Recent Performance:</b> Q1 FY2026 revenue grew 18% YoY to $77.7B, with EPS up 23% to $4.13.
Azure revenue surpassed $75B annually (+34% YoY), while AI business reached $13B run rate
(+175% YoY). The company maintains a $392B backlog, indicating strong multi-year demand visibility.
"""

elements.append(Paragraph(overview_text, body_style))
elements.append(Spacer(1, 0.2*inch))

elements.append(Paragraph("2026 Growth Catalysts", subheader_style))

catalysts_data = [
    ['Catalyst', 'Impact', 'Timeline'],
    ['AI Copilot Monetization',
     '900M monthly AI users, expanding to M365/Dynamics/GitHub with July 2026 price increases',
     'H1-H2 2026'],
    ['Azure Market Share Gains',
     '40% growth vs 17% for AWS. Supply constraints easing in H2 2026',
     'Ongoing'],
    ['OpenAI Partnership',
     'Exclusive cloud provider for ChatGPT/GPT-4, driving $13B+ AI revenue',
     'Multi-year'],
    ['Global Expansion',
     '$17.5B India investment, $5.4B Canada investment for AI infrastructure',
     '2026-2028'],
    ['M365 Price Increases',
     'Global commercial and government suite price hikes boost ARPU',
     'July 2026'],
    ['Quantum Computing',
     'Next-gen cloud accelerator beyond AI, early mover advantage',
     '2027+'],
]

catalysts_table = Table(catalysts_data, colWidths=[1.8*inch, 3.5*inch, 1.7*inch])
catalysts_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
elements.append(catalysts_table)
elements.append(Spacer(1, 0.3*inch))

elements.append(Paragraph("Analyst Sentiment & Price Targets", subheader_style))

analyst_text = """
<b>Wall Street Consensus:</b> 56 of 57 analysts rate MSFT as Buy/Strong Buy, with only 1 Hold
and zero Sell ratings. The consensus 12-month price target is <b>$628</b> (range: $500-$730),
implying 30% upside from current levels.

<b>Recent Notable Targets:</b>
• <b>$700:</b> Bull case based on 50% Azure growth projections and $5T market cap scenario
• <b>$650:</b> Wall Street base case if AI capacity constraints ease and Copilot adoption accelerates
• <b>$586:</b> Guggenheim (Oct 2025 upgrade)
• <b>$500:</b> Rothschild & Co conservative case (Nov 2025)

<b>Key Debates:</b> Bulls focus on AI monetization inflection and Azure share gains. Bears cite
elevated P/E (35x trailing, 26x forward), supply constraints limiting growth through H1 2026,
and competitive threats from AWS Bedrock and Google Gemini in enterprise AI.
"""

elements.append(Paragraph(analyst_text, body_style))
elements.append(PageBreak())

# ==================== PAGE 5: COMPETITIVE LANDSCAPE & RISKS ====================

elements.append(Paragraph("<b>COMPETITIVE LANDSCAPE & RISK ANALYSIS</b>", header_style))
elements.append(Paragraph("Cloud Market Position", subheader_style))

cloud_text = """
<b>Market Share (Q2 2025):</b>
• <b>AWS:</b> 30% (growth: 17% YoY)
• <b>Azure:</b> 20% (growth: 40% YoY) ← Microsoft
• <b>Google Cloud:</b> 13% (growth: 32% YoY)
• <b>Others:</b> 37%

<b>Competitive Dynamics:</b> While AWS maintains overall leadership, Microsoft's 40% growth rate
(2.4x AWS's pace) demonstrates accelerating market share gains. Azure benefits from enterprise
lock-in via Microsoft 365 integration, GitHub Copilot bundling, and the exclusive OpenAI
partnership. Google Cloud poses a threat with Gemini AI models and aggressive pricing.

<b>Microsoft's Advantages:</b>
• Seamless integration with Office 365, Teams, Dynamics (ecosystem moat)
• OpenAI exclusive partnership (ChatGPT runs on Azure infrastructure)
• Hybrid cloud strength (Azure Stack) for regulated industries
• Sales force expertise in enterprise relationships

<b>Competitive Threats:</b>
• AWS Bedrock platform offering multiple AI models (Amazon, Anthropic, Meta)
• Google Gemini models with strong performance benchmarks
• Oracle and Alibaba gaining share in regional markets
"""

elements.append(Paragraph(cloud_text, body_style))
elements.append(Spacer(1, 0.2*inch))

elements.append(Paragraph("Key Investment Risks", subheader_style))

risks_data = [
    ['Risk Category', 'Description', 'Mitigation/Probability'],
    ['Supply Constraints',
     'AI capacity shortages through H1 2026 limiting Azure growth potential',
     'HIGH: Massive capex ($94B 2025) addresses. Easing expected H2 2026'],
    ['Valuation Compression',
     '25.8x forward P/E leaves little room for misses. Tech multiple contraction risk',
     'MEDIUM: Justified by 18% growth and AI leadership, but sensitive to rates'],
    ['Regulatory Risk',
     'EU Digital Markets Act investigations, UK cloud lawsuit, antitrust scrutiny',
     'MEDIUM: Legal costs manageable, but could limit bundling strategies'],
    ['AI ROI Concerns',
     'Enterprise customers questioning AI spending returns, adoption slower than expected',
     'LOW: 900M users and $13B revenue validates demand, but watch metrics'],
    ['Competition',
     'AWS Bedrock, Google Gemini, open-source models pressuring margins and market share',
     'MEDIUM: Microsoft has integration moat, but pricing power at risk'],
    ['Macroeconomic',
     'IT budget cuts in recession, FX headwinds (strong dollar), rate sensitivity',
     'LOW-MEDIUM: Diversified revenue base, but cyclical exposure remains'],
]

risks_table = Table(risks_data, colWidths=[1.5*inch, 3.2*inch, 2.3*inch])
risks_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
elements.append(risks_table)
elements.append(Spacer(1, 0.2*inch))

risk_summary = """
<b>Risk Assessment Summary:</b> Microsoft's primary risks center on execution (supply constraints,
AI ROI delivery) and valuation (premium multiple compression). However, the company's competitive
moat, diversified revenue streams, and $392B backlog provide downside protection. We view the
risk/reward as favorable at current levels, with upside catalysts (AI monetization, Azure share
gains) outweighing near-term headwinds.
"""

elements.append(Paragraph(risk_summary, body_style))
elements.append(PageBreak())

# ==================== PAGE 6: TECHNICAL ANALYSIS ====================

elements.append(Paragraph("<b>TECHNICAL ANALYSIS & CHART PATTERNS</b>", header_style))

technical_text = """
<b>Current Price Action:</b> MSFT is trading at $483.98, up +16.48% YTD but down -12.9% from
the 52-week high of $555.45 (set in July 2025). The stock is consolidating in a $470-$495 range,
testing the middle Bollinger Band at $481.62.

<b>Key Support Levels:</b>
• <b>$469-$475:</b> Lower Bollinger Band and psychological support
• <b>$460-$465:</b> 200-day moving average and prior consolidation zone
• <b>$445-$450:</b> Major support from March 2025 breakout

<b>Key Resistance Levels:</b>
• <b>$494-$500:</b> Upper Bollinger Band and December resistance
• <b>$525-$530:</b> Q3 2025 highs, major overhead supply
• <b>$555-$560:</b> All-time high breakout level

<b>Indicator Analysis:</b>
• <b>RSI (40.76):</b> Below neutral 50 line but not oversold. Room for upside before overbought (>70)
• <b>MACD:</b> Recently crossed bullish (histogram +0.11), suggesting momentum shift
• <b>Bollinger Bands:</b> Bandwidth at 5.20% (narrow) indicates low volatility and potential breakout setup
• <b>Volume:</b> Average 22.8M shares/day, below 2024 average of 28M (cautious accumulation)

<b>Chart Pattern:</b> MSFT is forming a bullish ascending triangle with higher lows since October
2025 and flat resistance at $495. A breakout above $500 on strong volume (>30M shares) would
target $550+ (measured move from base).

<b>Technical Verdict:</b> Neutral-to-Bullish. The stock is consolidating after a strong run, with
positive MACD divergence and narrow Bollinger Bands suggesting an imminent directional move. We
favor the upside given fundamental strength, but await a confirmed breakout above $500 for maximum
conviction.
"""

elements.append(Paragraph(technical_text, body_style))
elements.append(Spacer(1, 0.3*inch))

# Support/Resistance table
sr_data = [
    ['Level', 'Price Range', 'Type', 'Strength'],
    ['R3', '$555-$560', 'All-Time High', 'Very Strong'],
    ['R2', '$525-$530', 'Q3 2025 Highs', 'Strong'],
    ['R1', '$494-$500', 'Upper BB / Resistance', 'Moderate'],
    ['Current', '$483.98', 'Mid-Range', '-'],
    ['S1', '$469-$475', 'Lower BB / Support', 'Moderate'],
    ['S2', '$460-$465', '200-day MA', 'Strong'],
    ['S3', '$445-$450', 'Major Support Zone', 'Very Strong'],
]

sr_table = Table(sr_data, colWidths=[1*inch, 1.8*inch, 2.2*inch, 2*inch])
sr_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
    ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#ffffcc')),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, 3), [colors.HexColor('#ffe6e6')]),
    ('ROWBACKGROUNDS', (0, 5), (-1, -1), [colors.HexColor('#e6f7e6')]),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
elements.append(sr_table)
elements.append(PageBreak())

# ==================== PAGE 7: FUNDAMENTAL DEEP DIVE ====================

elements.append(Paragraph("<b>FUNDAMENTAL ANALYSIS & VALUATION</b>", header_style))
elements.append(Paragraph("Key Financial Metrics", subheader_style))

fundamental_data = [
    ['Metric', 'Value', 'vs Industry', 'vs Historical Avg'],
    ['Market Cap', '$3.60T', '1st in Software', 'All-time high'],
    ['P/E Ratio (Forward)', '25.84x', 'Above sector (22x)', 'In-line (25-30x range)'],
    ['EPS (TTM)', '$14.05', 'Growing 20%+ YoY', 'Above trend'],
    ['Revenue Growth', '18% YoY', 'Top quartile', 'Accelerating'],
    ['Dividend Yield', '0.76%', 'Below sector (1.2%)', 'Stable'],
    ['Free Cash Flow', '$70B+ annual', 'Best-in-class', 'Growing 15%+ YoY'],
    ['Gross Margin', '~70%', 'Top tier', 'Expanding (AI mix)'],
    ['Return on Equity', '40%+', 'Excellent', 'Sustained high ROE'],
]

fundamental_table = Table(fundamental_data, colWidths=[1.8*inch, 1.5*inch, 1.8*inch, 1.9*inch])
fundamental_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('BOX', (0, 0), (-1, -1), 1, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
elements.append(fundamental_table)
elements.append(Spacer(1, 0.2*inch))

elements.append(Paragraph("Valuation Analysis", subheader_style))

valuation_text = """
<b>Relative Valuation:</b> At 25.8x forward P/E, MSFT trades at a premium to the S&P 500 (20x)
and the technology sector average (22x), but in-line with its own 5-year historical range
(25-30x). The premium is justified by:
• Best-in-class revenue growth (18% vs sector 12%)
• Superior margins (70% gross, 40%+ operating)
• AI leadership with $13B revenue run rate
• Durable competitive moats in cloud and productivity software

<b>DCF Valuation:</b> Using conservative assumptions (15% revenue CAGR through 2030, terminal
growth 3%, WACC 8.5%), our discounted cash flow model yields a fair value of <b>$620-$650 per share</b>,
aligning with Wall Street consensus.

<b>Comparable Companies:</b>
• <b>Amazon (AWS):</b> 30x forward P/E, 11% revenue growth → MSFT trading at discount to quality
• <b>Alphabet (Google Cloud):</b> 22x forward P/E, 13% growth → MSFT premium justified by faster growth
• <b>Oracle (Cloud):</b> 28x forward P/E, 8% growth → MSFT cheaper on PEG basis (1.4x vs 3.5x)

<b>Valuation Verdict:</b> FAIRLY VALUED with modest upside to intrinsic value. Not a screaming
bargain, but reasonable for a high-quality compounder. We prefer to accumulate on dips below 23x
forward P/E ($460-$470), where risk/reward skews heavily positive.
"""

elements.append(Paragraph(valuation_text, body_style))
elements.append(Spacer(1, 0.2*inch))

elements.append(Paragraph("Balance Sheet & Financial Health", subheader_style))

balance_text = """
<b>Fortress Balance Sheet:</b>
• <b>Cash & Equivalents:</b> $100B+ (provides flexibility for M&A, buybacks, dividends)
• <b>Debt:</b> $75B (manageable at 0.75x net debt/EBITDA)
• <b>Credit Rating:</b> AAA (only 2 U.S. companies with top rating: MSFT and JNJ)
• <b>Free Cash Flow:</b> $70B+ annually (covers capex, dividends, buybacks)

<b>Capital Allocation:</b> Microsoft returns $20B+ annually to shareholders via dividends ($2.87/share)
and buybacks. However, the company is prioritizing AI infrastructure capex ($94B in 2025, up 45% YoY)
over aggressive shareholder returns in the near term. We view this as prudent given the massive TAM
in cloud and AI.

<b>Financial Strength Rating:</b> EXCELLENT. No solvency concerns, robust cash generation, and
disciplined capital allocation.
"""

elements.append(Paragraph(balance_text, body_style))
elements.append(PageBreak())

# ==================== PAGE 8: CONCLUSIONS & DISCLAIMER ====================

elements.append(Paragraph("<b>INVESTMENT CONCLUSION</b>", header_style))

conclusion_text = """
<b>Summary of Findings:</b>

Microsoft represents a high-quality, lower-risk way to gain exposure to secular growth in cloud
computing and artificial intelligence. The company's execution across Azure (40% growth), AI
monetization ($13B run rate, +175% YoY), and productivity franchises (M365 price increases in 2026)
positions it for sustained 15-20% revenue growth over the next 2-3 years.

<b>Key Strengths:</b>
• <b>AI Leadership:</b> OpenAI partnership, 900M monthly AI users, $13B AI revenue run rate
• <b>Azure Momentum:</b> 40% growth taking share from AWS, $75B+ annual revenue
• <b>Competitive Moats:</b> Enterprise lock-in via Office 365, GitHub, Dynamics integration
• <b>Financial Strength:</b> AAA rating, $100B cash, $70B FCF, fortress balance sheet
• <b>Margin Expansion:</b> AI and cloud mix driving gross margins to 70%+
• <b>Valuation:</b> Fairly valued at 25.8x forward P/E, in-line with historical range

<b>Key Risks to Monitor:</b>
• Supply constraints limiting AI growth through H1 2026
• Regulatory scrutiny (EU DMA, UK cloud lawsuit)
• Competition from AWS Bedrock, Google Gemini
• Valuation multiple compression if growth disappoints

<b>Final Recommendation:</b> <b>BUY with 5-7% portfolio allocation</b> ($12,500-$17,500 for $250K
portfolio). Use a layered entry strategy, accumulating 50% at current levels ($483-$485) and scaling
in on dips to $470 and $460. Set a 2x ATR stop loss at $465 to limit downside risk to ~4%.

<b>12-Month Price Target:</b> $625 (base case), with upside to $700 if Azure growth accelerates
and AI capacity constraints ease in H2 2026.

<b>For long-term investors (3-5 year horizon), Microsoft offers:</b>
• Diversified exposure to cloud, AI, productivity, gaming, and quantum computing
• Durable 15%+ annual returns powered by structural tailwinds
• Lower volatility (Beta 0.88) than high-growth tech peers
• Dividend growth and capital appreciation

Microsoft is a core holding for growth-oriented portfolios seeking quality, execution, and exposure
to transformative technology trends.
"""

elements.append(Paragraph(conclusion_text, body_style))
elements.append(Spacer(1, 0.4*inch))

# ==================== DISCLAIMER ====================

disclaimer_box = [
    ['IMPORTANT LEGAL DISCLAIMER'],
]

disclaimer_table = Table(disclaimer_box, colWidths=[7*inch])
disclaimer_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3cd')),
    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 11),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#856404')),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
]))
elements.append(disclaimer_table)
elements.append(Spacer(1, 0.1*inch))

disclaimer_text = """
<b>Educational Purposes Only - Not Investment Advice</b>

This report is provided for educational and informational purposes only and does not constitute
investment advice, financial advice, trading advice, or any other sort of advice. The information
contained herein is based on publicly available data and the author's analysis, which may contain
errors or omissions.

<b>No Warranty:</b> Finance Guru™ makes no representations or warranties regarding the accuracy,
completeness, or timeliness of the information provided. Past performance is not indicative of
future results.

<b>Risk Disclosure:</b> Investing in securities involves risk, including the potential loss of
principal. The strategies and analysis presented may not be suitable for all investors. Before
making any investment decision, you should consult with qualified financial, legal, and tax
professionals who can assess your individual circumstances and risk tolerance.

<b>No Guarantee:</b> There is no guarantee that the price targets, recommendations, or strategies
outlined in this report will be achieved. Market conditions, company performance, and macroeconomic
factors can change rapidly and unpredictably.

<b>Forward-Looking Statements:</b> This report contains forward-looking statements based on current
expectations and assumptions. Actual results may differ materially from those projected.

<b>Independent Research:</b> Readers are encouraged to conduct their own due diligence and research
before making any investment decisions. Do not rely solely on this report.

<b>Data Sources:</b> Market data sourced from Yahoo Finance (yfinance), analyst estimates from
public filings and financial media. Web research via Perplexity and public sources as of December 18, 2025.

<b>Copyright:</b> © 2025 Finance Guru™. All rights reserved. This report is for the exclusive use
of the recipient and may not be reproduced or distributed without permission.

<b>Contact:</b> For questions or concerns about this report, please contact your Finance Guru™
analyst team.

---

<b>Sources & Citations:</b>
This analysis incorporates research from: TS2 Tech, The Motley Fool, Yahoo Finance, Nasdaq,
StockAnalysis, TipRanks, TradingView, Benzinga, Fintel, Stansberry Research, Revolgy, Turbo360,
Microsoft Investor Relations, Tomasz Tunguz, AInvest, and Statista. Full source links available
in web research appendix.
"""

disclaimer_para = Paragraph(disclaimer_text, ParagraphStyle(
    'Disclaimer',
    parent=small_style,
    fontSize=7,
    textColor=colors.HexColor('#666666'),
    alignment=TA_JUSTIFY
))
elements.append(disclaimer_para)

# Build PDF
doc.build(elements)

print(f"✅ PDF report generated successfully!")
print(f"📄 File: {OUTPUT_PATH}")
print(f"📊 Verdict: BUY - Strong Conviction")
print(f"🎯 Price Target: $625 (+29% upside)")
print(f"💰 Position Size: $12,500-$17,500 (5-7% of $250K portfolio)")
