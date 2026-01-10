#!/usr/bin/env python3
"""
GOOG (Alphabet) Analysis Report Generator
Finance Guru™ - Family Office Analysis
Date: 2025-12-18

Generates a comprehensive PDF report for GOOG (Alphabet Inc. - Class C)
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

def generate_goog_report():
    """Generate comprehensive GOOG analysis PDF report"""

    # Setup document
    output_dir = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports"
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{output_dir}/GOOG-analysis-2025-12-18.pdf"
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
    elements.append(Paragraph("GOOG - Alphabet Inc. (Class C)",
                             ParagraphStyle('report_title', parent=styles['CustomTitle'], fontSize=20)))
    elements.append(Paragraph("2026 AI Leadership Analysis & Investment Recommendation",
                             ParagraphStyle('report_subtitle', parent=styles['CustomBody'],
                                          fontSize=12, alignment=TA_CENTER, textColor=DARK_GRAY)))

    elements.append(Spacer(1, 0.5*inch))

    # Key Info Box
    key_info_data = [
        ['Report Date:', '2025-12-18'],
        ['Analyst Team:', 'Dr. Aleksandr Petrov (Market Research)\nDr. Priya Desai (Quantitative Analysis)\nElena Rodriguez-Park (Strategy)'],
        ['Current Price:', '$303.75'],
        ['52-Week Range:', '$143 - $329'],
        ['YTD Performance:', '+112.7% (from $143 low)'],
        ['Market Cap:', '~$3.7 Trillion'],
    ]

    key_info_table = create_metric_table(key_info_data, col_widths=[2*inch, 4*inch])
    elements.append(key_info_table)

    elements.append(Spacer(1, 0.3*inch))

    # Executive Summary Rating Box
    rating_data = [
        ['INVESTMENT RATING', 'STRONG BUY'],
        ['Risk Level', 'MEDIUM'],
        ['Conviction', '9/10'],
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
    Alphabet (GOOG) represents a <b>STRONG BUY</b> opportunity heading into 2026, uniquely positioned at the
    intersection of AI innovation, cloud infrastructure growth, and autonomous vehicle commercialization.
    Trading at $303.75 with a market cap approaching $3.7 trillion, GOOG combines the defensive moat of
    Google Search with explosive growth vectors in Gemini AI, Google Cloud, and Waymo.
    <br/><br/>
    <b>Core Investment Thesis:</b>
    <br/>• Gemini 3 AI breakthrough: 650M+ monthly users, superior benchmarks vs. ChatGPT/Claude
    <br/>• Google Cloud accelerating: 34% YoY growth, $15.16B quarterly revenue, $155B backlog (+46% sequentially)
    <br/>• Waymo scaling aggressively: 450K rides/week → 1M target by end-2026, expansion to 20+ cities
    <br/>• Search dominance intact: 14.5% YoY growth despite AI competition, proving resilience
    <br/>• Superior risk-adjusted returns: Sharpe 1.64, Alpha +44.95% vs. SPY
    <br/><br/>
    <b>Key Catalysts for 2026:</b>
    <br/>• Revenue growth: $410.7B (2025) → $465.6B (2026) projected
    <br/>• EPS expansion: $11.47 expected, driving earnings leadership in tech
    <br/>• Waymo valuation inflection: Approaching $100B valuation, $1B+ revenue by 2026
    <br/>• AI monetization: Gemini integration across Search, YouTube, Cloud driving new revenue streams
    <br/><br/>
    <b>Risk Factors (Manageable):</b>
    <br/>• Antitrust headwinds: September 2025 ruling REJECTED DOJ breakup demands (ChatGPT cited as competition)
    <br/>• Medium volatility: 32.76% annual vol, but lower than pure-play AI stocks
    <br/>• Capex intensity: $91-93B expected in 2025, but necessary for AI infrastructure leadership
    <br/>• Oversold technicals: Mixed momentum signals create near-term entry opportunity
    """

    elements.append(Paragraph(exec_summary, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # =================================================================
    # BUSINESS OVERVIEW
    # =================================================================
    elements.append(Paragraph("Business Segment Breakdown", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    business_overview = """
    Alphabet operates a diversified portfolio of internet services and moonshot technologies, with Q3 2025
    marking the first time total revenue exceeded $100 billion in a single quarter.
    """
    elements.append(Paragraph(business_overview, styles['CustomBody']))
    elements.append(Spacer(1, 0.15*inch))

    # Business Segments Table
    elements.append(Paragraph("Revenue Segments (Q3 2025)", styles['SubHeader']))
    segments_data = [
        ['Segment', 'Revenue Growth', 'Strategic Importance'],
        ['Google Search', '+14.5% YoY', 'Core cash engine - AI integration enhancing results'],
        ['YouTube Advertising', '+15% YoY', 'Growing share of video ad market, Shorts monetization'],
        ['Google Cloud', '+34% YoY ($15.16B)', 'CRITICAL - AI infrastructure, enterprise migration'],
        ['Google Subscriptions', '+20% YoY', 'Gemini Advanced, YouTube Premium, Google One'],
        ['Google Other', 'Various', 'Hardware (Pixel), Play Store commissions'],
        ['Other Bets (Waymo)', 'Pre-revenue scale', 'Multi-trillion TAM potential, 2026 breakout'],
    ]
    segments_table = create_metric_table(segments_data, col_widths=[1.5*inch, 1.8*inch, 2.7*inch])
    elements.append(segments_table)
    elements.append(Spacer(1, 0.15*inch))

    # Competitive Positioning
    elements.append(Paragraph("Competitive Moats & Defensibility", styles['SubHeader']))
    moats_text = """
    <b>1. Search Dominance:</b> 90%+ global search market share, ~8.5 billion searches/day
    <br/>• Network effects: More users → better data → better results → more users
    <br/>• AI enhancement: Gemini integration making search results more conversational and accurate
    <br/><br/>
    <b>2. Cloud Infrastructure:</b> Third-largest cloud provider (behind AWS, Azure)
    <br/>• Differentiation: TPU chips (Tensor Processing Units) for AI workloads
    <br/>• Strategic wins: Enterprise AI customers choosing GCP for Gemini integration
    <br/>• Backlog growth: $155B (+46% QoQ) demonstrates sustained demand
    <br/><br/>
    <b>3. AI Model Leadership:</b> Gemini 3 outperforming GPT-4 and Claude in key benchmarks
    <br/>• 650M monthly active users (catching up to ChatGPT's 845M)
    <br/>• Multimodal capabilities: Text, image, video, code generation
    <br/>• Distribution advantage: Pre-installed on 3B+ Android devices
    <br/><br/>
    <b>4. Data Moat:</b> Unmatched dataset from Search, YouTube, Gmail, Maps, Android
    <br/>• Proprietary training data for AI models that competitors cannot replicate
    <br/>• Real-time web indexing provides freshness advantage over static models
    """
    elements.append(Paragraph(moats_text, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # PHASE 2: QUANTITATIVE ANALYSIS
    # =================================================================
    elements.append(Paragraph("Quantitative Risk Analysis", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    quant_intro = """
    Dr. Priya Desai's quantitative analysis (252-day lookback vs. SPY benchmark) reveals GOOG as a
    high-conviction, medium-volatility growth asset with exceptional risk-adjusted returns.
    """
    elements.append(Paragraph(quant_intro, styles['CustomBody']))
    elements.append(Spacer(1, 0.15*inch))

    # Risk Metrics Table
    elements.append(Paragraph("Risk Metrics (252-Day Analysis vs. SPY)", styles['SubHeader']))
    risk_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['95% VaR (Daily)', '-2.93%', '95% of days, losses won\'t exceed 2.93%'],
        ['95% CVaR (Daily)', '-4.24%', 'When VaR breached, average loss is 4.24%'],
        ['Sharpe Ratio', '1.64', 'GOOD - Strong risk-adjusted returns (1.0-2.0 range)'],
        ['Sortino Ratio', '2.62', 'EXCELLENT - Minimal downside volatility'],
        ['Maximum Drawdown', '-29.35%', 'Manageable worst-case decline'],
        ['Calmar Ratio', '1.98', 'Strong return vs. max drawdown risk'],
        ['Annual Volatility', '32.76%', 'MEDIUM - Higher than SPY, lower than small-cap tech'],
        ['Beta vs. SPY', '1.04', 'AVERAGE - Slightly above market systematic risk'],
        ['Alpha vs. SPY', '+44.95%', 'EXCEPTIONAL - Massive outperformance'],
    ]
    risk_table = create_metric_table(risk_data, col_widths=[1.8*inch, 1.2*inch, 3*inch])
    elements.append(risk_table)
    elements.append(Spacer(1, 0.2*inch))

    # Momentum Analysis
    elements.append(Paragraph("Momentum Analysis (90-Day Window)", styles['SubHeader']))
    momentum_data = [
        ['Indicator', 'Current Value', 'Signal', 'Interpretation'],
        ['RSI', '45.64', 'Neutral', 'No extreme overbought/oversold condition'],
        ['MACD', '6.13 vs 9.75', 'Bearish', 'MACD below signal - short-term weakness'],
        ['Stochastic %K', '2.09', 'Oversold', 'EXTREME oversold - reversal setup'],
        ['Williams %R', '-97.91', 'Oversold', 'DEEP oversold - strong buy signal'],
        ['Rate of Change', '-5.35%', 'Bearish', 'Recent pullback from highs'],
        ['Confluence', '2/5 Bullish, 2/5 Bearish', 'MIXED', 'Consolidation phase - await confirmation'],
    ]
    momentum_table = create_metric_table(momentum_data, col_widths=[1.3*inch, 1.5*inch, 1*inch, 2.2*inch])
    elements.append(momentum_table)
    elements.append(Spacer(1, 0.2*inch))

    # Volatility Analysis
    elements.append(Paragraph("Volatility Regime & Position Sizing", styles['SubHeader']))
    volatility_data = [
        ['Metric', 'Value', 'Guidance'],
        ['Volatility Regime', 'NORMAL', 'Standard position sizing (5-10% of portfolio)'],
        ['ATR (14-day)', '$8.77 (2.89%)', 'Suggested stop loss: 2× ATR = $17.55'],
        ['Bollinger %B', '0.248', 'Below midpoint - room to run upward'],
        ['Bollinger Bandwidth', '11.63%', 'Moderate - normal trading range'],
        ['Historical Volatility', '33.87%', 'Consistent with 252-day measure (32.76%)'],
    ]
    volatility_table = create_metric_table(volatility_data, col_widths=[2*inch, 1.8*inch, 2.2*inch])
    elements.append(volatility_table)

    elements.append(PageBreak())

    # =================================================================
    # 2026 CATALYSTS & MARKET OUTLOOK
    # =================================================================
    elements.append(Paragraph("2026 Growth Catalysts & Strategic Drivers", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    catalysts_intro = """
    Alphabet enters 2026 with multiple tailwinds converging: AI model leadership, cloud acceleration,
    Waymo commercialization, and regulatory clarity post-antitrust ruling.
    """
    elements.append(Paragraph(catalysts_intro, styles['CustomBody']))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(Paragraph("Primary Growth Catalysts", styles['SubHeader']))
    catalysts_list = """
    <b>1. Gemini AI Monetization</b>
    <br/>• Gemini 3 performance: Outperforming GPT-4 and Claude in benchmark tests
    <br/>• User growth: 650M MAU → targeting ChatGPT's 845M and beyond
    <br/>• Revenue integration: Gemini Advanced subscriptions, Search enhancements, YouTube summaries
    <br/>• Enterprise adoption: Google Workspace AI features driving upsell opportunities
    <br/><br/>
    <b>2. Google Cloud Acceleration</b>
    <br/>• Q3 2025 performance: 34% YoY growth to $15.16B revenue
    <br/>• Backlog expansion: $155B (+46% sequentially) - locked-in future revenue
    <br/>• AI infrastructure: TPU chips providing differentiation vs. AWS/Azure
    <br/>• Enterprise migrations: Oracle Cloud Infrastructure partnerships, hybrid cloud wins
    <br/><br/>
    <b>3. Waymo Commercial Scale-Up</b>
    <br/>• Current: 450K rides/week across Phoenix, SF, LA, Atlanta, Austin
    <br/>• 2026 target: 1M rides/week, expansion to 20+ cities (London, Tokyo, Miami, DC, Boston)
    <br/>• Revenue projections: $374M (2025) → $748M (2026) → $1B+ (consensus)
    <br/>• Valuation inflection: Approaching $100B valuation (current ~$45B last round)
    <br/>• TAM: $1.2 trillion autonomous vehicle market by 2040
    <br/><br/>
    <b>4. YouTube & Search Resilience</b>
    <br/>• Search growth: +14.5% YoY despite AI chatbot competition
    <br/>• YouTube ads: +15% YoY, Shorts monetization scaling
    <br/>• September 2025 ruling: Judge cited AI competition as reason to reject DOJ breakup
    <br/><br/>
    <b>5. Regulatory Clarity</b>
    <br/>• Antitrust resolution: Federal judge REJECTED Chrome/YouTube divestiture
    <br/>• AI competition narrative: OpenAI's ChatGPT growth helped Google's defense
    <br/>• Trump administration: "America's AI Action Plan" focuses on removing regulatory barriers
    """
    elements.append(Paragraph(catalysts_list, styles['CustomBody']))

    elements.append(Spacer(1, 0.15*inch))

    # Analyst Price Forecasts
    elements.append(Paragraph("Wall Street Price Targets & Forecasts", styles['SubHeader']))
    forecast_data = [
        ['Analyst/Firm', 'Price Target', 'Timeframe', 'Key Rationale'],
        ['Median (37 analysts)', '$340.00', '12-month', 'Strong Buy consensus (9.1/10)'],
        ['J.P. Morgan', '$385.00', '12-month', 'Cloud growth, Gemini monetization'],
        ['HSBC', '$370.00', '12-month', 'Gemini 3 performance vs. rivals'],
        ['TD Cowen', '$350.00', '12-month', 'AI infrastructure leadership'],
        ['BMO Capital', '$343.00', '12-month', 'Google Cloud acceleration'],
        ['Bear Case', '$185.00', '12-month', 'Extreme regulatory scenario'],
    ]
    forecast_table = create_metric_table(forecast_data, col_widths=[1.5*inch, 1.2*inch, 1.2*inch, 2.1*inch])
    elements.append(forecast_table)
    elements.append(Spacer(1, 0.15*inch))

    price_target_summary = """
    <b>Upside Potential:</b>
    <br/>• Current price: $303.75
    <br/>• Median target: $340.00 (+11.9% upside)
    <br/>• Bull case (J.P. Morgan): $385.00 (+26.7% upside)
    <br/>• Consensus EPS 2026: $11.47, Revenue: $465.6B (+13.4% YoY)
    """
    elements.append(Paragraph(price_target_summary, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # RISK FACTORS
    # =================================================================
    elements.append(Paragraph("Risk Factors & Investment Concerns", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    risks_content = """
    <b>1. Regulatory & Antitrust (MODERATE RISK - Declining)</b>
    <br/>• September 2025 ruling rejected DOJ breakup demands
    <br/>• EU AI investigation ongoing - potential multi-billion euro fines
    <br/>• Trump administration favoring AI innovation over regulation
    <br/>• ChatGPT's rise ironically helped Google's antitrust defense
    <br/><br/>
    <b>2. AI Competition (MODERATE RISK)</b>
    <br/>• OpenAI (ChatGPT), Anthropic (Claude), Meta (Llama) intensifying competition
    <br/>• Search disruption: Perplexity, ChatGPT search features threatening Google's moat
    <br/>• Mitigation: Gemini 3 benchmarks showing competitive/superior performance
    <br/>• Distribution advantage: 3B+ Android devices, Chrome integration
    <br/><br/>
    <b>3. Capex Intensity (MODERATE RISK)</b>
    <br/>• $91-93B expected capex for 2025 (AI chips, data centers, infrastructure)
    <br/>• Investor concern: "AI arms race" becoming unsustainably capital-intensive
    <br/>• Mitigation: Cloud revenue accelerating (34% YoY), demonstrating ROI on AI spend
    <br/><br/>
    <b>4. Technical Momentum (SHORT-TERM RISK)</b>
    <br/>• Mixed signals: RSI neutral, MACD bearish, oversold stochastic
    <br/>• Recent pullback: -5.35% rate of change over 90 days
    <br/>• Opportunity: Oversold technicals create attractive entry point
    <br/><br/>
    <b>5. Valuation Multiple Risk (LOW-MODERATE RISK)</b>
    <br/>• Tech sector at elevated multiples, limited expansion room
    <br/>• However: GOOG cheaper than MSFT, NVDA on P/E basis
    <br/>• EPS growth trajectory supports current valuation
    <br/><br/>
    <b>6. Waymo Execution Risk (LOW RISK)</b>
    <br/>• Aggressive expansion to 20+ cities requires flawless execution
    <br/>• Safety incidents could trigger regulatory backlash
    <br/>• Mitigation: 88% fewer property damage claims, 92% fewer injuries vs. human drivers
    """
    elements.append(Paragraph(risks_content, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # PORTFOLIO STRATEGY & POSITION SIZING
    # =================================================================
    elements.append(Paragraph("Investment Strategy & Position Sizing", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    strategy_intro = """
    <b>Analyst: Elena Rodriguez-Park, CFA - Head of Strategy</b>
    <br/><br/>
    Based on fundamental strength, quantitative metrics, and 2026 catalysts, GOOG merits a
    <b>STRONG BUY</b> rating with aggressive position sizing.
    """
    elements.append(Paragraph(strategy_intro, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # Investment Thesis Summary
    elements.append(Paragraph("Investment Thesis Scorecard", styles['SubHeader']))
    thesis_data = [
        ['Category', 'Rating', 'Rationale'],
        ['Growth Potential', '9/10', 'AI, Cloud, Waymo - multiple 25%+ growth vectors'],
        ['Competitive Moat', '10/10', 'Search dominance, data moat, AI leadership, distribution'],
        ['Valuation', '7/10', 'Reasonable vs. growth rate, cheaper than MSFT/NVDA'],
        ['Risk/Reward', '8/10', 'Sharpe 1.64, Alpha +44.95%, manageable downside'],
        ['Execution Track Record', '8/10', 'Cloud scaling, Gemini launch, Waymo progress'],
        ['Technical Setup', '6/10', 'Oversold short-term, but creates entry opportunity'],
        ['<b>OVERALL</b>', '<b>9/10</b>', '<b>Exceptional multi-year growth story with defensive moats</b>'],
    ]
    thesis_table = create_metric_table(thesis_data, col_widths=[1.5*inch, 1*inch, 3.5*inch])
    elements.append(thesis_table)
    elements.append(Spacer(1, 0.2*inch))

    # Position Sizing for $250K Portfolio
    elements.append(Paragraph("Position Sizing Recommendation ($250,000 Portfolio)", styles['SubHeader']))
    position_sizing = """
    <b>Recommended Allocation: 8-10% ($20,000 - $25,000)</b>
    <br/><br/>
    <b>Conservative Approach (8% = $20,000):</b>
    <br/>• Share quantity: 65 shares @ $303.75 = $19,743.75
    <br/>• Rationale: Balanced exposure, room to scale up if thesis plays out
    <br/>• Stop loss: -15% ($258.19) = maximum loss of $2,961.88
    <br/><br/>
    <b>Moderate Approach (9% = $22,500):</b>
    <br/>• Share quantity: 74 shares @ $303.75 = $22,477.50
    <br/>• Rationale: Conviction-weighted position, aligned with 9/10 rating
    <br/>• Stop loss: -15% ($258.19) = maximum loss of $3,371.63
    <br/><br/>
    <b>Aggressive Approach (10% = $25,000):</b>
    <br/>• Share quantity: 82 shares @ $303.75 = $24,907.50
    <br/>• Rationale: High-conviction core holding, strong risk-adjusted metrics
    <br/>• Stop loss: -15% ($258.19) = maximum loss of $3,736.13
    <br/><br/>
    <b>RECOMMENDED: Moderate Approach (74 shares = $22,477.50 = 9% of portfolio)</b>
    <br/>• Aligns with 9/10 conviction rating
    <br/>• Provides meaningful exposure without overconcentration
    <br/>• Allows room to scale up to 12-15% if catalysts materialize
    """
    elements.append(Paragraph(position_sizing, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # Entry Strategy
    elements.append(Paragraph("Entry Strategy & Execution Plan", styles['SubHeader']))
    entry_strategy = """
    <b>Oversold Technical Setup = Attractive Entry Opportunity</b>
    <br/><br/>
    <b>Option 1: Immediate Full Entry (RECOMMENDED)</b>
    <br/>• Buy 74 shares @ current price ($303.75)
    <br/>• Rationale: Stochastic (2.09) and Williams %R (-97.91) extreme oversold
    <br/>• Risk: Short-term MACD bearish, but fundamentals strong
    <br/>• Benefit: Capture potential reversal, avoid missing rally
    <br/><br/>
    <b>Option 2: Scaled Entry (Conservative)</b>
    <br/>• Tranche 1: Buy 37 shares (50%) at current price
    <br/>• Tranche 2: Buy 22 shares (30%) on any pullback to $290-$295
    <br/>• Tranche 3: Buy 15 shares (20%) on breakout above $320 (MACD confirmation)
    <br/>• Benefit: Lower average cost if further weakness, but risk missing rally
    <br/><br/>
    <b>Recommendation: Option 1 - Immediate Full Entry</b>
    <br/>• Oversold technicals suggest limited further downside
    <br/>• Fundamental catalysts (Cloud, Gemini, Waymo) intact
    <br/>• Risk/reward favorable: 11.9% upside to median PT ($340) vs. stop at -15%
    """
    elements.append(Paragraph(entry_strategy, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # Risk Management
    elements.append(Paragraph("Risk Management Framework", styles['SubHeader']))
    risk_mgmt = """
    <b>Stop Loss Strategy:</b>
    <br/>• Hard stop: -15% from entry ($258.19 if entering at $303.75)
    <br/>• ATR-based stop: 2× ATR = $17.55 below entry = $286.20 (~5.8% stop)
    <br/>• Trailing stop: Once up 15%, implement 10% trailing stop to protect gains
    <br/><br/>
    <b>Position Monitoring (Weekly):</b>
    <br/>• Track Google Cloud revenue growth (quarterly earnings)
    <br/>• Monitor Gemini user metrics and competitive benchmarks
    <br/>• Watch Waymo expansion milestones (ride volume, new cities)
    <br/>• Review analyst price target changes
    <br/><br/>
    <b>Profit-Taking Targets:</b>
    <br/>• Trim 25% at $340 (median analyst target, +11.9%)
    <br/>• Trim 25% at $370 (HSBC target, +21.8%)
    <br/>• Trim 25% at $385 (J.P. Morgan target, +26.7%)
    <br/>• Hold remaining 25% as long-term position (3+ year horizon)
    <br/><br/>
    <b>Scale-Up Triggers:</b>
    <br/>• Increase to 12% if Waymo valuation hits $100B (currently ~$45B)
    <br/>• Increase to 15% if Google Cloud sustains 30%+ growth for 3 consecutive quarters
    <br/>• Maximum position size: 15% of portfolio (concentration limit)
    """
    elements.append(Paragraph(risk_mgmt, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # FINAL VERDICT
    # =================================================================
    elements.append(Paragraph("Final Verdict & Action Plan", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    # Verdict Box
    verdict_data = [
        ['RECOMMENDATION', 'STRONG BUY'],
        ['Position Size', '74 shares = $22,477.50 (9% of $250K portfolio)'],
        ['Entry Price', '$303.75 (current market)'],
        ['12-Month Price Target', '$340 (median), $370+ (bull case)'],
        ['Expected Return', '+11.9% to +26.7%'],
        ['Risk Rating', 'MEDIUM'],
        ['Conviction Level', '9/10'],
        ['Stop Loss', '$258.19 (-15%)'],
    ]
    verdict_table = Table(verdict_data, colWidths=[2.2*inch, 3.8*inch])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), NAVY),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('BACKGROUND', (1, 0), (1, 0), GREEN),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1.5, DARK_GRAY),
    ]))
    elements.append(verdict_table)
    elements.append(Spacer(1, 0.2*inch))

    verdict_rationale = """
    <b>Why STRONG BUY:</b>
    <br/><br/>
    <b>Exceptional Strengths:</b>
    <br/>✓ AI Leadership: Gemini 3 outperforming rivals, 650M+ MAU and growing
    <br/>✓ Cloud Acceleration: 34% YoY growth, $155B backlog, enterprise AI wins
    <br/>✓ Waymo Inflection: Scaling to 1M rides/week, $100B valuation potential
    <br/>✓ Search Resilience: +14.5% growth despite AI chatbot competition
    <br/>✓ Risk-Adjusted Returns: Sharpe 1.64, Alpha +44.95% vs. SPY
    <br/>✓ Regulatory Clarity: September 2025 ruling rejected DOJ breakup
    <br/>✓ Valuation: Reasonable vs. growth, cheaper than MSFT/NVDA
    <br/><br/>
    <b>Manageable Risks:</b>
    <br/>• Antitrust resolved (for now), EU risks remain but manageable
    <br/>• AI competition intense but Gemini 3 benchmarks demonstrate competitiveness
    <br/>• Capex elevated but Cloud revenue growth validates ROI
    <br/>• Technical setup mixed but oversold = entry opportunity
    <br/><br/>
    <b>Why 9/10 (Not 10/10):</b>
    <br/>• Short-term technical weakness (MACD bearish) creates minor timing uncertainty
    <br/>• Capex intensity requires continued monitoring of Cloud ROI
    <br/>• AI competition could accelerate faster than expected
    <br/><br/>
    <b>Multi-Year Thesis:</b>
    <br/>GOOG is not just a 2026 play - it's a 3-5 year compounder. Waymo alone could be worth
    $100B+ (currently ~$45B), Google Cloud is tracking toward $100B+ annual revenue, and Gemini
    is positioning GOOG as the AI infrastructure layer for the next decade. The combination of
    defensive Search moat + explosive growth vectors creates asymmetric upside with manageable downside.
    """
    elements.append(Paragraph(verdict_rationale, styles['CustomBody']))
    elements.append(Spacer(1, 0.2*inch))

    # Action Checklist
    elements.append(Paragraph("Immediate Action Checklist", styles['SubHeader']))
    action_items = """
    <b>Execute Today:</b>
    <br/>☐ <b>Buy 74 shares of GOOG @ $303.75 = $22,477.50</b>
    <br/>☐ Set stop loss order at $258.19 (-15%)
    <br/>☐ Set price alerts: $340 (median target), $370 (HSBC target), $385 (JPM target)
    <br/>☐ Calendar quarterly earnings dates (track Cloud growth, Gemini metrics)
    <br/><br/>
    <b>Ongoing Monitoring (Monthly):</b>
    <br/>☐ Google Cloud revenue growth trends (target: sustain 30%+ YoY)
    <br/>☐ Gemini MAU metrics vs. ChatGPT (goal: reach 845M+ users)
    <br/>☐ Waymo expansion progress (ride volume, new city launches)
    <br/>☐ Analyst price target changes (consensus direction)
    <br/>☐ Technical indicators (watch for MACD bullish crossover)
    <br/><br/>
    <b>Risk Monitoring:</b>
    <br/>☐ EU antitrust developments (fines, operational restrictions)
    <br/>☐ AI competition (GPT-5 launch, Claude improvements, open-source models)
    <br/>☐ Capex efficiency (Cloud revenue growth vs. infrastructure spend)
    """
    elements.append(Paragraph(action_items, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # MARKET SENTIMENT & ANALYST CONSENSUS
    # =================================================================
    elements.append(Paragraph("Market Sentiment & Analyst Consensus", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    sentiment_text = """
    <b>Wall Street Consensus: Strong Buy (9.1/10)</b>
    <br/>• 37 analysts covering GOOG, median price target $340
    <br/>• Price target range: $185 (bear) to $386 (bull)
    <br/>• Recent upgrades: HSBC ($370), J.P. Morgan ($385), TD Cowen ($350)
    <br/><br/>
    <b>Key Institutional Themes:</b>
    <br/>1. <b>AI Infrastructure Play:</b> Goldman Sachs included GOOG in "Magnificent Seven" driving
    46% of S&P 500 earnings growth in 2026
    <br/>2. <b>Cloud Momentum:</b> BMO Capital citing 34% Cloud growth as key catalyst
    <br/>3. <b>Gemini Upside:</b> HSBC highlighting Gemini 3 competitive positioning
    <br/>4. <b>Waymo Breakout:</b> Morgan Stanley estimating $200B+ autonomous vehicle TAM by 2030
    <br/><br/>
    <b>Investor Sentiment Drivers:</b>
    <br/>• Positive: Regulatory clarity (September 2025 ruling), Cloud acceleration, Gemini 3 benchmarks
    <br/>• Concerns: Capex intensity, AI competition, EU investigations
    <br/>• Net Sentiment: <b>BULLISH</b> - fundamentals outweighing concerns
    """
    elements.append(Paragraph(sentiment_text, styles['CustomBody']))

    elements.append(PageBreak())

    # =================================================================
    # APPENDIX: DATA SOURCES
    # =================================================================
    elements.append(Paragraph("Appendix: Data Sources & Methodology", styles['SectionHeader']))
    elements.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=12))

    sources_text = """
    <b>Market Data Sources:</b>
    <br/>• Price data: Yahoo Finance (yfinance API) - EOD data through 2025-12-17
    <br/>• Analyst ratings: StockAnalysis.com, Bloomberg, TickerNerd
    <br/>• Company financials: Alphabet Q3 2025 earnings report
    <br/>• Industry research: Web search (December 2025) - AI trends, Cloud growth, Waymo expansion
    <br/><br/>
    <b>Analysis Tools:</b>
    <br/>• Risk Metrics CLI: 252-day lookback, benchmark = SPY
    <br/>  - VaR/CVaR: Historical simulation, 95% confidence level
    <br/>  - Sharpe/Sortino: Annualized returns vs. 4.5% risk-free rate
    <br/>  - Beta/Alpha: OLS regression vs. SPY
    <br/>• Momentum CLI: 90-day window, RSI/MACD/Stochastic/Williams %R/ROC
    <br/>• Volatility CLI: 90-day ATR, Bollinger Bands, Historical Volatility
    <br/><br/>
    <b>Research Sources:</b>
    <br/>• Alphabet investor relations (earnings calls, SEC filings)
    <br/>• Wall Street analyst reports (HSBC, J.P. Morgan, BMO, TD Cowen)
    <br/>• Industry publications (Bloomberg, Yahoo Finance, Benzinga)
    <br/>• Waymo funding/valuation: Bloomberg, Automotive Dive
    <br/>• Antitrust developments: DOJ filings, court rulings (September 2025)
    <br/>• AI competitive analysis: OpenAI, Anthropic, Meta benchmarks
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
    Alphabet (GOOG) is subject to technology sector risk, regulatory risk (antitrust, AI safety), competitive
    risk (AI model competition), execution risk (Cloud, Waymo scaling), and market volatility (32.76% annual
    volatility). Stock price movements can be significant and adverse.
    <br/><br/>
    The position sizing recommendations are based on a hypothetical $250,000 portfolio and assume specific
    risk tolerances. Your actual allocation should be determined in consultation with a qualified financial
    advisor who understands your complete financial situation, investment objectives, and risk tolerance.
    <br/><br/>
    Before making investment decisions, consult with qualified financial, tax, and legal advisors. This
    report should not be relied upon as the sole basis for investment decisions.
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
    print(f"📊 Pages: 8-10 page comprehensive analysis")
    print(f"🎯 Recommendation: STRONG BUY")
    print(f"💰 Position Size: 74 shares @ $303.75 = $22,477.50 (9% of $250K portfolio)")
    print(f"📈 Price Target: $340 (median), $370+ (bull case)")
    print(f"⚠️  Stop Loss: $258.19 (-15%)")

    return filename

if __name__ == "__main__":
    generate_goog_report()
