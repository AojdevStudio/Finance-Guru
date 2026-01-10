#!/usr/bin/env python3
"""
NVDA Analysis Report Generator
Generates comprehensive PDF report for NVDA 2026 watchlist analysis
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

# Finance Guru Branding Colors
NAVY = colors.HexColor('#1a365d')
GOLD = colors.HexColor('#d69e2e')
LIGHT_GRAY = colors.HexColor('#f7fafc')
DARK_GRAY = colors.HexColor('#2d3748')

def create_styles():
    """Create custom styles for the report"""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=NAVY,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))

    # Subtitle style
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=GOLD,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica'
    ))

    # Section heading
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=NAVY,
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=2,
        borderColor=GOLD,
        borderPadding=5
    ))

    # Subsection heading
    styles.add(ParagraphStyle(
        name='SubsectionHeading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=NAVY,
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    ))

    # Body text
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_GRAY,
        spaceAfter=10,
        leading=14
    ))

    # Metric value (large numbers)
    styles.add(ParagraphStyle(
        name='MetricValue',
        parent=styles['Normal'],
        fontSize=18,
        textColor=NAVY,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER
    ))

    # Disclaimer
    styles.add(ParagraphStyle(
        name='Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        spaceAfter=10,
        leading=10,
        alignment=TA_CENTER
    ))

    return styles

def create_header_footer(canvas, doc):
    """Add header and footer to each page"""
    canvas.saveState()

    # Footer
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(inch, 0.5 * inch, f"Finance Guru™ - Private Family Office Analysis")
    canvas.drawRightString(7.5 * inch, 0.5 * inch, f"Page {doc.page}")
    canvas.drawCentredString(4.25 * inch, 0.5 * inch, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    canvas.restoreState()

def create_metric_table(data, col_widths=None):
    """Create a styled table for metrics"""
    if col_widths is None:
        col_widths = [2.5*inch, 2*inch]

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 1), (-1, -1), DARK_GRAY),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    return table

def generate_nvda_report():
    """Generate the comprehensive NVDA analysis report"""

    # Create output directory if it doesn't exist
    output_dir = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "NVDA-analysis-2025-12-18.pdf")

    # Create document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for flowables
    story = []
    styles = create_styles()

    # ========================================
    # TITLE PAGE
    # ========================================
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("NVIDIA CORPORATION (NVDA)", styles['CustomTitle']))
    story.append(Paragraph("2026 Watchlist Analysis", styles['Subtitle']))
    story.append(Spacer(1, 0.3*inch))

    # Executive summary box
    exec_summary_data = [
        ['Current Price', '$174.14'],
        ['Current Holdings', '12 shares (+108% gain)'],
        ['Analysis Date', 'December 18, 2025'],
        ['Analyst Team', 'Finance Guru Multi-Agent System'],
    ]
    story.append(create_metric_table(exec_summary_data))
    story.append(Spacer(1, 0.3*inch))

    # Quick verdict
    story.append(Paragraph("FINAL VERDICT: STRONG BUY", styles['MetricValue']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "NVIDIA remains the dominant AI infrastructure leader with exceptional 2026 catalysts. "
        "Despite near-term volatility and competitive pressures, the company's technological moat, "
        "Blackwell ramp, and $212B+ revenue trajectory support aggressive accumulation for long-term investors.",
        styles['CustomBody']
    ))

    story.append(PageBreak())

    # ========================================
    # PHASE 1: MARKET RESEARCH (DR. ALEKSANDR PETROV)
    # ========================================
    story.append(Paragraph("PHASE 1: MARKET RESEARCH", styles['SectionHeading']))
    story.append(Paragraph("Agent: Dr. Aleksandr Petrov, Market Researcher", styles['CustomBody']))
    story.append(Spacer(1, 0.2*inch))

    # Company Overview
    story.append(Paragraph("Company Overview", styles['SubsectionHeading']))
    story.append(Paragraph(
        "<b>Market Position:</b> NVIDIA controls 92% of the discrete GPU market and 80% of the AI accelerator segment "
        "as of Q3 2025, with a market capitalization of approximately $4.517 trillion.",
        styles['CustomBody']
    ))
    story.append(Paragraph(
        "<b>AI Infrastructure Leadership:</b> NVIDIA provides 10 gigawatts of compute power to OpenAI, "
        "10x larger than AMD's 6-gigawatt contract. The company is the key enabler of global AI infrastructure buildout "
        "with over 94% share of the discrete GPU market in Q2 2025.",
        styles['CustomBody']
    ))

    # Revenue & Growth
    story.append(Paragraph("Revenue & Growth Performance", styles['SubsectionHeading']))

    revenue_data = [
        ['Metric', 'Value'],
        ['FY2026 Revenue (Est.)', '$170-212B (+30-48% YoY)'],
        ['Q3 2025 Revenue', '$57.01B (+66% YoY)'],
        ['Data Center Division', '$51.2B (90% of total revenue)'],
        ['FY2027 Consensus', '$313B (+48% YoY)'],
    ]
    story.append(create_metric_table(revenue_data))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "NVIDIA's fiscal 2026 revenue forecast represents exceptional growth, largely fueled by voracious demand for AI chips. "
        "Management sees the company on track to generate about $212 billion in total revenue in fiscal 2026 "
        "(year ending roughly January 31, 2026).",
        styles['CustomBody']
    ))

    # Blackwell & Next-Gen Chips
    story.append(Paragraph("Blackwell Architecture & Rubin Roadmap", styles['SubsectionHeading']))
    story.append(Paragraph(
        "<b>Blackwell Performance:</b> CEO Jensen Huang stated that Blackwell sales are 'off the charts' and that cloud GPUs "
        "are sold out, emphasizing continued acceleration across training and inference demand.",
        styles['CustomBody']
    ))
    story.append(Paragraph(
        "<b>Revenue Visibility:</b> CFO Colette Kress confirmed NVIDIA has 'visibility to a half-trillion dollars' in Blackwell "
        "and Rubin AI chip revenue from the start of 2025 through the end of 2026, with that number likely to rise as more deals are signed.",
        styles['CustomBody']
    ))
    story.append(Paragraph(
        "<b>Rubin Architecture:</b> Next-generation Vera Rubin architecture has taped out, and the company is 'working feverishly' "
        "to bring Rubin systems to market in the second half of 2026.",
        styles['CustomBody']
    ))

    # 2026 Catalysts
    story.append(Paragraph("2026 Catalysts", styles['SubsectionHeading']))

    catalysts = [
        "<b>Blackwell Ramp:</b> Full production ramp of Blackwell architecture throughout 2026 with sold-out capacity",
        "<b>Inference Growth:</b> Deloitte projects inference will account for 2/3 of all AI compute by 2026 (up from 1/3 in 2023)",
        "<b>AI Market Expansion:</b> AI market projected to grow at 37% CAGR through 2030 (Grand View Research)",
        "<b>Data Center Dominance:</b> Continued expansion in hyperscale data center deployments globally",
        "<b>Software Ecosystem:</b> CUDA moat and comprehensive AI software stack remains unmatched",
        "<b>Rubin Launch:</b> Next-gen architecture launching H2 2026 maintains technological leadership"
    ]

    for catalyst in catalysts:
        story.append(Paragraph(f"• {catalyst}", styles['CustomBody']))

    story.append(Spacer(1, 0.15*inch))

    # Competitive Landscape
    story.append(Paragraph("Competitive Threats & Market Share", styles['SubsectionHeading']))

    story.append(Paragraph(
        "<b>AMD's Challenge:</b> AMD is launching Instinct MI450 series GPUs in 2026 based on CDNA 5 architecture (TSMC 2nm). "
        "Strategic partnership with OpenAI for 6 gigawatts of AMD Instinct GPUs (1 GW deployment starting H2 2026). "
        "AMD CEO Lisa Su expects tens of billions in annual AI data-center revenue starting 2027, potentially exceeding $100B over the next few years. "
        "MI300X outclasses H100 in memory capacity for certain workloads.",
        styles['CustomBody']
    ))

    story.append(Paragraph(
        "<b>Intel's Position:</b> Intel holds <1% of discrete AI accelerator market despite once holding 99% server processor share. "
        "Betting on affordability with Gaudi AI chips but remains far behind. Planning Falcon Shores successor (combining x86 with GPU) by 2025-2026.",
        styles['CustomBody']
    ))

    story.append(Paragraph(
        "<b>Custom Silicon Threat:</b> JPMorgan projects custom chips from Google, Amazon, Meta, and OpenAI will account for 45% "
        "of AI chip market by 2028 (up from 37% in 2024). Hyperscalers building custom silicon to avoid NVIDIA monopoly pricing "
        "and improve cloud rental margins.",
        styles['CustomBody']
    ))

    # Risk Factors
    story.append(Paragraph("Key Risk Factors", styles['SubsectionHeading']))

    risks = [
        "<b>AI Spending Scrutiny:</b> Investor anxiety about AI infrastructure ROI and potential spending slowdown in 2026",
        "<b>Valuation Concerns:</b> Trading at normalized P/E ratio around 45, significantly above broader market",
        "<b>Stock Volatility:</b> Down 17% from October 2025 peak, subject to sentiment swings",
        "<b>Competition Intensifying:</b> AMD gaining ground, custom silicon threat from hyperscalers",
        "<b>Geopolitical Risk:</b> U.S.-China trade tensions, export restrictions, potential tariffs affecting supply chain",
        "<b>China Competition:</b> Huawei's Ascend chips growing, potential market share loss in China",
        "<b>Digestion Period:</b> Major customers may pause spending in 2025-2026 to optimize existing investments"
    ]

    for risk in risks:
        story.append(Paragraph(f"• {risk}", styles['CustomBody']))

    story.append(PageBreak())

    # ========================================
    # PHASE 2: QUANTITATIVE ANALYSIS (DR. PRIYA DESAI)
    # ========================================
    story.append(Paragraph("PHASE 2: QUANTITATIVE ANALYSIS", styles['SectionHeading']))
    story.append(Paragraph("Agent: Dr. Priya Desai, Quantitative Analyst", styles['CustomBody']))
    story.append(Spacer(1, 0.2*inch))

    # Risk Metrics
    story.append(Paragraph("Risk Metrics (252-Day Analysis vs SPY)", styles['SubsectionHeading']))

    risk_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['95% VaR (Daily)', '-4.42%', '95% of days, losses won\'t exceed 4.42%'],
        ['95% CVaR (Daily)', '-7.25%', 'When VaR exceeded, avg loss is 7.25%'],
        ['Sharpe Ratio', '0.48', 'Poor (<1.0) - low risk-adjusted returns'],
        ['Sortino Ratio', '0.65', 'Focuses on downside deviation'],
        ['Maximum Drawdown', '-36.88%', 'Worst peak-to-trough decline'],
        ['Calmar Ratio', '0.77', 'Return/Max Drawdown ratio'],
        ['Annual Volatility', '49.30%', 'High volatility (40-80% range)'],
        ['Beta (vs SPY)', '1.83', 'High systematic risk (aggressive)'],
        ['Alpha (vs SPY)', '+8.20%', 'Outperforming SPY by 8.20% annually'],
    ]
    story.append(create_metric_table(risk_data, col_widths=[2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Risk Assessment:</b> NVDA exhibits high volatility (49.3% annually) with significant drawdown risk (-36.88% max). "
        "However, the positive alpha of 8.20% vs SPY demonstrates strong outperformance. Beta of 1.83 indicates aggressive "
        "exposure to market movements - expect amplified gains AND losses. Sharpe ratio of 0.48 is poor, suggesting volatility "
        "is high relative to returns, but this is typical for high-growth tech stocks.",
        styles['CustomBody']
    ))

    # Momentum Analysis
    story.append(Paragraph("Momentum Indicators (90-Day Analysis)", styles['SubsectionHeading']))

    momentum_data = [
        ['Indicator', 'Value', 'Signal', 'Interpretation'],
        ['RSI', '37.14', 'Neutral', 'No extreme condition'],
        ['MACD Line', '-2.89', 'Bearish', 'MACD below signal line'],
        ['Signal Line', '-2.15', 'Bearish', 'Downward momentum'],
        ['Histogram', '-0.74', 'Bearish', 'Negative divergence'],
        ['Stochastic %K', '3.56', 'OVERSOLD', 'Potential reversal up'],
        ['Stochastic %D', '22.80', 'OVERSOLD', '%K < 20 buy signal'],
        ['Williams %R', '-96.44', 'OVERSOLD', '%R < -80 buy signal'],
        ['ROC', '-4.99%', 'Bearish', 'Negative momentum'],
        ['Confluence', '2/5 Bullish, 2/5 Bearish', 'MIXED', 'No clear trend'],
    ]
    story.append(create_metric_table(momentum_data, col_widths=[1.5*inch, 1.3*inch, 1.2*inch, 2.5*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Momentum Assessment:</b> NVDA is showing OVERSOLD conditions on Stochastic and Williams %R, suggesting potential "
        "near-term reversal. However, MACD remains bearish with downward momentum. RSI at 37.14 is neutral (not extreme). "
        "This mixed signal environment indicates we're potentially near a bottom but momentum hasn't yet turned positive. "
        "For long-term investors, oversold conditions present attractive entry opportunities.",
        styles['CustomBody']
    ))

    # Volatility Analysis
    story.append(Paragraph("Volatility Analysis (90-Day Period)", styles['SubsectionHeading']))

    volatility_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['Volatility Regime', 'NORMAL', 'Standard position sizing (5-10%)'],
        ['ATR Value', '$5.61', 'Average daily price range'],
        ['ATR %', '3.22%', 'Relative volatility measure'],
        ['Suggested Stop Loss', '$11.22 (2× ATR)', 'Risk management level'],
        ['Daily Volatility', '1.93%', 'Daily price fluctuation'],
        ['Annual Volatility', '30.66%', 'Annualized volatility (90-day)'],
        ['Bollinger Upper', '$187.20', 'Resistance level'],
        ['Bollinger Middle', '$179.66', 'Mean reversion target'],
        ['Bollinger Lower', '$172.12', 'Support level'],
        ['%B Position', '0.134', 'Near lower band (support)'],
        ['Bandwidth', '8.39%', 'Narrow bands - potential breakout'],
    ]
    story.append(create_metric_table(volatility_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Volatility Assessment:</b> Current price ($174.14) is near Bollinger lower band ($172.12), indicating potential support. "
        "Bandwidth of 8.39% suggests narrow bands - 'the squeeze' - which often precedes significant breakouts. ATR of $5.61 "
        "suggests setting stop losses around $11.22 below entry for risk management. The NORMAL volatility regime supports "
        "standard position sizing of 5-10% of portfolio.",
        styles['CustomBody']
    ))

    # Correlation Analysis
    story.append(Paragraph("Portfolio Correlation (252-Day Analysis)", styles['SubsectionHeading']))

    correlation_data = [
        ['Asset Pair', 'Correlation', 'Level'],
        ['NVDA / VOO', '+0.730', 'VERY HIGH'],
        ['NVDA / PLTR', '+0.576', 'HIGH'],
        ['NVDA / TSLA', '+0.523', 'MODERATE-HIGH'],
        ['PLTR / VOO', '+0.607', 'HIGH'],
        ['TSLA / VOO', '+0.693', 'HIGH'],
        ['PLTR / TSLA', '+0.529', 'HIGH'],
    ]
    story.append(create_metric_table(correlation_data, col_widths=[2.5*inch, 1.5*inch, 2*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Diversification Score: 0.390 (MODERATE)</b>",
        styles['SubsectionHeading']
    ))

    story.append(Paragraph(
        "<b>Portfolio Analysis:</b> Your current portfolio (NVDA, PLTR, TSLA, VOO) has limited diversification with average "
        "correlation of 0.610. NVDA shows VERY HIGH correlation with VOO (0.730), meaning it moves closely with the broader "
        "market. All individual stocks show HIGH correlation with each other (0.52-0.58), indicating similar risk exposure. "
        "This tech-heavy concentration amplifies both gains and losses. Adding NVDA increases tech concentration risk. "
        "Consider position sizing carefully or adding uncorrelated hedges (bonds, commodities, inverse ETFs).",
        styles['CustomBody']
    ))

    story.append(PageBreak())

    # ========================================
    # PHASE 3: STRATEGY RECOMMENDATION (ELENA RODRIGUEZ-PARK)
    # ========================================
    story.append(Paragraph("PHASE 3: STRATEGY RECOMMENDATION", styles['SectionHeading']))
    story.append(Paragraph("Agent: Elena Rodriguez-Park, Strategy Advisor", styles['CustomBody']))
    story.append(Spacer(1, 0.2*inch))

    # Investment Thesis
    story.append(Paragraph("Investment Thesis Summary", styles['SubsectionHeading']))

    thesis_data = [
        ['Category', 'Rating', 'Rationale'],
        ['Market Position', '10/10', 'Dominant 92% GPU share, 80% AI accelerator market'],
        ['Growth Trajectory', '9/10', '$170-212B FY26 revenue (+30-48% YoY)'],
        ['Technological Moat', '10/10', 'Blackwell, Rubin roadmap, CUDA ecosystem unmatched'],
        ['Competitive Advantage', '8/10', 'Strong but facing AMD, custom silicon threats'],
        ['Financial Health', '9/10', 'Exceptional margins, strong cash flow'],
        ['Valuation', '6/10', 'P/E ~45 expensive but justified by growth'],
        ['Risk Profile', '7/10', 'High volatility, geopolitical risks, concentration'],
        ['Catalysts', '9/10', 'Blackwell ramp, Rubin launch, inference growth'],
        ['<b>OVERALL SCORE</b>', '<b>8.5/10</b>', '<b>STRONG BUY for aggressive investors</b>'],
    ]
    story.append(create_metric_table(thesis_data, col_widths=[2*inch, 1.3*inch, 3.2*inch]))
    story.append(Spacer(1, 0.2*inch))

    # Position Sizing Recommendation
    story.append(Paragraph("Position Sizing Recommendation", styles['SubsectionHeading']))

    story.append(Paragraph(
        "<b>Current Position:</b> 12 shares (+108% gain) = ~$2,090 current value",
        styles['CustomBody']
    ))

    story.append(Paragraph(
        "<b>Recommendation:</b> ADD 8-15 additional shares over next 3-6 months",
        styles['CustomBody']
    ))

    story.append(Paragraph(
        "<b>Target Allocation:</b> 10-15% of total portfolio (from current ~8-10%)",
        styles['CustomBody']
    ))

    story.append(Paragraph(
        "<b>Rationale:</b> NVDA is oversold on technical indicators (Stochastic 3.56, Williams %R -96.44) and trading near "
        "Bollinger lower band support. With Blackwell ramping and $500B+ revenue visibility through 2026, the fundamental "
        "thesis remains exceptionally strong. Current volatility presents accumulation opportunity. However, given HIGH "
        "correlation with existing holdings (PLTR, TSLA, VOO), limit incremental exposure to avoid over-concentration in tech.",
        styles['CustomBody']
    ))

    # Entry Strategy
    story.append(Paragraph("Entry Strategy & Execution Plan", styles['SubsectionHeading']))

    entry_strategies = [
        "<b>Strategy 1 - Dollar Cost Averaging (RECOMMENDED):</b> Purchase 2-3 shares monthly over 4-6 months. "
        "This smooths out volatility and reduces timing risk. Start with 3 shares immediately given oversold conditions.",

        "<b>Strategy 2 - Technical Levels:</b> Set limit orders at key support levels: $170 (Bollinger lower), "
        "$165 (psychological support), $160 (strong support). Add 3-4 shares at each level if price declines.",

        "<b>Strategy 3 - Catalyst-Based:</b> Add 5 shares ahead of Blackwell production milestones (Q1 2026), "
        "5 shares on strong earnings beats, 5 shares on Rubin launch announcement (H2 2026).",

        "<b>Strategy 4 - Volatility Exploitation:</b> During VIX spikes >25 or NVDA single-day drops >5%, add 2-3 shares. "
        "Volatility creates opportunity for long-term holders."
    ]

    for strategy in entry_strategies:
        story.append(Paragraph(f"• {strategy}", styles['CustomBody']))

    story.append(Spacer(1, 0.15*inch))

    # Risk Management
    story.append(Paragraph("Risk Management Framework", styles['SubsectionHeading']))

    risk_mgmt = [
        "<b>Stop Loss:</b> Mental stop at -25% from entry ($130 range). Given your +108% gain on existing shares, "
        "you have significant cushion. For NEW shares, use 2× ATR stop loss ($11.22 below entry).",

        "<b>Position Limit:</b> Cap NVDA at 15% of total portfolio to manage concentration risk. Your portfolio is "
        "already tech-heavy - don't exceed this limit.",

        "<b>Correlation Hedge:</b> Consider adding 5-10% inverse QQQ (PSQ) or long bonds (TLT) to hedge tech concentration. "
        "Your 0.390 diversification score indicates need for defensive positions.",

        "<b>Profit Taking:</b> Consider trimming 20% of position if NVDA exceeds $250 (43% gain from current). "
        "Lock in gains and rebalance portfolio.",

        "<b>Monitoring Metrics:</b> Watch weekly: (1) Blackwell production updates, (2) Data center spending trends, "
        "(3) AMD MI450 competitive threats, (4) China trade policy changes, (5) VIX levels for volatility regime changes."
    ]

    for item in risk_mgmt:
        story.append(Paragraph(f"• {item}", styles['CustomBody']))

    story.append(Spacer(1, 0.2*inch))

    # Final Verdict
    story.append(Paragraph("FINAL VERDICT: STRONG BUY", styles['MetricValue']))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Summary:</b> NVIDIA remains the unquestioned leader in AI infrastructure with exceptional growth visibility "
        "through 2026 and beyond. Despite near-term volatility (-17% from peak), elevated valuation (P/E ~45), and rising "
        "competition, the company's technological moat (Blackwell, Rubin, CUDA), dominant market position (92% GPU share), "
        "and massive revenue trajectory ($170-212B in FY26, $313B in FY27) justify aggressive accumulation.",
        styles['CustomBody']
    ))

    story.append(Paragraph(
        "<b>For Ossie's Portfolio:</b> Add 8-15 shares over next 3-6 months using dollar-cost averaging or technical entry "
        "strategy. Current oversold conditions (Stochastic 3.56, Williams %R -96.44) and support at Bollinger lower band "
        "present attractive entry point. Limit total allocation to 10-15% of portfolio given high correlation with existing "
        "PLTR, TSLA, VOO holdings (diversification score 0.390). Consider adding hedges (PSQ, TLT) to manage concentration risk.",
        styles['CustomBody']
    ))

    story.append(Paragraph(
        "<b>Risk Tolerance Match:</b> EXCELLENT fit for aggressive risk tolerance. High volatility (49.3%), significant "
        "drawdown potential (-36.88%), and Beta of 1.83 align perfectly with aggressive growth mandate. Expect turbulence "
        "but maintain conviction through volatility given structural AI megatrend.",
        styles['CustomBody']
    ))

    story.append(Paragraph(
        "<b>2026 Outlook:</b> NVIDIA is a TOP-TIER 2026 watchlist stock. Blackwell production ramp, Rubin launch (H2 2026), "
        "and inference market expansion (projected to reach 2/3 of AI compute) create multiple catalysts. Wall Street consensus "
        "targets range $240-300 (38-72% upside). 24/7 Wall St. projects $300.14 year-end 2026 target (68.9% gain).",
        styles['CustomBody']
    ))

    story.append(PageBreak())

    # ========================================
    # ANALYST PRICE TARGETS & CONSENSUS
    # ========================================
    story.append(Paragraph("ANALYST PRICE TARGETS & WALL STREET CONSENSUS", styles['SectionHeading']))
    story.append(Spacer(1, 0.15*inch))

    analyst_data = [
        ['Source', 'Price Target', 'Upside', 'Timeframe'],
        ['24/7 Wall St.', '$300.14', '+72.4%', '2026 Year-End'],
        ['MarketWatch Median', '$250.00', '+43.6%', '12-Month'],
        ['MarketWatch Average', '$257.00', '+47.6%', '12-Month'],
        ['MarketWatch High', '$432.78', '+148.6%', '12-Month'],
        ['MarketWatch Low', '$140.00', '-19.6%', '12-Month'],
        ['Consensus Range', '$240-$300', '+38% to +72%', '2026'],
    ]
    story.append(create_metric_table(analyst_data, col_widths=[2*inch, 1.5*inch, 1.3*inch, 1.7*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Wall Street Consensus:</b> Strong Buy rating across dozens of covering analysts. Median price target of $250 "
        "implies 43.6% upside from current $174.14 price. 24/7 Wall St.'s $300.14 target accounts for tariff risks, "
        "DeepSeek competition, and Blackwell supply constraints - still projects 72.4% gain.",
        styles['CustomBody']
    ))

    story.append(Spacer(1, 0.2*inch))

    # ========================================
    # KEY METRICS DASHBOARD
    # ========================================
    story.append(Paragraph("KEY METRICS DASHBOARD", styles['SectionHeading']))
    story.append(Spacer(1, 0.15*inch))

    dashboard_data = [
        ['MARKET DATA', ''],
        ['Current Price', '$174.14 (+1.87% today)'],
        ['52-Week Range', '$108-$210'],
        ['Market Cap', '$4.517 Trillion'],
        ['P/E Ratio', '~45x'],
        ['', ''],
        ['FINANCIAL METRICS', ''],
        ['FY26 Revenue (Est.)', '$170-212B (+30-48% YoY)'],
        ['Q3 2025 Revenue', '$57.01B (+66% YoY)'],
        ['Data Center Revenue', '$51.2B (90% of total)'],
        ['FY27 Consensus', '$313B (+48% YoY)'],
        ['', ''],
        ['RISK METRICS', ''],
        ['Beta (vs SPY)', '1.83 (High)'],
        ['Annual Volatility', '49.30% (High)'],
        ['Max Drawdown', '-36.88%'],
        ['Sharpe Ratio', '0.48 (Poor)'],
        ['Alpha vs SPY', '+8.20%'],
        ['', ''],
        ['MOMENTUM INDICATORS', ''],
        ['RSI', '37.14 (Neutral)'],
        ['Stochastic %K', '3.56 (OVERSOLD)'],
        ['Williams %R', '-96.44 (OVERSOLD)'],
        ['MACD', 'Bearish'],
        ['', ''],
        ['MARKET POSITION', ''],
        ['GPU Market Share', '92%'],
        ['AI Accelerator Share', '80%'],
        ['Key Competitor (AMD)', '6 GW OpenAI contract vs NVDA 10 GW'],
    ]
    story.append(create_metric_table(dashboard_data, col_widths=[3*inch, 3.5*inch]))

    story.append(PageBreak())

    # ========================================
    # APPENDIX: DATA SOURCES & METHODOLOGY
    # ========================================
    story.append(Paragraph("APPENDIX: DATA SOURCES & METHODOLOGY", styles['SectionHeading']))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph("Market Data Sources", styles['SubsectionHeading']))
    story.append(Paragraph(
        "• Price Data: Yahoo Finance (yfinance) - End-of-day historical prices through December 17, 2025<br/>"
        "• Market Research: Web search across financial news, analyst reports, and company filings (Dec 2025)<br/>"
        "• Benchmark: S&P 500 (SPY) for risk-adjusted performance comparison",
        styles['CustomBody']
    ))

    story.append(Paragraph("Analysis Methodology", styles['SubsectionHeading']))
    story.append(Paragraph(
        "• <b>Risk Metrics:</b> 252-day (1-year) analysis using historical simulation for VaR/CVaR, "
        "rolling volatility, regression analysis for beta/alpha vs SPY benchmark<br/>"
        "• <b>Momentum Analysis:</b> 90-day (1-quarter) technical indicator analysis including RSI (14-period), "
        "MACD (12,26,9), Stochastic (14,3,3), Williams %R (14-period), ROC (10-period)<br/>"
        "• <b>Volatility Analysis:</b> 90-day ATR (14-period), Bollinger Bands (20-period, 2-std), "
        "historical volatility calculation<br/>"
        "• <b>Correlation Analysis:</b> 252-day Pearson correlation matrix across portfolio holdings "
        "(NVDA, PLTR, TSLA, VOO)",
        styles['CustomBody']
    ))

    story.append(Paragraph("Agent Team", styles['SubsectionHeading']))
    story.append(Paragraph(
        "• <b>Dr. Aleksandr Petrov</b> - Market Research & Fundamental Analysis<br/>"
        "• <b>Dr. Priya Desai</b> - Quantitative Analysis & Risk Metrics<br/>"
        "• <b>Elena Rodriguez-Park</b> - Strategy Development & Portfolio Construction<br/>"
        "• <b>Finance Guru™ Platform</b> - Multi-agent orchestration and synthesis",
        styles['CustomBody']
    ))

    story.append(Spacer(1, 0.3*inch))

    # ========================================
    # DISCLAIMER
    # ========================================
    story.append(Paragraph("IMPORTANT DISCLAIMER", styles['SubsectionHeading']))
    story.append(Paragraph(
        "This report is for educational and informational purposes only. It does not constitute investment advice, "
        "financial advice, trading advice, or any other type of advice. The information presented is based on historical data "
        "and forward-looking projections that may not materialize. Past performance does not guarantee future results. "
        "All investments carry risk, including potential loss of principal. NVIDIA Corporation (NVDA) is a volatile, "
        "high-risk equity security subject to market fluctuations, competitive threats, regulatory changes, and geopolitical risks. "
        "The analysis reflects opinions as of December 18, 2025 and may become outdated. "
        "You should conduct your own research and consult with qualified financial professionals before making any investment decisions. "
        "Finance Guru™ and its agents are analytical tools, not registered investment advisors. "
        "Trade at your own risk and never invest more than you can afford to lose.",
        styles['Disclaimer']
    ))

    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(
        "Finance Guru™ - Private Family Office Analysis System | Generated: December 18, 2025",
        styles['Disclaimer']
    ))

    # Build PDF
    doc.build(story, onFirstPage=create_header_footer, onLaterPages=create_header_footer)

    return output_file

if __name__ == "__main__":
    output_file = generate_nvda_report()
    print(f"\n✅ NVDA Analysis Report Generated Successfully!")
    print(f"📄 Location: {output_file}")
    print(f"📊 Report includes comprehensive market research, quantitative analysis, and strategy recommendations")
    print(f"🎯 Final Verdict: STRONG BUY")
