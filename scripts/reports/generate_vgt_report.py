#!/usr/bin/env python3
"""
VGT Analysis Report Generator
Finance Guru™ - Family Office Analysis
Date: 2025-12-18

Generates a comprehensive PDF report for VGT (Vanguard Information Technology ETF)
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
import os

# Finance Guru Branding Colors
NAVY = colors.HexColor('#1a365d')
GOLD = colors.HexColor('#d69e2e')
GREEN = colors.HexColor('#38a169')
RED = colors.HexColor('#e53e3e')
LIGHT_GRAY = colors.HexColor('#f7fafc')
DARK_GRAY = colors.HexColor('#2d3748')

def create_header_style():
    """Create custom header styles"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=NAVY,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=NAVY,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='SubHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=NAVY,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name='Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Oblique'
    ))

    return styles

def create_metric_table(data, col_widths=None):
    """Create a styled table for metrics"""
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_GRAY),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
    ]))
    return table

def generate_vgt_report():
    """Generate comprehensive VGT analysis PDF report"""

    # Setup document
    output_dir = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{output_dir}/VGT-Analysis-2025-12-18.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)

    # Container for the 'Flowable' objects
    elements = []
    styles = create_header_style()

    # =================================================================
    # TITLE PAGE
    # =================================================================
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("FINANCE GURU™", styles['CustomTitle']))
    elements.append(Paragraph("Family Office Investment Analysis",
                             ParagraphStyle('subtitle', parent=styles['CustomBody'],
                                          fontSize=14, textColor=GOLD, alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.3*inch))

    # Divider
    elements.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceBefore=10, spaceAfter=10))

    # Report Title
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("VGT - Vanguard Information Technology ETF",
                             ParagraphStyle('report_title', parent=styles['CustomTitle'], fontSize=20)))
    elements.append(Paragraph("2026 Watchlist Analysis & Investment Recommendation",
                             ParagraphStyle('report_subtitle', parent=styles['CustomBody'],
                                          fontSize=12, alignment=TA_CENTER, textColor=DARK_GRAY)))

    elements.append(Spacer(1, 0.5*inch))

    # Key Info Box
    key_info_data = [
        ['Report Date:', '2025-12-18'],
        ['Analyst Team:', 'Dr. Aleksandr Petrov (Market Research)\nDr. Priya Desai (Quantitative Analysis)\nElena Rodriguez-Park (Strategy)'],
        ['Current Price:', '$740.62'],
        ['YTD Performance:', '+22.7%'],
        ['Expense Ratio:', '0.10%'],
    ]

    key_info_table = create_metric_table(key_info_data, col_widths=[2*inch, 4*inch])
    elements.append(key_info_table)

    elements.append(Spacer(1, 0.3*inch))

    # Executive Summary Rating Box
    rating_data = [
        ['INVESTMENT RATING', 'CONDITIONAL BUY'],
        ['Risk Level', 'MEDIUM-HIGH'],
        ['Conviction', '7/10'],
    ]
    rating_table = Table(rating_data, colWidths=[3*inch, 3*inch])
    rating_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1.5, NAVY),
    ]))
    elements.append(rating_table)

    elements.append(PageBreak())

    # =================================================================
    # EXECUTIVE SUMMARY
    # =================================================================
    elements.append(Paragraph("Executive Summary", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    exec_summary = """
    VGT (Vanguard Information Technology ETF) presents a <b>CONDITIONAL BUY</b> opportunity for 2026,
    offering concentrated exposure to the technology sector's AI-driven growth cycle. With NVIDIA (18.19%),
    Apple (14.29%), and Microsoft (12.93%) comprising 45% of holdings, VGT provides leveraged exposure
    to mega-cap tech innovation at a best-in-class 0.10% expense ratio.
    <br/><br/>
    <b>Key Investment Thesis:</b>
    <br/>• Positioned at the epicenter of the "giga cycle" - semiconductor industry's AI-driven expansion to $1 trillion+ by 2030
    <br/>• Top-tier portfolio construction with 59.96% in top 10 holdings, emphasizing quality over diversification
    <br/>• Strong YTD performance (+22.7%) with 22.18% annualized returns over the past decade
    <br/>• Low-cost access (0.10% ER) to AI infrastructure, semiconductors, and enterprise software mega-trends
    <br/><br/>
    <b>Primary Concerns:</b>
    <br/>• Extreme correlation with existing portfolio (0.943 with VOO, 0.864 with NVDA) - adds minimal diversification
    <br/>• High beta (1.35) amplifies downside risk in market corrections
    <br/>• Currently in consolidation phase with mixed momentum signals (RSI: 37.39, oversold stochastic)
    <br/>• Valuation risk: Tech sector trading at historically elevated multiples with limited expansion room
    """

    elements.append(Paragraph(exec_summary, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # =================================================================
    # FUND OVERVIEW & HOLDINGS
    # =================================================================
    elements.append(Paragraph("Fund Overview & Holdings Breakdown", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    fund_overview = """
    VGT tracks the MSCI US Investable Market Information Technology 25/50 Index, providing exposure to
    317 U.S. technology companies across software, hardware, semiconductors, and IT services. The fund's
    concentrated approach (top 5 = 51.98% of assets) reflects the winner-take-most dynamics of the tech sector.
    """
    elements.append(Paragraph(fund_overview, styles['CustomBody']))
    elements.append(Spacer(1, 0.15*inch))

    # Top Holdings Table
    elements.append(Paragraph("Top 10 Holdings (59.96% of Fund)", styles['SubHeader']))
    holdings_data = [
        ['Ticker', 'Company', 'Weight', 'Segment'],
        ['NVDA', 'NVIDIA Corporation', '18.19%', 'AI/Semiconductors'],
        ['AAPL', 'Apple Inc.', '14.29%', 'Consumer Hardware'],
        ['MSFT', 'Microsoft Corporation', '12.93%', 'Enterprise Software/Cloud'],
        ['AVGO', 'Broadcom Inc.', '4.48%', 'Semiconductors'],
        ['PLTR', 'Palantir Technologies', '2.09%', 'AI/Analytics Software'],
        ['ORCL', 'Oracle Corporation', '2.05%', 'Enterprise Software'],
        ['AMD', 'Advanced Micro Devices', '1.97%', 'Semiconductors'],
        ['CSCO', 'Cisco Systems', '~1.5%', 'Networking Equipment'],
        ['CRM', 'Salesforce', '~1.5%', 'Cloud CRM'],
        ['ADBE', 'Adobe Inc.', '~1.0%', 'Creative Software'],
    ]
    holdings_table = create_metric_table(holdings_data, col_widths=[0.8*inch, 2.2*inch, 1*inch, 2*inch])
    elements.append(holdings_table)
    elements.append(Spacer(1, 0.15*inch))

    # Sector Allocation
    elements.append(Paragraph("Sector Allocation", styles['SubHeader']))
    sector_text = """
    <b>Technology Exposure:</b> 99.2% | <b>Geographic Focus:</b> 99.1% United States
    <br/><br/>
    <b>Sub-sector Breakdown:</b>
    <br/>• AI Infrastructure & Semiconductors: ~27% (NVDA, AMD, AVGO)
    <br/>• Enterprise Software & Cloud: ~20% (MSFT, ORCL, CRM, ADBE)
    <br/>• Consumer Technology: ~14% (AAPL)
    <br/>• IT Services & Consulting: ~15%
    <br/>• Hardware & Networking: ~13% (CSCO, HPQ)
    <br/>• Emerging Tech & Analytics: ~11% (PLTR, AI-focused names)
    """
    elements.append(Paragraph(sector_text, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # PHASE 2: QUANTITATIVE ANALYSIS
    # =================================================================
    elements.append(Paragraph("Quantitative Risk Analysis", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    quant_intro = """
    Dr. Priya Desai's quantitative analysis (252-day lookback vs. SPY benchmark) reveals VGT as a
    high-beta, medium-volatility growth vehicle with solid alpha generation but elevated downside risk.
    """
    elements.append(Paragraph(quant_intro, styles['CustomBody']))
    elements.append(Spacer(1, 0.15*inch))

    # Risk Metrics Table
    elements.append(Paragraph("Risk Metrics (252-Day Analysis vs. SPY)", styles['SubHeader']))
    risk_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['95% VaR (Daily)', '-2.83%', '95% of days, losses won\'t exceed 2.83%'],
        ['95% CVaR (Daily)', '-4.20%', 'When VaR is breached, average loss is 4.20%'],
        ['Sharpe Ratio', '0.45', 'POOR - Below 1.0 threshold for risk-adjusted returns'],
        ['Sortino Ratio', '0.59', 'Focuses on downside risk - acceptable for growth'],
        ['Maximum Drawdown', '-27.23%', 'Worst peak-to-trough decline (significant)'],
        ['Calmar Ratio', '0.63', 'Return/Max DD - moderate risk compensation'],
        ['Annual Volatility', '28.09%', 'MEDIUM volatility (20-40% range)'],
        ['Beta vs. SPY', '1.35', 'HIGH - 35% more volatile than S&P 500'],
        ['Alpha vs. SPY', '+1.23%', 'Outperforming benchmark by 1.23% annually'],
    ]
    risk_table = create_metric_table(risk_data, col_widths=[1.8*inch, 1.2*inch, 3*inch])
    elements.append(risk_table)
    elements.append(Spacer(1, 0.2*inch))

    # Momentum Analysis
    elements.append(Paragraph("Momentum Analysis (90-Day Window)", styles['SubHeader']))
    momentum_data = [
        ['Indicator', 'Current Value', 'Signal', 'Interpretation'],
        ['RSI', '37.39', 'Neutral', 'Below 50 but not oversold - bearish lean'],
        ['MACD', '-1.64 (below signal)', 'Bearish', 'MACD below signal line - downward momentum'],
        ['Stochastic %K', '0.47', 'Oversold', 'Extreme oversold - potential reversal setup'],
        ['Williams %R', '-99.53', 'Oversold', 'Deep oversold territory - reversal likely'],
        ['Rate of Change', '-2.76%', 'Bearish', 'Negative momentum over lookback period'],
        ['Confluence', '2/5 Bullish, 2/5 Bearish', 'MIXED', 'No clear directional consensus'],
    ]
    momentum_table = create_metric_table(momentum_data, col_widths=[1.3*inch, 1.5*inch, 1*inch, 2.2*inch])
    elements.append(momentum_table)
    elements.append(Spacer(1, 0.2*inch))

    # Volatility Analysis
    elements.append(Paragraph("Volatility Regime & Position Sizing", styles['SubHeader']))
    volatility_data = [
        ['Metric', 'Value', 'Guidance'],
        ['Volatility Regime', 'LOW', 'Can use larger positions (10-20% of portfolio)'],
        ['ATR (14-day)', '$14.40 (1.94%)', 'Suggested stop loss: 2× ATR = $28.80'],
        ['Bollinger %B', '0.355', 'Price in lower half of bands - below midpoint'],
        ['Bollinger Bandwidth', '9.80%', 'NARROW - "squeeze" setup for potential breakout'],
        ['Annual Volatility', '21.80%', 'Slightly below 252-day vol (28.09%) - calming period'],
    ]
    volatility_table = create_metric_table(volatility_data, col_widths=[2*inch, 1.8*inch, 2.2*inch])
    elements.append(volatility_table)

    elements.append(PageBreak())

    # =================================================================
    # CORRELATION & PORTFOLIO FIT
    # =================================================================
    elements.append(Paragraph("Correlation Analysis & Portfolio Fit", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    correlation_intro = """
    <b>CRITICAL FINDING:</b> VGT exhibits extreme correlation with existing portfolio holdings,
    particularly VOO (0.943) and NVDA (0.864). This severely limits diversification benefits.
    <br/><br/>
    <b>Diversification Score:</b> 🟡 0.321 (MODERATE) | <b>Average Correlation:</b> 0.679 (HIGH)
    """
    elements.append(Paragraph(correlation_intro, styles['CustomBody']))
    elements.append(Spacer(1, 0.15*inch))

    # Correlation Matrix
    corr_data = [
        ['Asset Pair', 'Correlation', 'Classification', 'Implication'],
        ['VGT / VOO', '+0.943', 'VERY HIGH', 'Almost redundant - VGT tracks S&P 500 tech closely'],
        ['VGT / NVDA', '+0.864', 'VERY HIGH', 'NVDA is 18% of VGT - extreme overlap'],
        ['VGT / TSLA', '+0.662', 'HIGH', 'Moderate overlap - both growth-oriented'],
        ['VGT / PLTR', '+0.659', 'HIGH', 'PLTR is in VGT (2.09%) - direct overlap'],
        ['NVDA / VOO', '+0.730', 'VERY HIGH', 'NVDA dominates S&P 500 tech weighting'],
    ]
    corr_table = create_metric_table(corr_data, col_widths=[1.5*inch, 1*inch, 1.2*inch, 2.3*inch])
    elements.append(corr_table)
    elements.append(Spacer(1, 0.15*inch))

    portfolio_impact = """
    <b>Portfolio Construction Concern:</b>
    <br/>
    Adding VGT to a portfolio already containing VOO, NVDA, PLTR, and TSLA creates significant
    concentration risk in U.S. mega-cap technology. The 0.943 correlation with VOO means VGT
    provides minimal additional alpha potential while amplifying sector-specific downside risk.
    <br/><br/>
    <b>Recommendation:</b> If adding VGT, reduce VOO allocation proportionally to maintain target
    risk levels. Alternatively, use VGT as a <i>replacement</i> for direct tech stock holdings
    rather than a supplement.
    """
    elements.append(Paragraph(portfolio_impact, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # 2026 CATALYSTS & OUTLOOK
    # =================================================================
    elements.append(Paragraph("2026 Market Catalysts & Growth Drivers", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    catalysts_intro = """
    The semiconductor and technology sectors are entering an unprecedented "giga cycle" driven by
    AI infrastructure buildout, with forecasts pointing to a $1 trillion+ market before 2030.
    """
    elements.append(Paragraph(catalysts_intro, styles['CustomBody']))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph("Primary Growth Catalysts", styles['SubHeader']))
    catalysts_list = """
    <b>1. AI Infrastructure Expansion</b>
    <br/>• Semiconductor sales projected to spike 26% in 2026 to $975 billion (WSTS forecast)
    <br/>• AI-specific chip sales exceeding $150 billion in 2025, accelerating into 2026
    <br/>• NVIDIA's $3-4 trillion AI infrastructure opportunity over next 5 years
    <br/>• HBM (High-Bandwidth Memory) revenue growing from $16B (2024) to $100B+ by 2030
    <br/><br/>
    <b>2. Semiconductor Supply-Demand Dynamics</b>
    <br/>• TSMC production capacity through 2026 largely pre-booked by NVDA and AAPL
    <br/>• Memory segment (DRAM, HBM) facing "perfect storm" of constrained supply + surging demand
    <br/>• AMD targeting 60% CAGR for data center business, 35% overall
    <br/>• NVIDIA's Blackwell GPU family driving next upgrade cycle
    <br/><br/>
    <b>3. Enterprise AI Adoption</b>
    <br/>• Microsoft Azure AI services penetrating enterprise customer base
    <br/>• Oracle Cloud Infrastructure (OCI) winning AI workload migrations
    <br/>• Palantir's AIP (Artificial Intelligence Platform) scaling across Fortune 500
    <br/>• Apple Intelligence features driving iPhone upgrade cycle
    <br/><br/>
    <b>4. Post-Election Year Dynamics</b>
    <br/>• Historical pattern: VGT outperforms in year following U.S. Presidential elections
    <br/>• Price target: ~$800 by end of 2025, $830+ average for 2026
    <br/>• 5-year revenue projection: +75% ($100 → $175 by 2030)
    """
    elements.append(Paragraph(catalysts_list, styles['CustomBody']))

    elements.append(Spacer(1, 0.15*inch))

    # Price Forecast Table
    elements.append(Paragraph("Analyst Price Forecasts", styles['SubHeader']))
    forecast_data = [
        ['Timeframe', 'Low', 'Average', 'High', 'Implied Return'],
        ['2025 Year-End', '$765.51', '$774.62', '$783.74', '+2.94% from current'],
        ['2026 Year-End', '$797.84', '$829.15', '$842.90', '+10.18% from current'],
        ['2030 (Long-term)', 'N/A', '$1,252.87', 'N/A', '+69% from current'],
    ]
    forecast_table = create_metric_table(forecast_data, col_widths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.5*inch])
    elements.append(forecast_table)

    elements.append(PageBreak())

    # =================================================================
    # RISK FACTORS & CONCERNS
    # =================================================================
    elements.append(Paragraph("Risk Factors & Investment Concerns", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    risks_content = """
    <b>1. Valuation Risk (CRITICAL)</b>
    <br/>• Tech sector trading at historically elevated multiples with limited room for expansion
    <br/>• Mean reversion risk if AI hype cycle moderates or monetization disappoints
    <br/>• Top holdings (NVDA, AAPL, MSFT) account for 45% - concentrated valuation dependency
    <br/><br/>
    <b>2. Sector Concentration</b>
    <br/>• 99.2% technology allocation = zero sector diversification
    <br/>• Higher volatility than broad market (28.09% annual vol vs. ~18% for SPY)
    <br/>• Max drawdown of -27.23% demonstrates downside severity in corrections
    <br/><br/>
    <b>3. Momentum Deterioration</b>
    <br/>• Current technical setup shows mixed signals with bearish lean
    <br/>• MACD bearish, RSI neutral at 37.39, recent -2.76% rate of change
    <br/>• May require patience/volatility before resuming uptrend
    <br/><br/>
    <b>4. Portfolio Overlap (YOUR SPECIFIC CONCERN)</b>
    <br/>• 0.943 correlation with VOO means 89% shared variance
    <br/>• Direct holdings overlap: NVDA (18% of VGT), PLTR (2% of VGT)
    <br/>• Adding VGT increases portfolio beta without diversification benefit
    <br/><br/>
    <b>5. Regulatory & Geopolitical Risks</b>
    <br/>• Antitrust scrutiny of mega-cap tech (AAPL, MSFT, GOOG)
    <br/>• Export controls on advanced semiconductors (China relations)
    <br/>• AI safety regulation could slow deployment timelines
    <br/><br/>
    <b>6. Competition & Disruption</b>
    <br/>• VGT methodology excludes Amazon (AMZN) and Google (GOOG) - structural handicap
    <br/>• Rapid innovation cycles create winner-take-most but also displacement risk
    <br/>• Open-source AI models could commoditize infrastructure layer
    """
    elements.append(Paragraph(risks_content, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # STRATEGY RECOMMENDATION
    # =================================================================
    elements.append(Paragraph("Investment Strategy & Recommendation", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    strategy_intro = """
    <b>Analyst: Elena Rodriguez-Park, CFA - Head of Strategy</b>
    <br/><br/>
    Based on comprehensive market research, quantitative analysis, and portfolio fit evaluation,
    VGT merits a <b>CONDITIONAL BUY</b> rating with specific implementation guidelines.
    """
    elements.append(Paragraph(strategy_intro, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # Investment Thesis Table
    elements.append(Paragraph("Investment Thesis Summary", styles['SubHeader']))
    thesis_data = [
        ['Category', 'Rating', 'Rationale'],
        ['Growth Potential', '9/10', 'AI giga cycle, semiconductor supercycle, strong 2026 catalysts'],
        ['Quality', '8/10', 'Top-tier holdings, NVDA/MSFT/AAPL dominance, low 0.10% ER'],
        ['Valuation', '4/10', 'Tech valuations extended, limited multiple expansion room'],
        ['Risk/Reward', '6/10', 'High beta (1.35), but alpha generation (+1.23%) compensates'],
        ['Portfolio Fit', '3/10', 'Extreme correlation (0.943 VOO, 0.864 NVDA) limits value-add'],
        ['Technical Setup', '5/10', 'Mixed momentum, oversold signals but no clear trend'],
        ['<b>OVERALL</b>', '<b>7/10</b>', '<b>Strong fundamentals, but portfolio overlap reduces appeal</b>'],
    ]
    thesis_table = create_metric_table(thesis_data, col_widths=[1.5*inch, 1*inch, 3.5*inch])
    elements.append(thesis_table)
    elements.append(Spacer(1, 0.2*inch))

    # Position Sizing Recommendations
    elements.append(Paragraph("Position Sizing & Entry Strategy", styles['SubHeader']))
    position_sizing = """
    <b>Recommended Allocation:</b>
    <br/>• <b>Conservative Approach:</b> 5-8% of portfolio (if keeping VOO + individual tech stocks)
    <br/>• <b>Substitution Approach:</b> 15-20% of portfolio (replace direct NVDA/PLTR holdings with VGT)
    <br/>• <b>Aggressive Approach:</b> 12-15% of portfolio (accept higher correlation, maximize tech exposure)
    <br/><br/>
    <b>Entry Strategy:</b>
    <br/>1. <b>Immediate Partial Entry:</b> Deploy 40% of intended allocation at current levels ($740-$750)
    <br/>   • Justification: Oversold stochastic/Williams %R suggest near-term bounce potential
    <br/>   • Bollinger squeeze setup indicates consolidation before next move
    <br/><br/>
    2. <b>Scale-In on Weakness:</b> Add 30% if VGT pulls back to $710-$720 (lower Bollinger Band)
    <br/>   • This represents ~4% downside from current - reasonable risk/reward
    <br/>   • Would lower average cost basis and improve entry point
    <br/><br/>
    3. <b>Final Tranche on Confirmation:</b> Add remaining 30% on breakout above $780
    <br/>   • Confirms momentum resumption and validates uptrend
    <br/>   • Accept higher entry price for reduced uncertainty
    """
    elements.append(Paragraph(position_sizing, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # Risk Management
    elements.append(Paragraph("Risk Management Framework", styles['SubHeader']))
    risk_mgmt = """
    <b>Stop Loss Strategy:</b>
    <br/>• Hard stop: -15% from entry (e.g., $629 if entering at $740)
    <br/>• ATR-based stop: 2× ATR = $28.80 below entry (~3.9% stop)
    <br/>• Trailing stop: Once up 10%, implement 8% trailing stop to protect gains
    <br/><br/>
    <b>Position Monitoring:</b>
    <br/>• Review quarterly holdings changes (VGT rebalances to track MSCI index)
    <br/>• Monitor NVDA weight - if exceeds 20%, consider trimming VGT exposure
    <br/>• Track correlation drift with VOO - if falls below 0.85, VGT adds more value
    <br/><br/>
    <b>Rebalancing Triggers:</b>
    <br/>• Reduce exposure if VGT exceeds 18% of total portfolio (concentration limit)
    <br/>• Consider profit-taking if Sharpe ratio falls below 0.3 (risk-reward deterioration)
    <br/>• Sell if semiconductor cycle peaks (watch NVDA revenue growth deceleration)
    """
    elements.append(Paragraph(risk_mgmt, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # FINAL VERDICT
    # =================================================================
    elements.append(Paragraph("Final Verdict & Action Items", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    # Verdict Box
    verdict_data = [
        ['RECOMMENDATION', 'CONDITIONAL BUY'],
        ['Target Entry', '$710-$750 (scale in)'],
        ['12-Month Price Target', '$829 (average analyst forecast)'],
        ['Expected Return', '+10-12%'],
        ['Risk Rating', 'MEDIUM-HIGH'],
        ['Conviction Level', '7/10'],
    ]
    verdict_table = Table(verdict_data, colWidths=[2.5*inch, 3.5*inch])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), NAVY),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('BACKGROUND', (1, 0), (1, 0), GREEN),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1.5, DARK_GRAY),
    ]))
    elements.append(verdict_table)
    elements.append(Spacer(1, 0.2*inch))

    verdict_rationale = """
    <b>Why CONDITIONAL BUY (Not STRONG BUY):</b>
    <br/><br/>
    <b>Strengths:</b>
    <br/>✓ Exceptional exposure to AI/semiconductor megatrend at lowest-cost structure (0.10% ER)
    <br/>✓ Best-in-class portfolio construction (NVDA + MSFT + AAPL = 45% of assets)
    <br/>✓ Strong historical performance (22.18% annualized over 10 years)
    <br/>✓ Positive alpha generation (+1.23% vs. SPY) with manageable beta (1.35)
    <br/>✓ 2026 catalysts firmly in place (AI capex cycle, semiconductor supply constraints)
    <br/><br/>
    <b>Limitations:</b>
    <br/>✗ Extreme correlation with VOO (0.943) and NVDA (0.864) reduces portfolio diversification
    <br/>✗ Current technical setup mixed - oversold but lacking momentum confirmation
    <br/>✗ Valuation risk: Tech multiples historically elevated with limited expansion runway
    <br/>✗ High volatility (28% annual) and -27% max drawdown demonstrate downside severity
    <br/>✗ Excludes AMZN/GOOG due to methodology - structural handicap vs. competitors
    <br/><br/>
    <b>Conditions for Upgrading to STRONG BUY:</b>
    <br/>1. Portfolio restructuring to reduce VOO/tech concentration (sell VOO, increase VGT)
    <br/>2. Technical confirmation: RSI above 50, MACD crossover, breakout above $780
    <br/>3. Valuation pullback: 10-15% correction to reset risk/reward
    """
    elements.append(Paragraph(verdict_rationale, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # Action Items
    elements.append(Paragraph("Recommended Action Items", styles['SubHeader']))
    action_items = """
    <b>Immediate Actions:</b>
    <br/>☐ Review current portfolio allocation: Calculate exact % in VOO, NVDA, PLTR, TSLA
    <br/>☐ Determine VGT allocation strategy: Supplement vs. Substitution approach
    <br/>☐ Set price alerts: $720 (buy signal), $780 (breakout confirmation)
    <br/>☐ Establish position size: Based on risk tolerance and correlation concerns
    <br/><br/>
    <b>Ongoing Monitoring (Monthly):</b>
    <br/>☐ Track VGT holdings changes (NVDA weight, new additions to top 10)
    <br/>☐ Review semiconductor sector fundamentals (NVDA earnings, TSMC capacity reports)
    <br/>☐ Monitor momentum indicators (RSI, MACD) for trend confirmation
    <br/>☐ Reassess correlation with portfolio holdings
    <br/><br/>
    <b>Risk Mitigation:</b>
    <br/>☐ Implement stop loss at -15% from entry
    <br/>☐ Consider VGT as VOO replacement (not supplement) to manage correlation
    <br/>☐ Hedge with uncorrelated asset class if VGT exceeds 15% of portfolio
    <br/>☐ Monitor sector rotation signals (capital flows into value/defensive sectors)
    """
    elements.append(Paragraph(action_items, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # APPENDIX: DATA SOURCES
    # =================================================================
    elements.append(Paragraph("Appendix: Data Sources & Methodology", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    sources_text = """
    <b>Market Data Sources:</b>
    <br/>• Price data: Yahoo Finance (yfinance API) - EOD data through 2025-12-17
    <br/>• Fund holdings: Vanguard Investor Portal, StockAnalysis.com
    <br/>• Analyst forecasts: Wallet Investor, StockScan.io, AIPickup
    <br/>• Industry research: WSTS (World Semiconductor Trade Statistics), Creative Strategies
    <br/><br/>
    <b>Analysis Tools:</b>
    <br/>• Risk Metrics CLI: 252-day lookback, benchmark = SPY
    <br/>• Momentum CLI: 90-day window, RSI/MACD/Stochastic/Williams %R/ROC
    <br/>• Volatility CLI: 90-day ATR, Bollinger Bands, Historical Volatility
    <br/>• Correlation CLI: 252-day Pearson correlation matrix
    <br/><br/>
    <b>Methodology:</b>
    <br/>• VaR/CVaR: Historical simulation method, 95% confidence level
    <br/>• Sharpe/Sortino: Annualized returns vs. risk-free rate (assumed 4.5%)
    <br/>• Beta/Alpha: OLS regression vs. SPY benchmark
    <br/>• Momentum: Standard technical analysis indicator calculations
    <br/><br/>
    <b>External Research:</b>
    <br/>• StockScan.io: VGT price forecasts 2025-2030
    <br/>• ETF Database: Fund characteristics and peer comparisons
    <br/>• Morningstar: Fund ratings and analyst commentary
    <br/>• The Motley Fool: Investment thesis and sector analysis
    <br/>• Tom's Hardware: Semiconductor industry "giga cycle" research
    <br/>• Vanguard Research: Economic and market outlook for 2026
    """
    elements.append(Paragraph(sources_text, styles['CustomBody']))

    elements.append(Spacer(1, 0.3*inch))

    # =================================================================
    # DISCLAIMER
    # =================================================================
    elements.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceBefore=20, spaceAfter=10))

    disclaimer = """
    <b>IMPORTANT DISCLAIMER:</b>
    <br/><br/>
    This report is prepared by Finance Guru™ for Ossie Irondi's private family office and is intended
    for <b>educational and informational purposes only</b>. This document does not constitute investment
    advice, a recommendation to buy or sell securities, or an offer to provide personalized investment
    advisory services.
    <br/><br/>
    All investments carry risk, including potential loss of principal. Past performance does not guarantee
    future results. The analysis contained herein is based on publicly available information and proprietary
    quantitative models, which may contain errors or omissions. Market conditions, valuations, and forecasts
    can change rapidly.
    <br/><br/>
    VGT is subject to sector concentration risk (99.2% technology), volatility risk (28% annual volatility),
    correlation risk (0.943 with S&P 500), and valuation risk. The fund's performance is heavily dependent
    on the technology sector and its top holdings (NVDA, AAPL, MSFT).
    <br/><br/>
    Before making investment decisions, consult with qualified financial, tax, and legal advisors who understand
    your personal financial situation, risk tolerance, and investment objectives.
    <br/><br/>
    <b>Report prepared by:</b> Finance Guru™ Multi-Agent Analyst Team
    <br/><b>Date:</b> December 18, 2025
    <br/><b>For:</b> Ossie Irondi - Private Family Office
    <br/><br/>
    © 2025 Finance Guru™ - All Rights Reserved
    """
    elements.append(Paragraph(disclaimer, styles['Disclaimer']))

    # =================================================================
    # BUILD PDF
    # =================================================================
    doc.build(elements)
    print(f"\n✅ PDF Report Generated Successfully!")
    print(f"📄 Location: {filename}")
    print(f"📊 Pages: Multi-page comprehensive analysis")
    print(f"🎯 Recommendation: CONDITIONAL BUY")

    return filename

if __name__ == "__main__":
    generate_vgt_report()
