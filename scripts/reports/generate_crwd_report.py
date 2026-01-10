#!/usr/bin/env python3
"""
CRWD Analysis Report Generator
Generates comprehensive PDF report for CrowdStrike 2026 analysis
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

# Finance Guru Branding Colors
NAVY = colors.HexColor('#1a365d')
GOLD = colors.HexColor('#d69e2e')
LIGHT_GRAY = colors.HexColor('#f7fafc')
DARK_GRAY = colors.HexColor('#2d3748')
GREEN = colors.HexColor('#38a169')
RED = colors.HexColor('#e53e3e')

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

    # Custom bullet style
    styles.add(ParagraphStyle(
        name='CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_GRAY,
        spaceAfter=6,
        leading=14,
        leftIndent=20,
        bulletIndent=10
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

def generate_crwd_report():
    """Generate the comprehensive CRWD analysis report"""

    # Create output directory if it doesn't exist
    output_dir = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "CRWD-analysis-2025-12-18.pdf")

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
    story.append(Paragraph("CROWDSTRIKE HOLDINGS (CRWD)", styles['CustomTitle']))
    story.append(Paragraph("2026 Investment Analysis", styles['Subtitle']))
    story.append(Spacer(1, 0.3*inch))

    # Executive summary box
    exec_summary_data = [
        ['Current Price', '$477.26'],
        ['YTD Performance', '+108.2% (as of Dec 2025)'],
        ['Analysis Date', 'December 18, 2025'],
        ['Analyst Team', 'Finance Guru Multi-Agent System'],
    ]
    story.append(create_metric_table(exec_summary_data))
    story.append(Spacer(1, 0.3*inch))

    # Verdict Box
    verdict_data = [
        ['FINAL VERDICT', 'BUY'],
        ['Rating', 'MODERATE BUY'],
        ['Conviction Level', 'MEDIUM (6/10)'],
        ['Risk Level', 'HIGH'],
    ]
    story.append(create_metric_table(verdict_data, col_widths=[3*inch, 2*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "CrowdStrike is the #1 cybersecurity platform player with a dominant 21% market share "
        "in endpoint protection, strong AI-driven growth catalysts, and a credible path to $10B ARR by 2031. "
        "However, premium valuation (28× forward sales), intense competition from Microsoft/Palo Alto/Fortinet, "
        "and decelerating ARR growth (22% vs prior 32%) warrant measured position sizing. "
        "Recommended for long-term investors with high risk tolerance.",
        styles['CustomBody']
    ))

    story.append(PageBreak())

    # ========================================
    # EXECUTIVE SUMMARY
    # ========================================
    story.append(Paragraph("Executive Summary", styles['SectionHeading']))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Investment Thesis", styles['SubsectionHeading']))
    story.append(Paragraph(
        "CrowdStrike has established itself as the AI-native cybersecurity leader, transitioning from "
        "an endpoint protection specialist to a comprehensive platform consolidator. With 32 cloud modules "
        "spanning endpoint, cloud, identity, and SIEM solutions, CRWD is capitalizing on the secular shift "
        "toward platform consolidation as enterprises seek to reduce security tool sprawl.",
        styles['CustomBody']
    ))

    story.append(Paragraph(
        "The company's Falcon Flex licensing model has proven to be a powerful growth driver, enabling "
        "customers to consume the entire product portfolio flexibly. Falcon Flex ARR reached $1.35B in Q3 FY2026, "
        "more than triple year-ago levels, with 200+ customers expanding contracts in the quarter.",
        styles['CustomBody']
    ))

    story.append(Paragraph("Key Strengths", styles['SubsectionHeading']))
    bullet_points = [
        "<b>Market Leadership:</b> 21.21% market share in endpoint protection (2× nearest competitor)",
        "<b>Platform Moat:</b> 32 cloud modules create high switching costs and expansion opportunities",
        "<b>Financial Excellence:</b> $4.4B+ ARR with 20%+ growth, $1.07B free cash flow (27% FCF margin)",
        "<b>AI Integration:</b> Charlotte AI, Signal, and AI Systems Security Assessment driving differentiation",
        "<b>Customer Quality:</b> S&P 500 constituent, Leader in Gartner MQ for 6 consecutive years",
    ]
    for point in bullet_points:
        story.append(Paragraph(f"• {point}", styles['CustomBody']))

    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("Key Risks", styles['SubsectionHeading']))
    risk_points = [
        "<b>Valuation:</b> Trading at 28.5× forward sales vs peers at 18-20×, requiring perfect execution",
        "<b>Competition:</b> Microsoft, Palo Alto, Fortinet investing heavily in AI-driven security",
        "<b>Growth Deceleration:</b> ARR growth slowed from 32% (Q2 FY2025) to 22% (Q1 FY2026)",
        "<b>Reputational Risk:</b> July 2024 outage raised reliability questions (8.5M devices affected)",
        "<b>Margin Pressure:</b> Rising R&D and sales costs to maintain competitive position",
    ]
    for point in risk_points:
        story.append(Paragraph(f"• {point}", styles['CustomBody']))

    story.append(PageBreak())

    # ========================================
    # QUANTITATIVE ANALYSIS
    # ========================================
    story.append(Paragraph("Quantitative Analysis", styles['SectionHeading']))
    story.append(Paragraph("252-Day Risk Metrics (vs SPY Benchmark)", styles['SubsectionHeading']))

    risk_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['95% VaR (Daily)', '-4.11%', 'High downside risk'],
        ['95% CVaR (Daily)', '-5.87%', 'Tail risk elevated'],
        ['Sharpe Ratio', '0.66', 'Poor risk-adjusted returns'],
        ['Sortino Ratio', '1.11', 'Better downside-adjusted'],
        ['Max Drawdown', '-32.17%', 'Severe peak-to-trough decline'],
        ['Calmar Ratio', '1.10', 'Return/drawdown acceptable'],
        ['Annual Volatility', '46.35%', 'High volatility'],
        ['Beta (vs SPY)', '1.56', 'High systematic risk'],
        ['Alpha (vs SPY)', '+17.59%', 'Strong outperformance'],
    ]
    story.append(create_metric_table(risk_data, col_widths=[2.5*inch, 1.5*inch, 2*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Risk Assessment:</b> CRWD exhibits high volatility (46.35% annual) and significant drawdown risk (-32.17% max DD). "
        "However, the stock has delivered substantial alpha (+17.59%) despite a suboptimal Sharpe ratio (0.66). "
        "The 1.56 beta indicates amplified market sensitivity—expect 56% greater swings than SPY.",
        styles['CustomBody']
    ))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("90-Day Momentum Indicators", styles['SubsectionHeading']))

    momentum_data = [
        ['Indicator', 'Value', 'Signal'],
        ['RSI (14-day)', '32.67', 'Neutral'],
        ['MACD Line', '-7.49', 'Bearish'],
        ['MACD Signal', '-3.19', 'Bearish'],
        ['MACD Histogram', '-4.29', 'Negative momentum'],
        ['Stochastic %K', '0.31', 'Oversold'],
        ['Stochastic %D', '5.54', 'Oversold'],
        ['Williams %R', '-99.69', 'Oversold'],
        ['ROC (10-day)', '-6.77%', 'Bearish'],
        ['Momentum Confluence', '2 Bull / 2 Bear', 'MIXED'],
    ]
    story.append(create_metric_table(momentum_data, col_widths=[2.5*inch, 1.5*inch, 2*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Momentum Assessment:</b> CRWD is in a short-term corrective phase with oversold readings on Stochastic (0.31) "
        "and Williams %R (-99.69), suggesting potential reversal upward. However, MACD remains bearish with negative histogram, "
        "indicating downward momentum persists. RSI at 32.67 is neutral (not extreme). Mixed signals suggest waiting for "
        "confirmation before entry.",
        styles['CustomBody']
    ))

    story.append(PageBreak())

    story.append(Paragraph("90-Day Volatility Analysis", styles['SubsectionHeading']))

    volatility_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['Current Price', '$477.26', 'As of Dec 18, 2025'],
        ['Volatility Regime', 'NORMAL', 'Standard position sizing'],
        ['ATR (14-day)', '$17.09', '3.58% of price'],
        ['Suggested Stop Loss', '$34.18', '2× ATR'],
        ['Daily Volatility', '2.10%', 'Moderate intraday swings'],
        ['Annual Volatility', '33.36%', 'High volatility stock'],
        ['Bollinger Upper', '$534.01', '+11.9% from current'],
        ['Bollinger Middle', '$504.51', '+5.7% from current'],
        ['Bollinger Lower', '$475.01', '-0.5% from current'],
        ['%B Position', '0.038', 'Near lower band (support)'],
        ['Bandwidth', '11.69%', 'Moderate band width'],
    ]
    story.append(create_metric_table(volatility_data, col_widths=[2.5*inch, 1.5*inch, 2*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Volatility Assessment:</b> CRWD is trading near its lower Bollinger Band (%B = 0.038), suggesting the stock "
        "is approaching technical support. ATR of $17.09 (3.58%) indicates meaningful daily ranges—use 2× ATR ($34.18) "
        "for stop-loss placement. The NORMAL volatility regime supports standard 5-10% position sizing.",
        styles['CustomBody']
    ))

    story.append(PageBreak())

    # ========================================
    # MARKET SENTIMENT & CATALYSTS
    # ========================================
    story.append(Paragraph("Market Sentiment & 2026 Catalysts", styles['SectionHeading']))

    story.append(Paragraph("Wall Street Consensus", styles['SubsectionHeading']))
    analyst_data = [
        ['Metric', 'Value'],
        ['Consensus Rating', 'Moderate Buy'],
        ['Buy Ratings', '26'],
        ['Hold Ratings', '11'],
        ['Sell Ratings', '1'],
        ['Average Price Target', '$555.10 (range: $549-$563)'],
        ['Implied Upside', '+16.3% from $477.26'],
        ['High Target', '$706.00 (BTIG)'],
        ['Low Target', '$343.00'],
    ]
    story.append(create_metric_table(analyst_data))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph("Recent Price Target Increases (December 2025)", styles['SubsectionHeading']))
    target_updates = [
        "• Goldman Sachs: $535 → $564 (Buy)",
        "• Needham: $535 → $575 (Buy)",
        "• BTIG: $640 (Maintained Buy)",
        "• Citigroup: $595 (Buy)",
        "• Cantor Fitzgerald: $590 (Buy)",
        "• Susquehanna: $600 (Buy)",
        "• Scotiabank: $613 (Buy)",
        "• JPMorgan: $580 → $582 (Overweight)",
        "• BMO Capital: $500 → $555 (Outperform)",
        "• Morgan Stanley: $515 → $537 (Equal-Weight)",
    ]
    for update in target_updates:
        story.append(Paragraph(update, styles['CustomBody']))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("2026 Growth Catalysts", styles['SubsectionHeading']))

    catalysts = [
        "<b>Falcon Flex Acceleration:</b> Innovative licensing model enabling full platform consumption drove $1.35B ARR (3× YoY). "
        "200+ customers expanded contracts in Q3, with some increasing spend significantly. Facilitates consolidation of security "
        "point products onto unified Falcon platform.",

        "<b>AI Security Expansion:</b> Charlotte AI (generative AI assistant), Signal (weak signal correlation), and AI Systems "
        "Security Assessment position CRWD at the forefront of AI-driven security. Google Unified Security partnership and AWS "
        "collaborations could accelerate large-deal wins.",

        "<b>Platform Consolidation Trend:</b> Next-gen SIEM, identity security, and cloud protection now account for >33% of ARR "
        "(up from endpoint-only focus). Enterprise shift from 20+ security tools to unified platforms plays to CRWD's strength.",

        "<b>$10B ARR Target by FY2031:</b> Management reaffirmed goal representing 127% growth from current $4.4B ARR. Implies "
        "~15% CAGR over 6 years—achievable given $116B current TAM expanding to $250B by 2029.",

        "<b>Federal/Enterprise Contracts:</b> S&P 500 inclusion (June 2024) and Leader status in Gartner MQ/IDC MarketScape "
        "enhances credibility for large government/enterprise deals (though IRS contract under DOJ/SEC investigation).",

        "<b>Module Cross-Sell:</b> With 32 cloud modules, CRWD has vast land-and-expand opportunity. Average customer uses <10 modules, "
        "leaving significant upsell runway.",
    ]
    for catalyst in catalysts:
        story.append(Paragraph(f"• {catalyst}", styles['CustomBody']))
        story.append(Spacer(1, 0.08*inch))

    story.append(PageBreak())

    # ========================================
    # COMPETITIVE LANDSCAPE & RISKS
    # ========================================
    story.append(Paragraph("Competitive Landscape & Key Risks", styles['SectionHeading']))

    story.append(Paragraph("Competitive Positioning", styles['SubsectionHeading']))
    comp_data = [
        ['Company', 'Market Cap', 'FY Growth', 'Valuation (P/S)', 'Key Strength'],
        ['CRWD', '$113B', '29% YoY', '28.5×', 'Platform breadth + AI'],
        ['Palo Alto (PANW)', '$122B', '15%', '~18-20×', 'Enterprise suite + scale'],
        ['Fortinet (FTNT)', '$62B', '10-12%', '12-14×', 'Margin discipline (31.5%)'],
        ['SentinelOne', '$8B', '30%+', '10-12×', 'XDR innovation'],
        ['Microsoft', '$3T+', 'N/A', 'N/A', 'Bundling + enterprise lock-in'],
    ]
    story.append(create_metric_table(comp_data, col_widths=[1.3*inch, 1.2*inch, 1.1*inch, 1.2*inch, 1.8*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "CrowdStrike faces formidable competition from both platform consolidators (Palo Alto, Microsoft) and "
        "specialized players (Fortinet, SentinelOne, Zscaler). Microsoft's bundling strategy within Azure/M365 "
        "poses existential risk, while Palo Alto's balanced growth profile (15% revenue, 12.3% margin) and Fortinet's "
        "margin discipline (31.5% operating margin) highlight CRWD's premium valuation.",
        styles['CustomBody']
    ))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Key Risks to Monitor", styles['SubsectionHeading']))

    risks = [
        "<b>Valuation Compression Risk:</b> At 28.5× forward sales (vs fair value ~18.6×), CRWD requires sustained 20%+ ARR "
        "growth to justify premium. Any growth miss could trigger multiple contraction. Forward P/E of 59-120× (depending on "
        "estimate) vs PANW ~54× and FTNT ~36× shows significant downside risk.",

        "<b>Growth Deceleration:</b> ARR growth slowed from 32% (Q2 FY2025) to 22% (Q1 FY2026). If trend continues below 20%, "
        "premium valuation becomes untenable. Net new ARR of $194M (Q1 FY2026) must accelerate to hit $10B target by FY2031.",

        "<b>Microsoft Bundling Threat:</b> Microsoft Defender for Endpoint holds 11.82% market share and benefits from Azure/M365 "
        "ecosystem bundling. Enterprises may opt for 'good enough' bundled security over best-of-breed standalone solutions, "
        "pressuring CRWD's pricing power.",

        "<b>Margin Pressure:</b> Rising R&D and sales costs to compete with well-funded rivals (PANW, MSFT) could compress margins. "
        "CRWD must balance innovation investment with profitability expansion.",

        "<b>Reputational Overhang:</b> July 2024 outage (faulty update affected 8.5M devices globally) raised reliability questions. "
        "While long-term impact appears limited, any repeat incident could accelerate customer churn to competitors.",

        "<b>Regulatory Scrutiny:</b> DOJ/SEC investigation into $32M IRS deal with Carahsoft creates headline risk. Government "
        "contract exposure could face heightened compliance requirements.",

        "<b>Macro Headwinds:</b> Cybersecurity spending resilient but not recession-proof. Economic downturn could pressure IT budgets, "
        "slowing CRWD's enterprise expansion.",
    ]
    for risk in risks:
        story.append(Paragraph(f"• {risk}", styles['CustomBody']))
        story.append(Spacer(1, 0.08*inch))

    story.append(PageBreak())

    # ========================================
    # PORTFOLIO STRATEGY
    # ========================================
    story.append(Paragraph("Portfolio Strategy & Position Sizing", styles['SectionHeading']))

    story.append(Paragraph("Investment Recommendation", styles['SubsectionHeading']))
    story.append(Paragraph(
        "<b>Verdict: MODERATE BUY with Scaled Entry</b>",
        styles['MetricValue']
    ))
    story.append(Spacer(1, 0.1*inch))

    story.append(Paragraph(
        "CrowdStrike represents a high-conviction, long-term growth opportunity in cybersecurity platform consolidation, "
        "but current valuation and near-term momentum weakness warrant a measured approach. The stock's oversold technical "
        "condition (Stochastic %K = 0.31, Williams %R = -99.69) near Bollinger Band support suggests tactical entry opportunity, "
        "but MACD bearishness and ARR growth deceleration require risk management through scaled entry and defined stop-loss.",
        styles['CustomBody']
    ))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Position Sizing for $250,000 Portfolio", styles['SubsectionHeading']))

    # Position sizing table
    position_data = [
        ['Strategy', 'Allocation %', 'Dollar Amount', 'Shares', 'Rationale'],
        ['Conservative (3%)', '3%', '$7,500', '15-16', 'High valuation/volatility'],
        ['Standard (5%)', '5%', '$12,500', '26', 'Balanced risk/reward'],
        ['Aggressive (7%)', '7%', '$17,500', '36-37', 'High conviction + risk tolerance'],
        ['<b>RECOMMENDED</b>', '<b>5%</b>', '<b>$12,500</b>', '<b>26 shares</b>', '<b>Balanced approach</b>'],
    ]
    story.append(create_metric_table(position_data, col_widths=[1.5*inch, 1.1*inch, 1.2*inch, 0.9*inch, 1.8*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Recommendation:</b> Allocate <b>5% ($12,500 / 26 shares)</b> to CRWD using a scaled entry strategy. "
        "This balances the stock's high-growth potential against elevated volatility (46.35% annual) and valuation risk (28× P/S). "
        "Conservative investors with lower risk tolerance should reduce to 3%, while aggressive growth portfolios with high risk "
        "tolerance can scale to 7%.",
        styles['CustomBody']
    ))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Entry Strategy: Scaled Approach", styles['SubsectionHeading']))

    entry_strategy = [
        "<b>Tranche 1 (40% / $5,000 / 10 shares):</b> Initiate position at current levels ($477) given oversold technicals "
        "(Stochastic, Williams %R) and proximity to Bollinger lower band support. Establishes core position.",

        "<b>Tranche 2 (30% / $3,750 / 8 shares):</b> Add on MACD bullish crossover OR bounce from $470 support level. "
        "Confirms momentum reversal and reduces average cost if initial entry sees further weakness.",

        "<b>Tranche 3 (30% / $3,750 / 8 shares):</b> Complete position on breakout above $510 (Bollinger middle band) OR "
        "strong quarterly earnings beat with ARR acceleration. Validates uptrend resumption.",

        "<b>Alternative - Immediate Full Position:</b> If high conviction and willing to accept near-term volatility, deploy "
        "full $12,500 (26 shares) immediately at $477. Sets tight stop-loss at $443 (2× ATR = $34.18 below entry) to limit "
        "downside to ~7% portfolio impact.",
    ]
    for strategy in entry_strategy:
        story.append(Paragraph(f"• {strategy}", styles['CustomBody']))
        story.append(Spacer(1, 0.08*inch))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Risk Management Parameters", styles['SubsectionHeading']))

    risk_mgmt = [
        ['Parameter', 'Value', 'Rationale'],
        ['Stop-Loss', '$443 (-7.1%)', '2× ATR ($34.18) below $477 entry'],
        ['Portfolio Risk', '$875 (0.35%)', 'Acceptable risk per position'],
        ['Take-Profit 1', '$555 (+16.3%)', 'Wall Street consensus target'],
        ['Take-Profit 2', '$590-$640 (+23-34%)', 'Bullish analyst targets (BTIG, Citigroup)'],
        ['Trailing Stop', '15% after +25% gain', 'Lock in profits, let winners run'],
        ['Rebalance Trigger', '>10% portfolio weight', 'Trim on outsized appreciation'],
    ]
    story.append(create_metric_table(risk_mgmt, col_widths=[2*inch, 1.8*inch, 2.7*inch]))
    story.append(Spacer(1, 0.15*inch))

    story.append(Paragraph(
        "<b>Stop-Loss Discipline:</b> Rigidly adhere to $443 stop-loss (2× ATR). CRWD's high beta (1.56) means market downturns "
        "will be amplified 56%—preserving capital is paramount. If stopped out, reassess entry on improved technicals or valuation.",
        styles['CustomBody']
    ))

    story.append(PageBreak())

    # ========================================
    # MONITORING & MILESTONES
    # ========================================
    story.append(Paragraph("Monitoring Plan & Key Milestones", styles['SectionHeading']))

    story.append(Paragraph("Quarterly Earnings Checkpoints", styles['SubsectionHeading']))
    earnings_points = [
        "• <b>ARR Growth Rate:</b> Must maintain 20%+ to justify premium valuation. Watch for reacceleration toward 25-30% range.",
        "• <b>Falcon Flex ARR:</b> Track progression from $1.35B—target 50%+ YoY growth as model scales.",
        "• <b>Net Retention Rate:</b> Monitor for stability >120%. Declining NRR signals churn or upsell headwinds.",
        "• <b>Free Cash Flow Margin:</b> Sustain 25-30% FCF margin. Compression below 20% indicates margin pressure from competition.",
        "• <b>Module Adoption:</b> Track average modules per customer. Expansion from current <10 modules validates platform strategy.",
        "• <b>Large Deal Activity:</b> Watch for $1M+ ACV deals. Acceleration signals enterprise platform consolidation traction.",
    ]
    for point in earnings_points:
        story.append(Paragraph(point, styles['CustomBody']))

    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("Market/Competitive Signals", styles['SubsectionHeading']))
    market_signals = [
        "• <b>Microsoft Competition:</b> Track Microsoft Defender market share. Gains >15% could pressure CRWD pricing/growth.",
        "• <b>Palo Alto Convergence:</b> Monitor PANW platform bundle deals. Successful large enterprise wins indicate competitive threat.",
        "• <b>Valuation Multiple:</b> Watch for P/S multiple compression below 24×. Signals market reassessing growth premium.",
        "• <b>Analyst Downgrades:</b> >3 downgrades within single quarter warrants position review. Consensus shifts matter.",
        "• <b>Cybersecurity M&A:</b> Track PANW/MSFT acquisitions of startups. Could accelerate competitive feature parity.",
    ]
    for signal in market_signals:
        story.append(Paragraph(signal, styles['CustomBody']))

    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("Exit Criteria (Sell Signals)", styles['SubsectionHeading']))
    exit_criteria = [
        "• <b>ARR Growth Falls Below 15%:</b> Two consecutive quarters <15% ARR growth invalidates $10B FY2031 target.",
        "• <b>Major Customer Loss:</b> Loss of Fortune 100 anchor client to PANW/MSFT signals platform weakness.",
        "• <b>FCF Margin Compression:</b> FCF margin falls below 15% for two straight quarters.",
        "• <b>Second Major Outage:</b> Repeat of July 2024 incident magnitude triggers immediate exit (reliability imperative).",
        "• <b>Valuation Disconnect:</b> If stock reaches $640+ (34% upside) while ARR growth decelerates, take profits and rotate.",
        "• <b>Better Opportunity:</b> If superior risk/reward emerges in cybersecurity (e.g., FTNT at <20× P/S with 20%+ growth).",
    ]
    for criterion in exit_criteria:
        story.append(Paragraph(criterion, styles['CustomBody']))

    story.append(PageBreak())

    # ========================================
    # FINAL VERDICT & ACTION ITEMS
    # ========================================
    story.append(Paragraph("Final Verdict & Action Plan", styles['SectionHeading']))

    story.append(Paragraph("Investment Summary", styles['SubsectionHeading']))
    summary_data = [
        ['Rating', 'MODERATE BUY'],
        ['Conviction', 'MEDIUM (6/10)'],
        ['Risk Level', 'HIGH'],
        ['Time Horizon', '12-24 months'],
        ['Position Size', '5% portfolio ($12,500 / 26 shares)'],
        ['Entry Strategy', 'Scaled: 40% now, 30% on reversal, 30% on breakout'],
        ['Stop-Loss', '$443 (-7.1% from $477)'],
        ['Price Target (12mo)', '$555 (+16.3%)'],
        ['Upside Case', '$640 (+34%) if ARR accelerates + multiple expansion'],
        ['Downside Case', '$400 (-16%) if growth decelerates + multiple compression'],
    ]
    story.append(create_metric_table(summary_data, col_widths=[2.5*inch, 3.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("Why MODERATE BUY vs STRONG BUY?", styles['SubsectionHeading']))
    story.append(Paragraph(
        "While CrowdStrike possesses elite competitive positioning (#1 market share, platform breadth, AI integration) "
        "and credible long-term growth visibility ($10B ARR by FY2031), several factors prevent a STRONG BUY rating:",
        styles['CustomBody']
    ))
    story.append(Spacer(1, 0.1*inch))

    moderate_reasons = [
        "• <b>Valuation Premium:</b> 28.5× forward sales vs 18.6× fair value requires perfect execution—minimal margin for error",
        "• <b>ARR Deceleration:</b> 22% growth (Q1 FY2026) down from 32% (Q2 FY2025)—trend must reverse",
        "• <b>Competitive Intensification:</b> Microsoft bundling + Palo Alto/Fortinet AI investments narrowing differentiation",
        "• <b>Technical Weakness:</b> MACD bearish, ROC negative—momentum not yet confirmed as reversed",
        "• <b>Reputational Overhang:</b> July 2024 outage creates binary risk of repeat incident destroying trust",
    ]
    for reason in moderate_reasons:
        story.append(Paragraph(reason, styles['CustomBody']))

    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(
        "A STRONG BUY would require: (1) ARR reacceleration to 25%+, (2) valuation pullback to 20-22× P/S, "
        "(3) confirmed MACD bullish crossover, and (4) major platform win vs MSFT/PANW demonstrating durable moat.",
        styles['CustomBody']
    ))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Action Items - Next 30 Days", styles['SubsectionHeading']))

    action_items = [
        "<b>Week 1:</b> Initiate Tranche 1 (40% / $5,000 / 10 shares) at current levels (~$477). Set stop-loss at $443.",

        "<b>Week 2-3:</b> Monitor for MACD bullish crossover or bounce from $470 support. If confirmed, deploy Tranche 2 "
        "(30% / $3,750 / 8 shares). If breakdown below $470, hold Tranche 2 cash and reassess.",

        "<b>Week 4:</b> Review Q4 FY2026 earnings (late Feb 2026 expected). Key metrics: ARR growth, Falcon Flex ARR, "
        "FCF margin, FY2027 guidance. If ARR >22% and guidance strong, deploy Tranche 3 (30% / $3,750 / 8 shares).",

        "<b>Ongoing:</b> Set calendar reminders for quarterly earnings, track analyst rating changes weekly, monitor PANW/MSFT "
        "competitive announcements. Review position if stop-loss triggered or exit criteria met.",
    ]
    for item in action_items:
        story.append(Paragraph(f"• {item}", styles['CustomBody']))
        story.append(Spacer(1, 0.08*inch))

    story.append(PageBreak())

    # ========================================
    # APPENDIX: RESEARCH SOURCES
    # ========================================
    story.append(Paragraph("Appendix: Research Sources & Citations", styles['SectionHeading']))

    story.append(Paragraph("Quantitative Data Sources", styles['SubsectionHeading']))
    quant_sources = [
        "• Yahoo Finance (yfinance API): Daily OHLCV data, 252-day and 90-day historical prices",
        "• Finnhub Market Data: Real-time pricing ($477.26 as of Dec 18, 2025)",
        "• Finance Guru CLI Tools: risk_metrics_cli.py, momentum_cli.py, volatility_cli.py",
    ]
    for source in quant_sources:
        story.append(Paragraph(source, styles['CustomBody']))

    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("Market Research Sources (December 2025)", styles['SubsectionHeading']))

    sources = [
        "• Yahoo Finance - CrowdStrike Holdings (CRWD) Stock Data",
        "• DCFmodeling.com - CRWD Financial Health & Mission Statement",
        "• Nasdaq - \"3 Reasons CrowdStrike Is a Long-Term Buy for 2030 and Beyond\"",
        "• IndexBox - Cybersecurity Market Growth 2025-2032 & CrowdStrike's Performance",
        "• BNN Bloomberg - \"CrowdStrike revenue climbs on expanding cybersecurity demand\"",
        "• 6sense - CrowdStrike Market Share in Endpoint Protection",
        "• Statista - CrowdStrike Statistics & Facts",
        "• SiliconANGLE - \"From product to platform: How CrowdStrike navigates to durable growth\"",
        "• TS2 Space - CRWD Stock Forecast and Analyst Targets (Multiple Articles)",
        "• GuruFocus - Analyst Ratings & Price Targets",
        "• Sahm Capital - \"CrowdStrike Is Up 8.8% After Surge in Contract Renewals\"",
        "• Simply Wall St - CRWD Financial Analysis",
        "• MarketBeat - CRWD Stock Forecast & Price Target 2025",
        "• TipRanks - CRWD Stock Forecast and Analysts Predictions",
        "• Benzinga - CrowdStrike Analyst Ratings & Price Predictions",
        "• StockAnalysis - CRWD Stock Forecast & Price Targets",
        "• AInvest.com - \"Navigating the Evolving Cybersecurity Landscape\" (Valuation Analysis)",
        "• Finimize - \"CrowdStrike's Growth Engine Faces A New Speed Limit\"",
        "• The Motley Fool - \"Can CrowdStrike Stock Keep Moving Higher in 2025?\"",
        "• TradingView/Zacks - Industry Outlook (PANW, CRWD, FTNT, QLYS)",
    ]
    for source in sources:
        story.append(Paragraph(source, styles['CustomBody']))

    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Analyst Firms Cited", styles['SubsectionHeading']))
    analysts = [
        "Goldman Sachs", "Needham", "BTIG", "Citigroup", "Cantor Fitzgerald",
        "Susquehanna", "Scotiabank", "JPMorgan", "BMO Capital Markets", "Morgan Stanley",
        "Rosenblatt Securities", "Gartner (Magic Quadrant)", "IDC (MarketScape)"
    ]
    analyst_text = ", ".join(analysts)
    story.append(Paragraph(analyst_text, styles['CustomBody']))

    story.append(PageBreak())

    # ========================================
    # DISCLAIMER
    # ========================================
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("IMPORTANT DISCLAIMERS", styles['SectionHeading']))
    story.append(Spacer(1, 0.2*inch))

    disclaimer_text = [
        "<b>Educational Purpose Only:</b> This report is generated by Finance Guru™, a private AI-powered family office "
        "system, for educational and informational purposes only. It does not constitute investment advice, financial advice, "
        "trading advice, or any other type of professional advice.",

        "<b>Not Investment Advice:</b> The analysis, recommendations, and opinions expressed herein are based on publicly "
        "available information and quantitative models as of December 18, 2025. They reflect the views of the Finance Guru "
        "multi-agent system and do not represent personalized investment recommendations for any individual investor.",

        "<b>Consult Professionals:</b> Before making any investment decisions, you should consult with qualified financial "
        "advisors, tax professionals, and legal counsel who understand your specific financial situation, risk tolerance, "
        "investment objectives, and time horizon.",

        "<b>Risk Disclosure:</b> Investing in securities involves substantial risk of loss. CrowdStrike Holdings (CRWD) is "
        "a high-volatility stock (46.35% annual volatility) with significant drawdown risk (-32.17% max drawdown). Past "
        "performance is not indicative of future results. You may lose some or all of your invested capital.",

        "<b>No Guarantees:</b> There is no guarantee that CRWD will achieve the price targets, revenue projections, or ARR "
        "growth rates mentioned in this report. Market conditions, competitive dynamics, regulatory changes, and macroeconomic "
        "factors can materially impact outcomes.",

        "<b>Data Accuracy:</b> While Finance Guru strives for accuracy, data is provided 'as is' without warranties. Users "
        "should independently verify all information before making investment decisions.",

        "<b>Conflicts of Interest:</b> The author/portfolio may hold positions in CRWD or competing securities. This report "
        "is for the author's private use and does not constitute a recommendation to buy or sell securities.",
    ]

    for disclaimer in disclaimer_text:
        story.append(Paragraph(disclaimer, styles['CustomBody']))
        story.append(Spacer(1, 0.1*inch))

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        "© 2025 Finance Guru™ - Private Family Office Analysis System | "
        "Powered by BMAD-CORE™ v6.0.0 | "
        "Generated: December 18, 2025",
        styles['Disclaimer']
    ))

    # Build PDF
    doc.build(story, onFirstPage=create_header_footer, onLaterPages=create_header_footer)
    print(f"\n✅ Report generated successfully: {output_file}\n")
    return output_file

if __name__ == "__main__":
    generate_crwd_report()
