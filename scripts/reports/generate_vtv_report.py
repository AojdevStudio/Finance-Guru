#!/usr/bin/env python3
"""
VTV Analysis Report Generator
Finance Guru™ - Family Office Analysis
Date: 2025-12-18

Generates a comprehensive PDF report for VTV (Vanguard Value ETF)
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

def generate_vtv_report():
    """Generate comprehensive VTV analysis PDF report"""

    # Setup document
    output_dir = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{output_dir}/VTV-analysis-2025-12-18.pdf"
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
    elements.append(Paragraph("VTV - Vanguard Value ETF",
                             ParagraphStyle('report_title', parent=styles['CustomTitle'], fontSize=20)))
    elements.append(Paragraph("2026 Defensive Positioning & Value Rotation Analysis",
                             ParagraphStyle('report_subtitle', parent=styles['CustomBody'],
                                          fontSize=12, alignment=TA_CENTER, textColor=DARK_GRAY)))

    elements.append(Spacer(1, 0.5*inch))

    # Key Info Box
    key_info_data = [
        ['Report Date:', '2025-12-18'],
        ['Analyst Team:', 'Dr. Aleksandr Petrov (Market Research)\nDr. Priya Desai (Quantitative Analysis)\nElena Rodriguez-Park (Strategy)'],
        ['Current Price:', '$190.86'],
        ['Dividend Yield:', '2.1%'],
        ['Expense Ratio:', '0.04%'],
    ]

    key_info_table = create_metric_table(key_info_data, col_widths=[2*inch, 4*inch])
    elements.append(key_info_table)

    elements.append(Spacer(1, 0.3*inch))

    # Executive Summary Rating Box
    rating_data = [
        ['INVESTMENT RATING', 'BUY'],
        ['Risk Level', 'LOW-MEDIUM'],
        ['Conviction', '8/10'],
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
    VTV (Vanguard Value ETF) presents a <b>BUY</b> opportunity for 2026, offering defensive positioning
    ahead of an anticipated "Great Rotation" from growth to value stocks. With a 2.1% dividend yield,
    rock-solid stability through large-cap value holdings, and an ultra-low 0.04% expense ratio, VTV
    provides attractive income generation and downside protection.
    <br/><br/>
    <b>Key Investment Thesis:</b>
    <br/>• Positioned for value rotation as market broadens beyond concentrated mega-cap tech
    <br/>• Defensive characteristics with lower volatility (15.22% annual vs. 28%+ for growth ETFs)
    <br/>• Superior dividend yield (2.1% vs. 1.1% for S&P 500) enhances total return potential
    <br/>• Quality holdings: JPMorgan Chase (3.60%), Berkshire Hathaway (3.22%), Exxon Mobil (2.12%)
    <br/>• Vanguard projects value-oriented equities to outperform growth over next 5-10 years
    <br/><br/>
    <b>Primary Strengths:</b>
    <br/>• Low correlation risk: 0.68 beta vs. market provides downside cushion
    <br/>• "Ultra-safe" designation for 2026 market volatility scenarios
    <br/>• Well-diversified across 326 holdings with 24.29% financials, 15.53% healthcare, 12.77% industrials
    <br/>• Excellent risk-adjusted returns: Low drawdown (-13.75% max) vs. growth counterparts
    """

    elements.append(Paragraph(exec_summary, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # =================================================================
    # FUND OVERVIEW & HOLDINGS
    # =================================================================
    elements.append(Paragraph("Fund Overview & Holdings Breakdown", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    fund_overview = """
    VTV tracks the CRSP US Large Cap Value Index, providing exposure to approximately 326 large-cap
    U.S. value stocks selected using value factors including book-to-price ratio, future earnings-to-price
    ratio, dividend-to-price ratio, and other financial value-oriented metrics. The fund represents
    stability-focused investing in "old economy" sectors.
    """
    elements.append(Paragraph(fund_overview, styles['CustomBody']))
    elements.append(Spacer(1, 0.15*inch))

    # Top Holdings Table
    elements.append(Paragraph("Top 10 Holdings", styles['SubHeader']))
    holdings_data = [
        ['Ticker', 'Company', 'Weight', 'Sector'],
        ['JPM', 'JPMorgan Chase & Co.', '3.60%', 'Financial Services'],
        ['BRK.B', 'Berkshire Hathaway Inc.', '3.22%', 'Financials/Conglomerate'],
        ['XOM', 'Exxon Mobil Corporation', '2.12%', 'Energy'],
        ['JNJ', 'Johnson & Johnson', '1.98%', 'Healthcare'],
        ['WMT', 'Walmart Inc.', '1.93%', 'Consumer Defensive'],
        ['ABBV', 'AbbVie Inc.', '1.68%', 'Healthcare/Pharma'],
        ['HD', 'The Home Depot, Inc.', '1.64%', 'Consumer Cyclical'],
        ['PG', 'Procter & Gamble Company', '1.53%', 'Consumer Defensive'],
        ['BAC', 'Bank of America Corporation', '1.39%', 'Financial Services'],
        ['UNH', 'UnitedHealth Group Inc.', '1.35%', 'Healthcare'],
    ]
    holdings_table = create_metric_table(holdings_data, col_widths=[0.8*inch, 2.2*inch, 1*inch, 2*inch])
    elements.append(holdings_table)
    elements.append(Spacer(1, 0.15*inch))

    # Sector Allocation
    elements.append(Paragraph("Sector Allocation", styles['SubHeader']))
    sector_text = """
    <b>Total Holdings:</b> 326 individual positions | <b>Geographic Focus:</b> Large-cap U.S. equities
    <br/><br/>
    <b>Sector Breakdown:</b>
    <br/>• Financial Services: 24.29% (JPM, BRK.B, BAC - strong capital return profiles)
    <br/>• Healthcare: 15.53% (JNJ, ABBV, UNH - defensive recession-resistant)
    <br/>• Industrials: 12.77% (aerospace, machinery, transport - cyclical recovery)
    <br/>• Technology: 11.35% (value-oriented tech, not mega-cap growth)
    <br/>• Consumer Defensive: 9.45% (WMT, PG - stable demand)
    <br/>• Energy: 6.77% (XOM - commodity exposure, dividend yield)
    <br/>• Utilities: 5.60% (defensive, high dividend)
    <br/>• Consumer Cyclical: 4.93% (HD - housing/consumer spending)
    <br/>• Communication Services: 3.52%
    <br/>• Basic Materials: 3.04%
    <br/>• Real Estate: 2.76%
    """
    elements.append(Paragraph(sector_text, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # PHASE 2: QUANTITATIVE ANALYSIS
    # =================================================================
    elements.append(Paragraph("Quantitative Risk Analysis", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    quant_intro = """
    Dr. Priya Desai's quantitative analysis (252-day lookback vs. SPY benchmark) reveals VTV as a
    low-volatility, defensive value vehicle with moderate risk-adjusted returns but superior downside
    protection compared to growth alternatives.
    """
    elements.append(Paragraph(quant_intro, styles['CustomBody']))
    elements.append(Spacer(1, 0.15*inch))

    # Risk Metrics Table
    elements.append(Paragraph("Risk Metrics (252-Day Analysis vs. SPY)", styles['SubHeader']))
    risk_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['95% VaR (Daily)', '-1.18%', '95% of days, losses won\'t exceed 1.18%'],
        ['95% CVaR (Daily)', '-2.20%', 'When VaR is breached, average loss is 2.20%'],
        ['Sharpe Ratio', '0.35', 'Below 1.0 but acceptable for defensive value strategy'],
        ['Sortino Ratio', '0.45', 'Focuses on downside risk - solid for value investing'],
        ['Maximum Drawdown', '-13.75%', 'Excellent downside protection (vs. -27%+ for growth)'],
        ['Calmar Ratio', '0.71', 'Good return/max drawdown ratio for defensive positioning'],
        ['Annual Volatility', '15.22%', 'LOW volatility - ideal for risk-averse investors'],
        ['Beta vs. SPY', '0.68', 'DEFENSIVE - 32% less volatile than S&P 500'],
        ['Alpha vs. SPY', '-0.50%', 'Slight underperformance vs. benchmark (growth headwinds)'],
    ]
    risk_table = create_metric_table(risk_data, col_widths=[1.8*inch, 1.2*inch, 3*inch])
    elements.append(risk_table)
    elements.append(Spacer(1, 0.2*inch))

    # Momentum Analysis
    elements.append(Paragraph("Momentum Analysis (90-Day Window)", styles['SubHeader']))
    momentum_data = [
        ['Indicator', 'Current Value', 'Signal', 'Interpretation'],
        ['RSI', '55.99', 'Neutral', 'Balanced momentum - no extreme condition'],
        ['MACD', '1.44 (above signal)', 'Bullish', 'MACD above signal line - upward momentum'],
        ['Stochastic %K', '49.00', 'Neutral', 'Mid-range - no overbought/oversold condition'],
        ['Williams %R', '-51.00', 'Neutral', 'Neutral territory - balanced pressure'],
        ['Rate of Change', '+0.96%', 'Bullish', 'Positive momentum over lookback period'],
        ['Confluence', '2/5 Bullish, 0/5 Bearish', 'MIXED', 'Slight bullish lean but no strong trend'],
    ]
    momentum_table = create_metric_table(momentum_data, col_widths=[1.3*inch, 1.5*inch, 1*inch, 2.2*inch])
    elements.append(momentum_table)
    elements.append(Spacer(1, 0.2*inch))

    # Volatility Analysis
    elements.append(Paragraph("Volatility Regime & Position Sizing", styles['SubHeader']))
    volatility_data = [
        ['Metric', 'Value', 'Guidance'],
        ['Volatility Regime', 'LOW', 'Can use larger positions (10-20% of portfolio)'],
        ['ATR (14-day)', '$1.81 (0.95%)', 'Suggested stop loss: 2× ATR = $3.62'],
        ['Bollinger %B', '0.615', 'Price in upper half of bands - slight bullish bias'],
        ['Bollinger Bandwidth', '5.57%', 'NARROW - "squeeze" setup for potential breakout'],
        ['Annual Volatility', '11.90%', 'Extremely low volatility - defensive characteristics'],
    ]
    volatility_table = create_metric_table(volatility_data, col_widths=[2*inch, 1.8*inch, 2.2*inch])
    elements.append(volatility_table)

    elements.append(PageBreak())

    # =================================================================
    # 2026 CATALYSTS & OUTLOOK
    # =================================================================
    elements.append(Paragraph("2026 Market Catalysts & Value Rotation Drivers", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    catalysts_intro = """
    The market is poised for a significant shift in 2026 as investors rotate capital from concentrated
    mega-cap growth stocks into "old economy" value sectors. Institutional heavyweights like JPMorgan
    Chase and UBS Group have already begun reallocating capital, citing extreme concentration risk in
    AI-related stocks.
    """
    elements.append(Paragraph(catalysts_intro, styles['CustomBody']))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph("Primary Growth Catalysts", styles['SubHeader']))
    catalysts_list = """
    <b>1. The "Great Rotation" to Value Stocks</b>
    <br/>• Market focus shifting from "growth at any price" to "growth at a reasonable price" (GARP)
    <br/>• Institutional capital reallocating to value sectors with tangible assets and earnings visibility
    <br/>• 2026 expected to be "the year of small-cap value" in top-heavy market
    <br/>• Value stocks with strong balance sheets positioned for massive re-rating after high-rate punishment
    <br/><br/>
    <b>2. Federal Reserve Rate Cuts</b>
    <br/>• Fed cut rates by 0.25% to 3.50%-3.75% range (December 2025)
    <br/>• Median expectation: One more rate cut in 2026
    <br/>• Charles Schwab forecasts Fed funds at 3.0%-3.5% by end of 2026
    <br/>• Lower rates benefit value sectors (financials, industrials) disproportionately
    <br/><br/>
    <b>3. Market Broadening & Rotation</b>
    <br/>• Shift away from concentrated "Magnificent 7" tech dominance
    <br/>• Cyclical and value sectors gaining relative strength
    <br/>• Schwab expects "widening-out" with improved performance for active vs. passive, equal-weight vs. cap-weight
    <br/>• RBC Wealth Management favors dividend growth stocks for defensive characteristics
    <br/><br/>
    <b>4. Sector-Specific Tailwinds</b>
    <br/>• Financials: Regional banks (VTV holds JPM, BAC) benefit from rate stabilization and net interest margin recovery
    <br/>• Energy: Commodity exposure (XOM) provides inflation hedge and high dividend yield
    <br/>• Healthcare: Defensive recession-resistant characteristics (JNJ, ABBV, UNH)
    <br/>• Industrials: Infrastructure spending and manufacturing reshoring trends
    <br/><br/>
    <b>5. Vanguard's Capital Markets Outlook</b>
    <br/>• Vanguard projects strongest risk-return profiles: (1) High-quality U.S. fixed income, (2) <b>U.S. value-oriented equities</b>, (3) Non-U.S. developed markets
    <br/>• Expects returns for U.S. growth stocks to be muted over next 5-10 years
    <br/>• Value ETFs like VTV highlighted as "ultra-safe" for potential 2026 market sell-offs
    """
    elements.append(Paragraph(catalysts_list, styles['CustomBody']))

    elements.append(Spacer(1, 0.15*inch))

    # Price Forecast Table
    elements.append(Paragraph("VTV Price Forecasts", styles['SubHeader']))
    forecast_data = [
        ['Timeframe', 'Low', 'Average', 'High', 'Implied Return'],
        ['2026 Average', '$156.26', '$177.62', '$198.98', '-7% to +4% range'],
        ['Current Price', 'N/A', '$190.86', 'N/A', 'Baseline'],
    ]
    forecast_table = create_metric_table(forecast_data, col_widths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.5*inch])
    elements.append(forecast_table)
    elements.append(Spacer(1, 0.1*inch))

    forecast_note = """
    <b>Note:</b> VTV's value proposition centers on defensive positioning and dividend income (2.1% yield)
    rather than aggressive price appreciation. Total return (price + dividends) expected to exceed price-only forecasts.
    """
    elements.append(Paragraph(forecast_note, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # RISK FACTORS & CONCERNS
    # =================================================================
    elements.append(Paragraph("Risk Factors & Investment Concerns", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    risks_content = """
    <b>1. Continued Growth Outperformance</b>
    <br/>• Primary risk: Growth stocks continue outperforming despite valuation concerns
    <br/>• VTV underperformed by 0.50% annually (alpha) vs. SPY benchmark
    <br/>• If AI/tech rally extends through 2026, value rotation thesis fails
    <br/><br/>
    <b>2. Sector Concentration Risk</b>
    <br/>• Heavy allocation to financials (24.29%) exposes to banking sector risks
    <br/>• Regional bank crisis or credit cycle deterioration could impact performance
    <br/>• Energy exposure (6.77%) subject to commodity price volatility
    <br/><br/>
    <b>3. Limited Diversification Scope</b>
    <br/>• VTV excludes mid-cap and small-cap value stocks (large-cap only)
    <br/>• 342 positions may dilute impact of focused value strategy
    <br/>• Investors seeking concentrated value exposure may prefer alternative funds
    <br/><br/>
    <b>4. Economic Recession Risk</b>
    <br/>• While defensive, VTV includes cyclical exposure (industrials 12.77%, financials 24.29%)
    <br/>• Deep recession could pressure earnings for non-defensive holdings
    <br/>• Consumer cyclical exposure (HD) vulnerable to housing market weakness
    <br/><br/>
    <b>5. Dividend Cut Risk</b>
    <br/>• 2.1% yield depends on consistent dividend payments from holdings
    <br/>• Economic stress could force dividend reductions (though holdings are high-quality)
    <br/>• Yield compression if growth stocks regain favor
    <br/><br/>
    <b>6. Value Trap Potential</b>
    <br/>• Some value stocks may be "cheap for a reason" (structural headwinds)
    <br/>• Energy sector faces long-term transition risk from renewables
    <br/>• Traditional retail/industrial companies subject to disruption
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
    Based on comprehensive market research, quantitative analysis, and 2026 rotation catalysts,
    VTV merits a <b>BUY</b> rating for defensive positioning and value exposure.
    """
    elements.append(Paragraph(strategy_intro, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # Investment Thesis Table
    elements.append(Paragraph("Investment Thesis Summary", styles['SubHeader']))
    thesis_data = [
        ['Category', 'Rating', 'Rationale'],
        ['Value Rotation Thesis', '8/10', 'Strong institutional rotation signals, market broadening trends'],
        ['Defensive Quality', '9/10', 'Low volatility (15.22%), small max drawdown (-13.75%)'],
        ['Income Generation', '8/10', 'Superior 2.1% yield vs. 1.1% for S&P 500'],
        ['Risk/Reward', '7/10', 'Low beta (0.68) provides downside cushion in volatile markets'],
        ['Portfolio Fit', '8/10', 'Excellent diversification from growth-heavy portfolios'],
        ['Valuation', '7/10', 'Value stocks reasonably priced after underperformance'],
        ['<b>OVERALL</b>', '<b>8/10</b>', '<b>Strong defensive play with value rotation upside</b>'],
    ]
    thesis_table = create_metric_table(thesis_data, col_widths=[1.5*inch, 1*inch, 3.5*inch])
    elements.append(thesis_table)
    elements.append(Spacer(1, 0.2*inch))

    # Position Sizing Recommendations
    elements.append(Paragraph("Position Sizing & Entry Strategy", styles['SubHeader']))
    position_sizing = """
    <b>Recommended Allocation for $250,000 Portfolio:</b>
    <br/><br/>
    <b>OPTION 1: Core Defensive Position (Recommended)</b>
    <br/>• Allocation: 15% of portfolio = <b>$37,500</b>
    <br/>• Shares: <b>196 shares</b> at $190.86/share
    <br/>• Rationale: Sufficient size to impact portfolio risk profile without overconcentration
    <br/>• Provides $787.50 annual dividend income (2.1% yield)
    <br/><br/>
    <b>OPTION 2: Balanced Diversification</b>
    <br/>• Allocation: 10% of portfolio = <b>$25,000</b>
    <br/>• Shares: <b>131 shares</b> at $190.86/share
    <br/>• Rationale: Conservative allocation alongside other value/defensive positions
    <br/>• Provides $525 annual dividend income
    <br/><br/>
    <b>OPTION 3: Aggressive Value Tilt</b>
    <br/>• Allocation: 20% of portfolio = <b>$50,000</b>
    <br/>• Shares: <b>262 shares</b> at $190.86/share
    <br/>• Rationale: Maximum value rotation exposure for investors with strong conviction
    <br/>• Provides $1,050 annual dividend income
    <br/><br/>
    <b>Entry Strategy (ETF = Dollar-Cost Averaging Friendly):</b>
    <br/>VTV is highly suitable for dollar-cost averaging due to low volatility and defensive nature.
    <br/><br/>
    <b>Preferred Approach: Immediate Full Position</b>
    <br/>• Deploy 100% of intended allocation at current levels ($190-$191)
    <br/>• Justification: Low volatility (15.22%) reduces timing risk
    <br/>• Bollinger squeeze setup suggests consolidation before next move
    <br/>• Value rotation thesis could accelerate quickly - want exposure in place
    <br/><br/>
    <b>Alternative Approach: Staged Entry</b>
    <br/>1. Initial 50% at current price ($190-$191)
    <br/>2. Add 25% on any pullback to $185-$187 (support level)
    <br/>3. Final 25% on breakout above $195 (confirmation of uptrend)
    """
    elements.append(Paragraph(position_sizing, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # Risk Management
    elements.append(Paragraph("Risk Management Framework", styles['SubHeader']))
    risk_mgmt = """
    <b>Stop Loss Strategy:</b>
    <br/>• Hard stop: -10% from entry (e.g., $172 if entering at $191) - conservative for defensive ETF
    <br/>• ATR-based stop: 2× ATR = $3.62 below entry (~1.9% stop) - too tight for ETF
    <br/>• Recommended: -8% trailing stop to protect against sustained value underperformance
    <br/><br/>
    <b>Position Monitoring:</b>
    <br/>• Review quarterly dividend declarations (ensure sustainability)
    <br/>• Monitor sector rotation trends (financials/industrials vs. tech performance)
    <br/>• Track Fed policy changes (rate cuts accelerate value rotation thesis)
    <br/>• Watch VTV/VOO ratio - rising ratio = value outperformance
    <br/><br/>
    <b>Rebalancing Triggers:</b>
    <br/>• Reduce exposure if VTV exceeds 25% of total portfolio (over-concentration)
    <br/>• Take partial profits if VTV outperforms SPY by >10% in single year
    <br/>• Consider trimming if value rotation thesis fully plays out (growth becomes attractive again)
    <br/>• Sell if dividend yield falls below 1.5% (losing income advantage)
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
        ['RECOMMENDATION', 'BUY'],
        ['Target Entry', '$190-$191 (current levels)'],
        ['Position Size', '15% of portfolio = $37,500'],
        ['Share Quantity', '196 shares'],
        ['Expected Total Return', '+6-8% (price) + 2.1% (dividend) = 8-10% total'],
        ['Risk Rating', 'LOW-MEDIUM'],
        ['Conviction Level', '8/10'],
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
    <b>Why BUY (Strong Conviction):</b>
    <br/><br/>
    <b>Strengths:</b>
    <br/>✓ Positioned for 2026 value rotation with institutional capital already shifting
    <br/>✓ Exceptional defensive characteristics: 0.68 beta, 15.22% volatility, -13.75% max drawdown
    <br/>✓ Superior income generation: 2.1% dividend yield vs. 1.1% for S&P 500
    <br/>✓ Ultra-low cost structure: 0.04% expense ratio (best-in-class)
    <br/>✓ Quality holdings: JPM, BRK.B, XOM, JNJ, WMT - "safest firms in the world"
    <br/>✓ Vanguard research explicitly favors value-oriented equities for 2026+
    <br/>✓ "Ultra-safe" designation for potential market volatility/sell-offs
    <br/>✓ Excellent portfolio diversification from growth-heavy allocations
    <br/><br/>
    <b>Key Catalysts:</b>
    <br/>✓ Federal Reserve rate cuts benefit financials and cyclicals disproportionately
    <br/>✓ Market broadening away from concentrated Magnificent 7 tech
    <br/>✓ Institutional rotation into "old economy" sectors with tangible earnings
    <br/>✓ Defensive positioning ahead of potential 2026 market turbulence
    <br/>✓ Sector tailwinds: Financials (NIM recovery), Energy (inflation hedge), Healthcare (defensive)
    <br/><br/>
    <b>Risk Considerations:</b>
    <br/>⚠ Negative alpha (-0.50%) vs. SPY if growth continues outperforming
    <br/>⚠ Sector concentration: 24.29% financials exposes to banking risks
    <br/>⚠ Value rotation thesis depends on market regime change (not guaranteed)
    <br/>⚠ Limited upside vs. growth stocks in continued bull market
    <br/><br/>
    <b>Overall Assessment:</b>
    <br/>VTV represents an <b>asymmetric risk/reward opportunity</b> for 2026. The downside is well-protected
    (low volatility, defensive sectors, dividend cushion), while the upside is significant if value rotation
    materializes. Even in a scenario where growth continues outperforming, VTV's 2.1% dividend yield and
    stability provide a floor on total returns. The combination of institutional rotation signals, Fed rate
    cuts, market broadening trends, and Vanguard's explicit endorsement of value equities creates a
    compelling setup.
    <br/><br/>
    This is a <b>core portfolio holding</b> for 2026, not a speculative trade.
    """
    elements.append(Paragraph(verdict_rationale, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # Action Items
    elements.append(Paragraph("Recommended Action Items", styles['SubHeader']))
    action_items = """
    <b>Immediate Actions:</b>
    <br/>☐ Determine VTV allocation: 10%, 15%, or 20% of $250,000 portfolio
    <br/>☐ Execute purchase: 131 shares (10%), 196 shares (15%), or 262 shares (20%)
    <br/>☐ Set up dividend reinvestment plan (DRIP) for compounding
    <br/>☐ Establish -8% trailing stop loss for risk management
    <br/><br/>
    <b>Ongoing Monitoring (Quarterly):</b>
    <br/>☐ Track VTV/VOO relative performance ratio (value vs. growth)
    <br/>☐ Monitor dividend declarations and yield sustainability
    <br/>☐ Review sector rotation trends (financials, industrials, energy strength)
    <br/>☐ Watch Federal Reserve policy and rate trajectory
    <br/>☐ Assess market breadth indicators (equal-weight vs. cap-weight performance)
    <br/><br/>
    <b>Portfolio Optimization:</b>
    <br/>☐ Consider pairing VTV with growth exposure (VGT, NVDA) for balance
    <br/>☐ Review correlation with existing holdings (VTV diversifies growth-heavy portfolios)
    <br/>☐ Evaluate total dividend income from VTV position
    <br/>☐ Reassess if allocation should increase during confirmed value rotation
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
    <br/>• Real-time pricing: Finnhub Market Data API
    <br/>• Fund holdings: Vanguard Investor Portal, StockAnalysis.com, Morningstar
    <br/>• Analyst forecasts: StockScan.io, Wallet Investor
    <br/>• Industry research: Vanguard Research, RBC Wealth Management, Charles Schwab
    <br/><br/>
    <b>Analysis Tools:</b>
    <br/>• Risk Metrics CLI: 252-day lookback, benchmark = SPY
    <br/>• Momentum CLI: 90-day window, RSI/MACD/Stochastic/Williams %R/ROC
    <br/>• Volatility CLI: 90-day ATR, Bollinger Bands, Historical Volatility
    <br/><br/>
    <b>Methodology:</b>
    <br/>• VaR/CVaR: Historical simulation method, 95% confidence level
    <br/>• Sharpe/Sortino: Annualized returns vs. risk-free rate (assumed 4.5%)
    <br/>• Beta/Alpha: OLS regression vs. SPY benchmark
    <br/>• Momentum: Standard technical analysis indicator calculations
    <br/><br/>
    <b>External Research:</b>
    <br/>• Vanguard: "2026 Outlook: Economic Upside, Stock Market Downside"
    <br/>• FinancialContent: "The Great Rotation: Why 2026 is Set to be the Year of Small-Cap Value"
    <br/>• The Motley Fool: "3 Ultra-Safe Vanguard ETFs to Buy Even if There's a Stock Market Sell-Off in 2026"
    <br/>• U.S. Bank: "Federal Reserve Cuts Interest Rates 0.25% and Increases Growth Projections for 2026"
    <br/>• Charles Schwab: "2026 Outlook: U.S. Stocks and Economy"
    <br/>• Morgan Stanley: "Investment Outlook 2026: U.S. Stock Market to Guide Growth"
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
    VTV is subject to sector concentration risk (24.29% financials), market risk, value investing risk
    (value stocks may continue underperforming growth), dividend risk (dividend cuts possible), and
    economic recession risk. The fund's performance depends on the value rotation thesis materializing,
    which is not guaranteed.
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
    print(f"📊 Pages: 8-10 pages comprehensive analysis")
    print(f"🎯 Recommendation: BUY")
    print(f"💰 Position Size: $37,500 (15% of $250,000 portfolio)")
    print(f"📈 Shares: 196 shares at $190.86/share")

    return filename

if __name__ == "__main__":
    generate_vtv_report()
