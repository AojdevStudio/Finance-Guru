#!/usr/bin/env python3
"""
Generate VRT (Vertiv Holdings) Analysis Report - 2026 Watchlist
Finance Guru Multi-Agent Analysis
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

# Output path
OUTPUT_PATH = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports/VRT-analysis-2025-12-18.pdf"

# Create PDF
doc = SimpleDocTemplate(OUTPUT_PATH, pagesize=letter,
                        rightMargin=0.75*inch, leftMargin=0.75*inch,
                        topMargin=0.75*inch, bottomMargin=0.75*inch)

# Container for elements
elements = []

# Styles
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#1a472a'),
    spaceAfter=30,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=16,
    textColor=colors.HexColor('#2d5f3d'),
    spaceAfter=12,
    spaceBefore=12,
    fontName='Helvetica-Bold'
)

subheading_style = ParagraphStyle(
    'CustomSubHeading',
    parent=styles['Heading3'],
    fontSize=13,
    textColor=colors.HexColor('#2d5f3d'),
    spaceAfter=8,
    spaceBefore=8,
    fontName='Helvetica-Bold'
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['BodyText'],
    fontSize=11,
    spaceAfter=6,
    leading=14
)

# Title Page
elements.append(Spacer(1, 1.5*inch))
elements.append(Paragraph("Finance Guru™", title_style))
elements.append(Paragraph("Multi-Agent Quantitative Analysis",
                         ParagraphStyle('subtitle', parent=body_style, fontSize=14, alignment=TA_CENTER)))
elements.append(Spacer(1, 0.5*inch))
elements.append(Paragraph("VRT (Vertiv Holdings)",
                         ParagraphStyle('ticker', parent=heading_style, fontSize=20, alignment=TA_CENTER)))
elements.append(Paragraph("2026 Watchlist Comprehensive Analysis",
                         ParagraphStyle('analysis_type', parent=body_style, fontSize=12, alignment=TA_CENTER)))
elements.append(Spacer(1, 0.5*inch))
elements.append(Paragraph(f"Report Date: December 18, 2025",
                         ParagraphStyle('date', parent=body_style, fontSize=11, alignment=TA_CENTER)))
elements.append(Paragraph(f"Current Price: $154.39 (+3.04%)",
                         ParagraphStyle('price', parent=body_style, fontSize=11, alignment=TA_CENTER)))
elements.append(PageBreak())

# Executive Summary
elements.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
summary_text = """
<b>Investment Thesis:</b> Vertiv Holdings (VRT) is a premier AI infrastructure play positioned at the nexus
of two critical bottlenecks in the AI era: heat and power management. With a record $9.5 billion backlog
and 52% YTD gains in 2025, VRT has transformed from a legacy industrial player into a high-growth tech powerhouse.
<br/><br/>
<b>Key Highlights:</b><br/>
• Revenue: $2.676B Q3 2025 (+29% YoY) | 2026E: $12.4B<br/>
• Organic Orders: +60% YoY with 1.4x book-to-bill ratio<br/>
• Market Position: Within 0.5% of market leader Schneider Electric in data center power<br/>
• Strategic Advantages: Liquid cooling leadership (45x capacity expansion), 800 VDC power portfolio for 2027 NVIDIA Rubin platforms<br/>
• Risk-Adjusted Returns: Alpha of +11.90% vs SPY, Beta 2.27 (high-beta aggressive growth)<br/>
<br/>
<b>2026 Outlook:</b> Wall Street consensus projects 15-20% revenue growth with EPS of $5.29. Analysts
identify 2026 as "Mass Liquid Cooling Adoption" year where direct liquid cooling (DLC) becomes default
for 50%+ of new data center builds.
"""
elements.append(Paragraph(summary_text, body_style))
elements.append(Spacer(1, 0.3*inch))

# Rating Box
rating_data = [
    ["PHASE 3: STRATEGY RECOMMENDATION", ""],
    ["Investment Thesis Rating", "8.5/10"],
    ["Risk-Adjusted Attractiveness", "7.0/10"],
    ["2026 Growth Catalyst Strength", "9.0/10"],
    ["Portfolio Fit (Tech-Heavy)", "6.5/10"],
    ["", ""],
    ["FINAL VERDICT", "CONDITIONAL BUY"],
]
rating_table = Table(rating_data, colWidths=[4*inch, 2*inch])
rating_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5f3d')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
    ('GRID', (0, 0), (-1, -2), 1, colors.black),
    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ffd700')),
    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ('FONTSIZE', (0, -1), (-1, -1), 14),
    ('ALIGN', (0, -1), (-1, -1), 'CENTER'),
]))
elements.append(rating_table)
elements.append(PageBreak())

# PHASE 1: MARKET RESEARCH
elements.append(Paragraph("PHASE 1: MARKET RESEARCH", heading_style))
elements.append(Paragraph("Agent: Dr. Aleksandr Petrov, Market Research Specialist", subheading_style))

elements.append(Paragraph("<b>Company Overview</b>", subheading_style))
company_text = """
Vertiv Holdings Co. (NYSE: VRT) designs, manufactures, and services critical digital infrastructure
technologies for data centers, communication networks, and commercial/industrial facilities. The company's
portfolio spans three core segments:<br/>
• <b>Thermal Management:</b> Air and liquid cooling systems, precision air handlers, heat rejection equipment<br/>
• <b>Power Management:</b> UPS systems, PDUs, switchgear, busway, DC power systems<br/>
• <b>Integrated Solutions:</b> Modular prefabricated data centers, edge computing infrastructure<br/>
<br/>
Headquartered in Columbus, Ohio, Vertiv operates globally with ~30,000 employees and serves hyperscalers
(Meta, Google, Microsoft), colocation providers, and enterprise clients.
"""
elements.append(Paragraph(company_text, body_style))
elements.append(Spacer(1, 0.2*inch))

elements.append(Paragraph("<b>AI Infrastructure Tailwinds</b>", subheading_style))
ai_text = """
<b>Structural Trend:</b> AI computing drives higher rack densities, requiring sophisticated power delivery
and thermal management. Traditional air cooling maxes out at ~20-30 kW/rack; AI workloads (especially GPU
clusters) demand 60-100+ kW/rack, necessitating liquid cooling solutions.<br/><br/>

<b>Strategic Positioning:</b><br/>
• <b>Liquid Cooling Leadership:</b> 45x manufacturing capacity expansion in 2024; DLC systems ship to
hyperscalers in volume<br/>
• <b>800 VDC Power Architecture:</b> Next-gen power distribution planned for H2 2026, aligned with
NVIDIA Rubin Ultra 2027 rollout (10-15% efficiency gain vs traditional AC systems)<br/>
• <b>PurgeRite Acquisition ($1.0B):</b> Expands fluid management services for high-density computing,
critical for liquid cooling deployments<br/>
• <b>Caterpillar Partnership (Nov 2025):</b> Co-develop integrated solutions for AI-heavy data centers,
combining Vertiv cooling/power with CAT backup generation<br/>
<br/>
<b>2026 Catalyst - Mass Liquid Cooling Adoption:</b> Industry analysts project DLC becomes standard for
50%+ of new AI data center builds in 2026, up from ~15-20% in 2025. Vertiv's early-mover advantage in
liquid cooling positions it to capture outsized market share.
"""
elements.append(Paragraph(ai_text, body_style))
elements.append(Spacer(1, 0.2*inch))

elements.append(Paragraph("<b>Competitive Landscape</b>", subheading_style))
competitive_text = """
<b>Market Share Dynamics:</b><br/>
• <b>Data Center Power:</b> Schneider Electric leads, Vertiv #2 (within 0.5% of leader), Eaton #3.
Top 5 players hold ~41-43% combined share.<br/>
• <b>Data Center Cooling:</b> Vertiv leads with strongest product footprint and recent market share gains.
Schneider, Johnson Controls, and Rittal Systems are key competitors.<br/>
• <b>Liquid Cooling Niche:</b> Vertiv more agile than Schneider in high-density liquid cooling deployment;
significant shipments in Q4 2023 and aggressive capacity expansion.<br/>
<br/>
<b>Competitive Threats:</b><br/>
• <b>Schneider Electric:</b> Acquired Motivair ($850M) to bolster liquid cooling; launched digital twin
capabilities with NVIDIA Omniverse<br/>
• <b>Eaton & ABB:</b> Leverage utility-scale credentials and embedded install bases<br/>
• <b>Price War Risk:</b> Intense competition could compress margins if AI capex slows<br/>
<br/>
<b>Vertiv's Edge:</b> Comprehensive portfolio (power + cooling + racks + management software) vs niche
players; faster innovation cycle in liquid cooling vs legacy giants.
"""
elements.append(Paragraph(competitive_text, body_style))
elements.append(PageBreak())

# PHASE 2: QUANTITATIVE ANALYSIS
elements.append(Paragraph("PHASE 2: QUANTITATIVE ANALYSIS", heading_style))
elements.append(Paragraph("Agent: Dr. Priya Desai, Quantitative Research Director", subheading_style))

elements.append(Paragraph("<b>Risk Metrics (252-Day Analysis vs SPY)</b>", subheading_style))
risk_data = [
    ["Metric", "VRT", "Interpretation"],
    ["Value at Risk (95%)", "-6.52%", "95% of days, losses won't exceed 6.52%"],
    ["CVaR (95%)", "-10.75%", "When losses exceed VaR, avg loss is 10.75%"],
    ["Sharpe Ratio", "0.45", "Poor risk-adjusted returns (< 1.0)"],
    ["Sortino Ratio", "0.54", "Better downside-adjusted performance"],
    ["Maximum Drawdown", "-61.28%", "Severe peak-to-trough decline observed"],
    ["Calmar Ratio", "0.58", "Return per unit of max drawdown"],
    ["Annual Volatility", "69.06%", "High volatility (40-80% range)"],
    ["Beta (vs SPY)", "2.27", "High systematic risk - aggressive growth"],
    ["Alpha (vs SPY)", "+11.90%", "Outperforming benchmark by 11.90% annually"],
]
risk_table = Table(risk_data, colWidths=[2*inch, 1.5*inch, 3*inch])
risk_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5f3d')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
]))
elements.append(risk_table)
elements.append(Spacer(1, 0.2*inch))

risk_commentary = """
<b>Risk Profile Assessment:</b> VRT exhibits high-beta characteristics (2.27) consistent with aggressive
growth stocks in volatile sectors. The 69% annual volatility and -61% max drawdown reflect significant
historical price swings, typical of stocks that experienced COVID-era disruption and subsequent recovery.
Strong alpha generation (+11.90%) demonstrates fundamental outperformance, but poor Sharpe ratio (0.45)
indicates this comes at high volatility cost. Suitable for aggressive risk tolerance only.
"""
elements.append(Paragraph(risk_commentary, body_style))
elements.append(Spacer(1, 0.3*inch))

elements.append(Paragraph("<b>Momentum Analysis (90-Day Window)</b>", subheading_style))
momentum_data = [
    ["Indicator", "Value", "Signal", "Interpretation"],
    ["RSI", "33.68", "NEUTRAL", "No extreme overbought/oversold condition"],
    ["MACD", "-3.32", "BEARISH", "MACD below signal line (downward momentum)"],
    ["Stochastic %K", "4.80", "OVERSOLD", "%K < 20, potential reversal up"],
    ["Williams %R", "-95.20", "OVERSOLD", "%R < -80, potential buy signal"],
    ["ROC (90-day)", "-16.40%", "BEARISH", "Negative momentum (16.40% loss)"],
    ["Confluence", "2/5 Bullish", "MIXED", "No clear directional consensus"],
]
momentum_table = Table(momentum_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 2.8*inch])
momentum_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5f3d')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
]))
elements.append(momentum_table)
elements.append(Spacer(1, 0.2*inch))

momentum_commentary = """
<b>Momentum Signal Interpretation:</b> Mixed signals with a slight oversold tilt. Stochastic and Williams %R
both flash oversold warnings (potential reversal up), while MACD and ROC show bearish momentum. RSI at 33.68
is neutral territory. This suggests recent price weakness (down 16.40% over 90 days) may be approaching
exhaustion, but trend reversal not yet confirmed. Technical setup favors patient accumulation near support
levels rather than aggressive buying into downtrend.
"""
elements.append(Paragraph(momentum_commentary, body_style))
elements.append(Spacer(1, 0.3*inch))

elements.append(Paragraph("<b>Volatility Regime Analysis</b>", subheading_style))
volatility_data = [
    ["Metric", "Value", "Guidance"],
    ["Volatility Regime", "HIGH", "Reduce position sizes (2-5% of portfolio)"],
    ["ATR (Absolute)", "$10.42", "Average daily price swing"],
    ["ATR (%)", "6.75%", "Significant intraday movement"],
    ["Suggested Stop Loss", "2x ATR = $20.83", "Risk management threshold"],
    ["Annual Volatility", "62.99%", "High but declining from 69% peak"],
    ["Bollinger Band %B", "0.123", "Price near lower band (support)"],
    ["BB Bandwidth", "26.60%", "Wide bands reflect high volatility"],
]
volatility_table = Table(volatility_data, colWidths=[2.5*inch, 1.5*inch, 3*inch])
volatility_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5f3d')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
]))
elements.append(volatility_table)
elements.append(Spacer(1, 0.2*inch))

volatility_commentary = """
<b>Volatility-Based Position Sizing:</b> HIGH regime dictates conservative sizing (2-5% of portfolio max).
ATR of $10.42 (6.75%) means daily swings of $10+ are normal—unsuitable for tight stop-losses. Bollinger %B
at 0.123 indicates price near lower band, suggesting technical support. Wide 26.60% bandwidth confirms
elevated uncertainty. Recommend using 2x ATR stop ($20.83 from entry) to avoid premature shakeouts.
"""
elements.append(Paragraph(volatility_commentary, body_style))
elements.append(PageBreak())

elements.append(Paragraph("<b>Portfolio Correlation Analysis (252-Day)</b>", subheading_style))
corr_data = [
    ["Asset Pair", "Correlation", "Strength", "Implication"],
    ["VRT / NVDA", "+0.766", "VERY HIGH", "Strong co-movement with AI chip leader"],
    ["VRT / VOO", "+0.648", "HIGH", "Significant market beta exposure"],
    ["VRT / PLTR", "+0.508", "MODERATE", "Some overlap in AI infrastructure theme"],
    ["VRT / TSLA", "+0.418", "MODERATE", "Lower correlation - diversification benefit"],
]
corr_table = Table(corr_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 3*inch])
corr_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5f3d')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
]))
elements.append(corr_table)
elements.append(Spacer(1, 0.2*inch))

correlation_commentary = """
<b>Portfolio Fit Assessment:</b> Diversification score of 0.402 (GOOD) overall, but VRT adds moderate
concentration risk to existing tech-heavy portfolio. Very high correlation with NVDA (+0.766) means VRT
and NVDA will often move together, limiting diversification benefit. High VOO correlation (+0.648) indicates
VRT won't protect in broad market downturns. Moderate PLTR correlation (+0.508) suggests some AI thematic
overlap. Lower TSLA correlation (+0.418) is positive.<br/><br/>

<b>Recommendation:</b> VRT increases portfolio's AI infrastructure concentration. If adding VRT, consider
reducing NVDA weight or pairing with uncorrelated defensive positions (utilities, consumer staples) to
maintain overall portfolio balance.
"""
elements.append(Paragraph(correlation_commentary, body_style))
elements.append(PageBreak())

# PHASE 3: STRATEGY RECOMMENDATION
elements.append(Paragraph("PHASE 3: STRATEGY RECOMMENDATION", heading_style))
elements.append(Paragraph("Agent: Elena Rodriguez-Park, Portfolio Strategy Director", subheading_style))

elements.append(Paragraph("<b>Investment Thesis Summary</b>", subheading_style))
thesis_text = """
<b>BULL CASE (Weighted 60%):</b><br/>
1. <b>Structural AI Tailwind:</b> Mass liquid cooling adoption in 2026 creates multi-year growth runway.
Vertiv's 45x capacity expansion and early mover advantage position it to capture outsized share.<br/>
2. <b>Pricing Power:</b> Record $9.5B backlog (1.4x book-to-bill) demonstrates pricing power in supply-constrained
market. 60% YoY organic order growth shows robust demand visibility into 2026.<br/>
3. <b>Technology Moats:</b> 800 VDC power systems (2026) aligned with NVIDIA Rubin Ultra (2027) create
sticky customer relationships. PurgeRite acquisition adds fluid management IP.<br/>
4. <b>Market Share Gains:</b> Closing gap with Schneider Electric (within 0.5%) while maintaining superior
liquid cooling agility. Caterpillar partnership expands addressable market.<br/>
5. <b>Strong Alpha Generation:</b> +11.90% annual alpha vs SPY demonstrates fundamental outperformance
despite high volatility.<br/>
<br/>
<b>BEAR CASE (Weighted 40%):</b><br/>
1. <b>Valuation Risk:</b> Trading at 30-35x 2026 EPS—"priced for perfection" by traditional metrics.
Limited margin of safety if AI capex slows or competition intensifies.<br/>
2. <b>Execution Risk:</b> Rapid capacity expansion (45x in liquid cooling) carries operational risk.
Supply chain complexity and quality control challenges in scaling phase.<br/>
3. <b>Competition Intensifying:</b> Schneider ($850M Motivair acquisition), Eaton, and ABB aggressively
targeting same AI infrastructure budgets. Price war risk if market share battles escalate.<br/>
4. <b>High Volatility/Drawdown:</b> 69% annual volatility and -61% max drawdown unsuitable for conservative
investors. Poor Sharpe ratio (0.45) means returns come at high volatility cost.<br/>
5. <b>Momentum Weakness:</b> Recent 16.40% pullback (90-day ROC) and bearish MACD suggest near-term headwinds.
Technical setup not yet confirmed for reversal.<br/>
6. <b>Portfolio Concentration:</b> +0.766 correlation with NVDA increases AI infrastructure concentration risk
in already tech-heavy portfolio.
"""
elements.append(Paragraph(thesis_text, body_style))
elements.append(Spacer(1, 0.3*inch))

elements.append(Paragraph("<b>Position Sizing & Entry Strategy</b>", subheading_style))
sizing_text = """
<b>Recommended Position Size:</b> 3-5% of portfolio<br/>
• Baseline: 3% (conservative positioning given HIGH volatility regime)<br/>
• Aggressive: 5% max (only if comfortable with potential 20-30% drawdowns)<br/>
• Rationale: High volatility (ATR 6.75%) and -61% historical max drawdown require defensive sizing<br/>
<br/>
<b>Entry Strategy (Tiered Accumulation):</b><br/>
• <b>Tranche 1 (40% of position):</b> Enter at current levels ($150-155) - Oversold technicals (Stochastic
4.80, Williams %R -95.20) suggest potential near-term bounce<br/>
• <b>Tranche 2 (30% of position):</b> Add on pullback to $140-145 (Bollinger lower band support zone)<br/>
• <b>Tranche 3 (30% of position):</b> Reserve for deeper correction to $120-130 (prior consolidation support)
OR momentum confirmation above $165 (MACD crossover bullish)<br/>
<br/>
<b>Avoid These Entry Points:</b><br/>
• Chasing above $170+ without pullback (reduces margin of safety)<br/>
• Entering full position at once in HIGH volatility regime (increased downside risk)<br/>
<br/>
<b>Timeline:</b> 3-6 month accumulation window (Q1-Q2 2026). Allows capturing weakness and building position
ahead of "Mass Liquid Cooling Adoption" catalyst in H2 2026.
"""
elements.append(Paragraph(sizing_text, body_style))
elements.append(Spacer(1, 0.3*inch))

elements.append(Paragraph("<b>Risk Management Framework</b>", subheading_style))
risk_mgmt_text = """
<b>Stop Loss Strategy:</b><br/>
• <b>Technical Stop:</b> 2x ATR = $20.83 below entry (accounts for normal volatility)<br/>
• <b>Hard Stop:</b> -25% from average cost basis (max acceptable loss given aggressive risk profile)<br/>
• Example: If avg entry $150, hard stop at $112.50<br/>
<br/>
<b>Profit Taking Levels:</b><br/>
• <b>Target 1 (+30%):</b> $195-200 - Take 25% of position, lock in gains<br/>
• <b>Target 2 (+60%):</b> $240-250 - Take another 35%, let 40% run<br/>
• <b>Target 3 (+100%):</b> $300+ - Trail stop at 2x ATR to capture upside<br/>
<br/>
<b>Portfolio Rebalancing Triggers:</b><br/>
• If VRT exceeds 8% of portfolio (due to appreciation), trim back to 5%<br/>
• If VRT/NVDA combined exceeds 25%, reduce one or both to manage AI infrastructure concentration<br/>
• Monitor correlation quarterly - if VRT/NVDA correlation rises above 0.85, consider rotation<br/>
<br/>
<b>Re-evaluation Criteria (Sell Signals):</b><br/>
1. AI capex slowdown: Hyperscalers (MSFT, GOOGL, META) reduce data center spending guidance<br/>
2. Market share losses: Schneider or Eaton gain >3% share in liquid cooling segment<br/>
3. Margin compression: Gross margins decline below 30% for 2 consecutive quarters<br/>
4. Backlog deterioration: Book-to-bill falls below 1.0x for 2+ quarters<br/>
5. Technical breakdown: Close below $120 on weekly chart (invalidates bullish structure)
"""
elements.append(Paragraph(risk_mgmt_text, body_style))
elements.append(PageBreak())

elements.append(Paragraph("<b>2026 Catalyst Timeline</b>", subheading_style))
catalyst_text = """
<b>Q1 2026 (Jan-Mar):</b><br/>
• Q4 2025 earnings report (late Jan/early Feb) - Key metric: Backlog growth and liquid cooling orders<br/>
• Potential S&P 500 inclusion announcement (failed Dec 2025, could retry Q1 2026)<br/>
• 800 VDC power system product launch announcements<br/>
<br/>
<b>Q2 2026 (Apr-Jun):</b><br/>
• Q1 2026 earnings - Watch for 2026 guidance raise on liquid cooling demand<br/>
• Caterpillar partnership first customer wins announced<br/>
• Industry conferences (DCD, 7x24 Exchange) showcasing liquid cooling deployments<br/>
<br/>
<b>Q3 2026 (Jul-Sep):</b><br/>
• H2 2026: 800 VDC power portfolio release (aligned with NVIDIA Rubin Ultra prep)<br/>
• Q2 earnings - Evidence of "Mass Liquid Cooling Adoption" in order mix (targeting 50%+ DLC penetration)<br/>
• Hyperscaler contract announcements (META, GOOGL, MSFT data center projects)<br/>
<br/>
<b>Q4 2026 (Oct-Dec):</b><br/>
• Q3 earnings - Validation of 2026 growth thesis (15-20% revenue growth, EPS $5.25+)<br/>
• 2027 guidance: Look for continued high teens revenue growth on AI infrastructure buildout<br/>
• Year-end portfolio review: Assess if thesis played out, decide on 2027 allocation
"""
elements.append(Paragraph(catalyst_text, body_style))
elements.append(Spacer(1, 0.3*inch))

elements.append(Paragraph("<b>Scenario Analysis</b>", subheading_style))
scenario_data = [
    ["Scenario", "Probability", "Price Target", "Return", "Key Drivers"],
    ["Bull Case\n(Mass Adoption)", "35%", "$280-320", "+80-110%",
     "DLC adoption >60%, market share gains,\nNVIDIA partnership momentum"],
    ["Base Case\n(Steady Growth)", "45%", "$200-240", "+30-55%",
     "DLC adoption ~50%, stable margins,\n15-20% revenue growth"],
    ["Bear Case\n(Slowdown)", "15%", "$100-120", "-20-35%",
     "AI capex pullback, margin compression,\ncompetitive losses"],
    ["Worst Case\n(Recession)", "5%", "$60-80", "-50-60%",
     "Macro recession, data center freeze,\nhigh-beta selloff"],
]
scenario_table = Table(scenario_data, colWidths=[1.3*inch, 1*inch, 1*inch, 1*inch, 2.7*inch])
scenario_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5f3d')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
]))
elements.append(scenario_table)
elements.append(Spacer(1, 0.2*inch))

scenario_commentary = """
<b>Expected Value Calculation:</b><br/>
(0.35 × 95%) + (0.45 × 42.5%) + (0.15 × -27.5%) + (0.05 × -55%) = <b>+29.5% expected return</b><br/>
<br/>
<b>Risk-Reward:</b> Positive skew favors upside. Base case (+30-55%) carries 45% probability, while severe
downside scenarios (Bear + Worst = 20% combined) are lower probability. However, high volatility (69% annual)
means path to gains will be turbulent. Suitable for investors comfortable with 20-30% interim drawdowns.
"""
elements.append(Paragraph(scenario_commentary, body_style))
elements.append(PageBreak())

# FINAL VERDICT
elements.append(Paragraph("FINAL VERDICT & RATING", heading_style))

verdict_text = """
<b><font size=14 color='#d4af37'>CONDITIONAL BUY - 7.5/10</font></b><br/>
<br/>
<b>Recommendation:</b> Initiate 3-5% position via tiered accumulation over Q1-Q2 2026, contingent on:<br/>
1. Confirmation of "Mass Liquid Cooling Adoption" trend in Q4 2025 earnings (late Jan 2026)<br/>
2. Maintenance of >1.0x book-to-bill ratio and backlog growth >$10B<br/>
3. No evidence of AI capex slowdown from hyperscalers in Q1 earnings season<br/>
<br/>
<b>Best For:</b> Aggressive growth investors comfortable with high volatility (69% annual) and -60% max drawdown
potential. Strong conviction required in multi-year AI infrastructure buildout thesis.<br/>
<br/>
<b>Not Suitable For:</b> Conservative investors, retirees, or those with <3 year time horizon. High correlation
with NVDA (+0.766) makes this unsuitable for portfolios already overweight AI semiconductors.<br/>
<br/>
<b>Key Strengths:</b><br/>
• Unparalleled positioning at AI infrastructure chokepoint (heat + power)<br/>
• Strong alpha generation (+11.90% vs SPY) demonstrates fundamental edge<br/>
• Record backlog ($9.5B) and 60% order growth provide 2026 visibility<br/>
• Technology moats (800 VDC, liquid cooling IP) create customer stickiness<br/>
• Market share gains trajectory vs market leader Schneider Electric<br/>
<br/>
<b>Key Risks:</b><br/>
• Valuation stretched (30-35x 2026 EPS) - priced for perfection<br/>
• Execution risk in rapid capacity scaling (45x expansion)<br/>
• Intensifying competition (Schneider, Eaton, ABB) could pressure margins<br/>
• High volatility/drawdown profile (-61% max DD) unsuitable for weak hands<br/>
• Portfolio concentration risk with NVDA (adds AI infrastructure overlap)<br/>
<br/>
<b>Bottom Line:</b> VRT is a high-conviction AI infrastructure play with strong fundamental thesis, but
valuation and volatility demand disciplined entry strategy and tight risk management. The "Mass Liquid
Cooling Adoption" catalyst for 2026 provides compelling upside case, but success is NOT guaranteed.
Recommend phased accumulation with 3-5% max allocation, hard stops at -25%, and quarterly re-evaluation
of thesis validity.<br/>
<br/>
<b>Next Steps:</b><br/>
1. Monitor Q4 2025 earnings (late Jan 2026) for backlog and liquid cooling order trends<br/>
2. Begin Tranche 1 entry (40% of position) if earnings confirm thesis<br/>
3. Set calendar reminders for quarterly earnings and catalyst checkpoints<br/>
4. Review portfolio correlation monthly - adjust if VRT+NVDA exceeds 25% combined weight
"""
elements.append(Paragraph(verdict_text, body_style))
elements.append(PageBreak())

# DISCLAIMERS
elements.append(Paragraph("IMPORTANT DISCLAIMERS", heading_style))
disclaimer_text = """
<b>Educational Purpose Only:</b> This report is prepared by Finance Guru™ for educational and informational
purposes only for Ossie's private family office. This analysis is NOT investment advice, and should not be
construed as a recommendation to buy, sell, or hold any security.<br/>
<br/>
<b>Not Investment Advice:</b> The information contained in this report does not constitute investment advice,
financial advice, trading advice, or any other sort of advice. You should not treat any of the report's content
as such. Finance Guru™ does not recommend that any security should be bought, sold, or held by you. Conduct
your own due diligence and consult a licensed financial advisor before making any investment decisions.<br/>
<br/>
<b>Risk Disclosure:</b> All investments involve risk, including the potential loss of principal. Past performance
does not guarantee future results. The analysis presented here is based on historical data, market research,
and quantitative modeling, which may not accurately predict future outcomes. Market conditions can change
rapidly, rendering any analysis obsolete.<br/>
<br/>
<b>Consult Professionals:</b> Before making any investment decision, you should consult with qualified financial,
legal, and tax professionals who can evaluate your specific circumstances, risk tolerance, and investment
objectives.<br/>
<br/>
<b>Data Sources:</b> Market data sourced from yfinance (Yahoo Finance end-of-day prices). Company research
compiled from publicly available sources including financial news sites, analyst reports, and company filings.
Finance Guru™ makes no guarantees regarding the accuracy, completeness, or timeliness of this information.<br/>
<br/>
<b>Quantitative Models:</b> Risk metrics, momentum indicators, volatility analysis, and correlation calculations
are generated using Finance Guru™'s proprietary Python-based analytical tools. Model outputs are dependent on
input data quality and historical patterns, which may not repeat in the future.<br/>
<br/>
<b>No Guarantees:</b> Finance Guru™ makes no representations or warranties regarding the accuracy of this
analysis or the likelihood of any projected outcomes. Investment results will vary, and losses may occur.<br/>
<br/>
<b>Personal Responsibility:</b> You are solely responsible for your investment decisions and their outcomes.
By reviewing this report, you acknowledge that you understand these risks and will not hold Finance Guru™
or its creators liable for any losses incurred.<br/>
<br/>
<b>Report Date:</b> December 18, 2025. Market conditions and company circumstances may have changed since
this report was prepared. Always verify current data before making investment decisions.
"""
elements.append(Paragraph(disclaimer_text, body_style))
elements.append(Spacer(1, 0.5*inch))

# Sources
elements.append(Paragraph("SOURCES & CITATIONS", heading_style))
sources_text = """
<b>Market Research Sources:</b><br/>
• TS2 Space: "Vertiv (VRT) Stock News Today (Dec. 18, 2025): Why Shares Are Moving, Wall Street Forecasts,
and the 2026 Outlook"<br/>
• TS2 Space: "Vertiv (VRT) Stock News Today, Dec. 15, 2025: AI Data Center Cooling Tailwinds, Analyst
Price Targets, and the 2026 Outlook"<br/>
• Financial Content: "The New Architect of Silicon Valley: Vertiv's Cooling Dominance Propels Stock
Toward 2026 Highs"<br/>
• The Motley Fool: "Is This Ohio-Based Company Poised for Market Gains in AI/Data Center Infrastructure?"<br/>
• Markets and Markets: "Top Companies in Data Center Power Market" and "Data Center Cooling Market Size
& Share Analysis"<br/>
• Fierce Network: "Snapshot: what's happening in the data center infrastructure market"<br/>
<br/>
<b>Quantitative Data Sources:</b><br/>
• Market data: yfinance (Yahoo Finance) - End-of-day prices through December 17, 2025<br/>
• Risk metrics: Finance Guru™ risk_metrics_cli.py (252-day analysis vs SPY)<br/>
• Momentum analysis: Finance Guru™ momentum_cli.py (90-day window)<br/>
• Volatility analysis: Finance Guru™ volatility_cli.py (90-day regime assessment)<br/>
• Correlation matrix: Finance Guru™ correlation_cli.py (252-day analysis vs PLTR, TSLA, NVDA, VOO)<br/>
<br/>
<b>Company Information:</b><br/>
• Vertiv Holdings Co. public filings and investor relations materials<br/>
• Industry analyst reports and consensus estimates compiled from public sources<br/>
<br/>
<b>Report Generation:</b><br/>
• Finance Guru™ Multi-Agent System v2.0.0<br/>
• Agent Framework: BMAD-CORE™ v6.0.0<br/>
• Report compiled: December 18, 2025
"""
elements.append(Paragraph(sources_text, body_style))

# Build PDF
doc.build(elements)

print("=" * 70)
print("✅ VRT ANALYSIS REPORT GENERATED")
print("=" * 70)
print(f"📄 Output: {OUTPUT_PATH}")
print(f"📅 Report Date: December 18, 2025")
print(f"🎯 Ticker: VRT (Vertiv Holdings)")
print(f"💰 Current Price: $154.39 (+3.04%)")
print(f"📊 Final Verdict: CONDITIONAL BUY - 7.5/10")
print(f"📈 Position Size: 3-5% of portfolio")
print("=" * 70)
