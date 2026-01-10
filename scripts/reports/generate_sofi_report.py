#!/usr/bin/env python3
"""
SOFI Technologies Full Research Report Generator
Generates comprehensive PDF analysis report for SOFI stock
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime

def create_sofi_report():
    """Generate comprehensive SOFI analysis PDF report"""

    output_path = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports/SOFI-analysis-2025-12-18.pdf"
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)

    # Container for document elements
    elements = []
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

    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    subheader_style = ParagraphStyle(
        'CustomSubHeader',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        leading=14
    )

    # PAGE 1: HEADER & EXECUTIVE SUMMARY

    # Title
    elements.append(Paragraph("SOFI TECHNOLOGIES, INC.", title_style))
    elements.append(Paragraph("Investment Analysis Report",
                             ParagraphStyle('Subtitle', parent=body_style, fontSize=12, alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.2*inch))

    # Header table (VGT-style)
    header_data = [
        ['Analyst Team', 'Finance Guru Research Division'],
        ['Report Date', 'December 18, 2025'],
        ['Ticker', 'SOFI (NASDAQ)'],
        ['Current Price', '$26.29'],
        ['YTD Performance', '+86.06%'],
        ['52-Week Range', '$14.13 - $32.73']
    ]

    header_table = Table(header_data, colWidths=[2*inch, 4*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7'))
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.3*inch))

    # Verdict Box
    elements.append(Paragraph("INVESTMENT VERDICT", header_style))

    verdict_data = [
        ['RECOMMENDATION', 'HOLD / MODERATE BUY'],
        ['RATING', '7.5/10'],
        ['TARGET ALLOCATION', '2.0% - 3.0% of Portfolio'],
        ['RISK LEVEL', 'HIGH (Beta: 2.41, Vol: 64%)'],
        ['TIME HORIZON', '12-24 Months']
    ]

    verdict_table = Table(verdict_data, colWidths=[2*inch, 4*inch])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f8f5')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a5490')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#1a5490'))
    ]))
    elements.append(verdict_table)
    elements.append(Spacer(1, 0.2*inch))

    # Executive Summary
    elements.append(Paragraph("EXECUTIVE SUMMARY", header_style))

    exec_summary = """
    <b>Investment Thesis:</b> SoFi Technologies represents a compelling fintech growth story with strong fundamental
    execution, having achieved 8 consecutive quarters of GAAP profitability and 86% YTD returns. The company's national
    bank charter provides a sustainable competitive moat through low-cost deposit funding ($32.9B), while its
    diversified revenue streams (55% from financial services/tech platforms, 45% from lending) reduce concentration risk.
    <br/><br/>
    <b>Key Strengths:</b>
    • Exceptional member growth: 12.6M total members (+35% YoY), 18.6M products (+36% YoY)<br/>
    • Strong profitability metrics: Record Q3 2025 EBITDA of $277M, 38% revenue growth<br/>
    • Robust deposit base of $32.9B providing low-cost funding advantage<br/>
    • Strategic positioning in crypto/stablecoins with SoFi USD launch planned for 2026<br/>
    • Potential S&P 500 inclusion catalyst (per Truist analysis)
    <br/><br/>
    <b>Primary Concerns:</b>
    • Elevated volatility (64% annual) and high beta (2.41) create significant drawdown risk<br/>
    • Credit quality concerns: 330 bps net losses on $18B personal loan portfolio (Q1 2025)<br/>
    • Stretched valuation: Trading at premium to traditional banks with limited margin of safety<br/>
    • Recent $1.5B equity offering caused 7.3% stock decline, signaling dilution concerns<br/>
    • Regulatory uncertainty around crypto initiatives and AI deployments
    <br/><br/>
    <b>Position Context:</b> Current holding of 29 shares ($762.41 position value) represents minimal portfolio exposure.
    Given the high-risk/high-reward profile and strong YTD performance, we recommend a cautious approach: maintain
    current position without immediate additions, monitor Q4 2025 and Q1 2026 earnings for credit quality trends,
    and consider tactical additions only on significant pullbacks (15-20% from current levels).
    """

    elements.append(Paragraph(exec_summary, body_style))
    elements.append(PageBreak())

    # PAGE 2: QUANTITATIVE ANALYSIS

    elements.append(Paragraph("QUANTITATIVE RISK ANALYSIS", header_style))
    elements.append(Paragraph("252-Day Risk Metrics (vs SPY Benchmark)", subheader_style))

    risk_data = [
        ['Metric', 'Value', 'Interpretation'],
        ['Value at Risk (95%)', '-6.29%', 'Daily loss limit (95% of days)'],
        ['Conditional VaR (95%)', '-9.21%', 'Average loss when VaR exceeded'],
        ['Sharpe Ratio', '0.98', 'POOR - Below 1.0 threshold'],
        ['Sortino Ratio', '1.47', 'Better downside-adjusted returns'],
        ['Maximum Drawdown', '-47.31%', 'Severe peak-to-trough decline'],
        ['Calmar Ratio', '1.43', 'Return/drawdown tradeoff'],
        ['Annual Volatility', '64.31%', 'HIGH - Significant price swings'],
        ['Beta (vs SPY)', '2.41', 'HIGH - Amplifies market moves 2.4x'],
        ['Alpha (vs SPY)', '+42.61%', 'STRONG - Outperformance driver']
    ]

    risk_table = Table(risk_data, colWidths=[2*inch, 1.2*inch, 2.8*inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    elements.append(risk_table)
    elements.append(Spacer(1, 0.2*inch))

    # Momentum Analysis
    elements.append(Paragraph("MOMENTUM INDICATORS (90-Day)", subheader_style))

    momentum_data = [
        ['Indicator', 'Value', 'Signal', 'Interpretation'],
        ['RSI (14-day)', '39.82', 'Neutral', 'No extreme overbought/oversold'],
        ['MACD', '-0.56', 'Bearish', 'Below signal line (-0.29)'],
        ['MACD Histogram', '-0.27', 'Bearish', 'Downward momentum'],
        ['Stochastic %K', '1.90', 'OVERSOLD', 'Potential reversal upward'],
        ['Stochastic %D', '6.95', 'OVERSOLD', 'Confirming oversold condition'],
        ['Williams %R', '-98.10', 'OVERSOLD', 'Extreme oversold (<-80)'],
        ['Rate of Change', '-12.95%', 'Bearish', 'Recent price decline'],
        ['Confluence Score', '2/5 Bullish', 'MIXED', 'No clear directional bias']
    ]

    momentum_table = Table(momentum_data, colWidths=[1.8*inch, 1*inch, 1.2*inch, 2*inch])
    momentum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    elements.append(momentum_table)
    elements.append(Spacer(1, 0.2*inch))

    # Volatility Regime
    elements.append(Paragraph("VOLATILITY REGIME ANALYSIS (90-Day)", subheader_style))

    vol_data = [
        ['Metric', 'Value', 'Implication'],
        ['Volatility Regime', 'HIGH', 'Reduce position sizes (2-5% portfolio)'],
        ['ATR (14-day)', '$1.41 (5.35%)', 'Suggested stop: 2x ATR = $2.81'],
        ['Annual Volatility', '62.48%', 'Consistent with 252-day analysis'],
        ['Bollinger Upper', '$30.45', 'Resistance level'],
        ['Bollinger Middle', '$27.44', 'Near current price'],
        ['Bollinger Lower', '$24.44', 'Support level'],
        ['%B Position', '0.308', 'Lower third of band range'],
        ['Bandwidth', '21.90%', 'Normal volatility expansion']
    ]

    vol_table = Table(vol_data, colWidths=[2*inch, 1.8*inch, 2.2*inch])
    vol_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    elements.append(vol_table)
    elements.append(PageBreak())

    # PAGE 3: COMPANY OVERVIEW & BUSINESS MODEL

    elements.append(Paragraph("COMPANY OVERVIEW", header_style))

    company_overview = """
    <b>About SoFi Technologies:</b>
    <br/><br/>
    SoFi Technologies, Inc. is a pioneering American financial technology company founded in 2011 by Stanford University
    students who identified an opportunity to disrupt the student loan market. The company has evolved from a
    student loan refinancing startup into a comprehensive digital banking platform serving 12.6 million members
    (as of Q3 2025).
    <br/><br/>
    <b>Business Model - Three Core Divisions:</b>
    <br/><br/>
    <b>1. Lending Division (45% of Revenue):</b><br/>
    • Student loan refinancing (highest originations since 2021: $1.3B in Q4 2024, +71% YoY)<br/>
    • Personal loans ($18B portfolio with 330 bps net loss rate in Q1 2025)<br/>
    • Mortgages and home equity solutions<br/>
    • Revenue from net interest, securitization sales, and whole loan sales
    <br/><br/>
    <b>2. Technology Platform Division:</b><br/>
    • <b>Galileo Financial Technologies</b> (acquired 2020 for $1.2B): Banking-as-a-Service provider with 168M
    enabled accounts globally by Q4 2024<br/>
    • <b>Technisys</b> (acquired 2022 for $1.1B): Digital banking infrastructure<br/>
    • Platform access and card management services via APIs<br/>
    • Enables SoFi to offer white-label banking services to other fintechs
    <br/><br/>
    <b>3. Financial Services Division (Combined with Tech = 55% of Revenue):</b><br/>
    • <b>SoFi Money:</b> FDIC-insured checking/savings ($32.9B total deposits in Q3 2025)<br/>
    • <b>SoFi Invest:</b> Stocks, ETFs, options trading, AI-focused funds, private market funds<br/>
    • <b>SoFi Crypto:</b> First nationally chartered bank to offer cryptocurrency trading (relaunched Nov 2025)<br/>
    • Revenue from transaction fees, management fees, share lending
    <br/><br/>
    <b>Strategic Advantage - National Bank Charter (2022):</b><br/>
    After acquiring Golden Pacific Bancorp in 2021, SoFi received federal approval to become SoFi Bank, National
    Association in January 2022. This charter allows the company to fund loans with low-cost member deposits
    rather than expensive third-party debt facilities - a game-changing competitive advantage that reduces
    funding costs and improves net interest margins.
    <br/><br/>
    <b>Key Products:</b><br/>
    • <b>SoFi Smart Card</b> (launched 2025): All-in-one account offering 5% cash back at groceries, 4.30% APY on savings<br/>
    • <b>SoFi USD Stablecoin</b> (planned 2026): Fully reserved U.S. dollar stablecoin for SoFi Pay international payments<br/>
    • AI/ML-powered risk assessment beyond traditional credit scores (education, career trajectory, income potential)
    """

    elements.append(Paragraph(company_overview, body_style))
    elements.append(PageBreak())

    # PAGE 4: 2026 CATALYSTS

    elements.append(Paragraph("2026 GROWTH CATALYSTS", header_style))

    catalysts_text = """
    <b>1. Crypto & Stablecoin Infrastructure:</b>
    <br/>
    • <b>SoFi Pay Launch:</b> International payments product leveraging blockchain rails, with integrated
    "SoFi USD" stablecoin planned for 2026 rollout<br/>
    • <b>Competitive Positioning:</b> First nationally chartered FDIC-insured bank offering crypto trading,
    creating regulatory differentiation vs. pure-play crypto platforms<br/>
    • <b>Risk Factor:</b> Regulatory scrutiny remains high; SoFi temporarily halted crypto services in 2025
    amid enforcement actions before re-entering under new OCC guidance
    <br/><br/>
    <b>2. S&P 500 Inclusion Potential:</b>
    <br/>
    • <b>Analyst View:</b> Truist believes SoFi, along with Affirm and Toast, could be added to the S&P 500
    "in the near future" (per Dec 3, 2025 note)<br/>
    • <b>Impact:</b> Index inclusion triggers forced buying from passive funds, potentially driving significant
    price appreciation<br/>
    • <b>Requirements:</b> Must maintain profitability (✓ 8 consecutive GAAP profitable quarters), meet
    market cap thresholds, and demonstrate earnings stability
    <br/><br/>
    <b>3. Member Growth & Cross-Selling Flywheel:</b>
    <br/>
    • <b>Current Metrics:</b> 12.6M members (+35% YoY), 18.6M products (+36% YoY)<br/>
    • <b>Cross-Sell Success:</b> 40% of new products adopted by existing members, demonstrating ecosystem stickiness<br/>
    • <b>Target:</b> Company aims for sustained 30% annual growth in both members and products<br/>
    • <b>Revenue Multiplier:</b> Each additional product per member increases lifetime value and reduces
    customer acquisition costs
    <br/><br/>
    <b>4. New Product Launches:</b>
    <br/>
    • <b>SoFi Smart Card:</b> All-in-one account with 5% grocery cash back and 4.30% APY savings, competing
    directly with Apple Card and traditional rewards cards<br/>
    • <b>Differentiation:</b> Integrated banking/investing/crypto in single platform reduces friction and
    increases engagement
    <br/><br/>
    <b>5. Strategic M&A & Capital Deployment:</b>
    <br/>
    • <b>War Chest:</b> Recent $1.5B capital raise (54.5M shares at $27.50) provides dry powder for acquisitions<br/>
    • <b>Target Areas:</b> Management cited crypto infrastructure and AI capabilities as M&A priorities<br/>
    • <b>Precedent:</b> Galileo ($1.2B) and Technisys ($1.1B) acquisitions successfully expanded platform capabilities<br/>
    • <b>Debt Refinancing:</b> Portion of capital allocated to refinancing high-cost debt, improving interest expense profile
    <br/><br/>
    <b>6. Bank Charter Leverage Expansion:</b>
    <br/>
    • <b>Deposit Growth:</b> $32.9B total deposits (Q3 2025) provides increasing low-cost funding capacity<br/>
    • <b>Loan Growth Runway:</b> Can expand lending volumes without proportional increase in funding costs<br/>
    • <b>NIM Expansion:</b> As deposit base grows, net interest margin should improve vs. peers relying on
    wholesale funding
    <br/><br/>
    <b>7. Regulatory & Macro Tailwinds:</b>
    <br/>
    • <b>Student Loan Normalization:</b> Payment resumption post-moratorium driving refinancing demand
    ($1.3B Q4 2024 originations, +71% YoY)<br/>
    • <b>Rate Environment:</b> Potential Fed rate cuts in 2026 could reduce funding costs and stimulate
    loan demand<br/>
    • <b>Fintech Regulation:</b> Clearer regulatory frameworks for digital assets could unlock crypto revenue streams
    """

    elements.append(Paragraph(catalysts_text, body_style))
    elements.append(PageBreak())

    # PAGE 5: RISKS & CHALLENGES

    elements.append(Paragraph("KEY RISKS & CHALLENGES", header_style))

    risks_text = """
    <b>1. Credit Quality Deterioration:</b>
    <br/>
    • <b>Current State:</b> Q1 2025 reported 330 basis points net losses on $18B personal loan portfolio<br/>
    • <b>Concentration Risk:</b> Personal loans constitute ~70% of lending portfolio, creating significant exposure
    to consumer credit cycles<br/>
    • <b>Trend Analysis:</b> Personal loan delinquency rates showed month-over-month increases, though student
    loan delinquencies improved marginally<br/>
    • <b>Implication:</b> Rising charge-offs could compress net interest margins and require higher loan loss reserves
    <br/><br/>
    <b>2. Intense Competition:</b>
    <br/>
    • <b>Mega-Banks:</b> JPMorgan, Bank of America investing billions in digital banking capabilities, leveraging
    massive deposit bases and brand recognition<br/>
    • <b>Neobank Rivals:</b> Chime, Ally Bank, Marcus by Goldman Sachs competing for same digitally-native customer base<br/>
    • <b>Fintech Disruptors:</b> Block (Cash App), PayPal, Robinhood offering overlapping products (investing, crypto, banking)<br/>
    • <b>Margin Pressure:</b> Customer acquisition costs remain elevated in crowded market; competitive deposit rates
    limit NIM expansion
    <br/><br/>
    <b>3. Valuation & Dilution Concerns:</b>
    <br/>
    • <b>Premium Pricing:</b> Trading well above traditional banks on P/E and P/B basis, leaving limited margin of safety<br/>
    • <b>Recent Dilution:</b> $1.5B stock offering (54.5M shares) triggered 7.3% stock decline, signaling investor concerns<br/>
    • <b>Growth Expectations:</b> Market pricing in 25% revenue growth (2025) and 22% (2026); any miss could trigger
    sharp correction<br/>
    • <b>Analyst Skepticism:</b> Mixed consensus (Hold rating, $27.48 avg target), with bears citing stretched multiples
    <br/><br/>
    <b>4. Regulatory & Compliance Risks:</b>
    <br/>
    • <b>Crypto Uncertainty:</b> SoFi halted crypto services in 2025 amid regulatory enforcement, demonstrating vulnerability
    to policy changes<br/>
    • <b>Bank Supervision:</b> As nationally chartered bank, subject to OCC oversight and capital requirements that
    could constrain growth<br/>
    • <b>AI/ML Regulation:</b> Proprietary underwriting algorithms face potential scrutiny around fairness and bias<br/>
    • <b>Consumer Protection:</b> CFPB oversight of lending practices, fee structures, and marketing claims
    <br/><br/>
    <b>5. Macro & Interest Rate Sensitivity:</b>
    <br/>
    • <b>Rate Volatility:</b> Net interest margin highly sensitive to Fed policy; rapid rate changes create asset-liability
    mismatch risk<br/>
    • <b>Recession Exposure:</b> Economic downturn would simultaneously increase credit losses and reduce loan demand<br/>
    • <b>Employment Dependency:</b> Target customers (young professionals) particularly vulnerable to layoffs in tech/finance
    <br/><br/>
    <b>6. Operational & Technology Risks:</b>
    <br/>
    • <b>Platform Complexity:</b> Managing lending + banking + investing + crypto increases operational risk and
    IT infrastructure demands<br/>
    • <b>Integration Challenges:</b> Galileo and Technisys acquisitions require ongoing integration; execution risk remains<br/>
    • <b>Cybersecurity:</b> High-profile target for attacks given customer financial data and crypto holdings<br/>
    • <b>Liquidity Profile:</b> Weak liquidity ratios deter risk-averse institutional investors
    <br/><br/>
    <b>7. Market Sentiment & Volatility:</b>
    <br/>
    • <b>Growth Stock Correlation:</b> Beta of 2.41 means SOFI amplifies market downturns (2.4x SPY moves)<br/>
    • <b>Volatility Regime:</b> 64% annual volatility creates significant drawdown risk (max DD: -47.31%)<br/>
    • <b>Sector Rotation:</b> As fintech growth stock, vulnerable to rotations into value/defensive sectors<br/>
    • <b>Retail Sentiment:</b> Heavy retail investor base creates momentum-driven price swings
    """

    elements.append(Paragraph(risks_text, body_style))
    elements.append(PageBreak())

    # PAGE 6: ANALYST CONSENSUS & MARKET SENTIMENT

    elements.append(Paragraph("ANALYST CONSENSUS & PRICE TARGETS", header_style))

    analyst_text = """
    <b>Wall Street Ratings (December 2025):</b>
    <br/><br/>
    <b>JPMorgan:</b> Neutral | Price Target: $31 (raised from $28)<br/>
    • Positive on bank charter leverage and deposit growth trajectory<br/>
    • Cautious on valuation premium vs. regional banks<br/>
    • Acknowledges strong execution but sees limited upside at current levels
    <br/><br/>
    <b>Truist Securities:</b> Hold | Price Target: $28 (lowered from $31)<br/>
    • Cited high forward earnings multiple vs. sector averages<br/>
    • Warned of difficult comparables in Q4 2025 and 2026<br/>
    • Identified potential S&P 500 inclusion as positive catalyst<br/>
    • Concerned about margin pressure if underwriting tightens or loan demand normalizes
    <br/><br/>
    <b>KBW (Keefe, Bruyette & Woods):</b> Underperform (Sell) | Price Target: $20 (raised from $18)<br/>
    • Most bearish major analyst; sees fundamental overvaluation<br/>
    • Expects credit quality deterioration to compress margins<br/>
    • Questions sustainability of growth rates in saturated digital banking market
    <br/><br/>
    <b>Consensus Summary:</b><br/>
    • <b>TipRanks Aggregate:</b> Hold consensus, $27.50 average target (range: $12-$38)<br/>
    • <b>StockAnalysis:</b> $24.70 average target<br/>
    • <b>MarketBeat:</b> $25.69 average target<br/>
    • <b>Benzinga (Oct 2025):</b> Hold consensus, $16.04 mean target based on 28 analyst ratings
    <br/><br/>
    <b>Interpretation:</b> Wall Street remains skeptical despite strong operational performance. The wide target
    range ($12-$38) reflects deep uncertainty about SoFi's long-term business model sustainability. Bulls see a
    category-defining fintech platform; bears see an overvalued lender with deteriorating credit quality. The
    reality likely lies in between.
    """

    elements.append(Paragraph(analyst_text, body_style))
    elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("MARKET SENTIMENT & TECHNICAL POSITIONING", subheader_style))

    sentiment_text = """
    <b>Current Technical Picture (December 18, 2025):</b><br/>
    • Price: $26.29 (near middle of Bollinger Bands: $24.44 - $30.45)<br/>
    • Multiple oversold indicators: Stochastic %K (1.90), Williams %R (-98.10)<br/>
    • Bearish MACD crossover signals potential further downside<br/>
    • Recent 12.95% decline from local highs creates tactical buying opportunity
    <br/><br/>
    <b>Volume & Institutional Activity:</b><br/>
    • $1.5B equity raise suggests management sees stock as fairly valued or overvalued (dilutive timing)<br/>
    • Heavy retail investor base creates volatility spikes on news events<br/>
    • Institutional ownership increasing but still below mega-cap fintech peers
    <br/><br/>
    <b>Sentiment Drivers:</b><br/>
    • <b>Positive:</b> 8 consecutive GAAP profitable quarters, 86% YTD returns, S&P 500 inclusion speculation<br/>
    • <b>Negative:</b> Recent equity dilution, credit quality concerns, stretched valuation multiples<br/>
    • <b>Neutral:</b> Mixed momentum indicators, sideways consolidation after strong run
    """

    elements.append(Paragraph(sentiment_text, body_style))
    elements.append(PageBreak())

    # PAGE 7: PORTFOLIO STRATEGY & POSITION SIZING

    elements.append(Paragraph("PORTFOLIO STRATEGY & POSITION SIZING", header_style))

    strategy_text = """
    <b>Current Position Context:</b><br/>
    • Existing Holdings: 29 shares<br/>
    • Current Position Value: $762.41 (29 shares × $26.29)<br/>
    • Portfolio Allocation: ~0.3% of $250,000 portfolio<br/>
    • Cost Basis: Not provided (assume blended from prior purchases)
    <br/><br/>
    <b>Recommended Position Sizing:</b>
    <br/><br/>
    Given SOFI's high-risk profile (Beta: 2.41, Volatility: 64%, Max DD: -47%), we recommend conservative position
    sizing aligned with volatility regime analysis:
    """

    elements.append(Paragraph(strategy_text, body_style))
    elements.append(Spacer(1, 0.1*inch))

    # Position sizing table
    sizing_data = [
        ['Position Tier', 'Portfolio %', 'Dollar Amount', 'Share Count', 'Action'],
        ['Conservative', '1.5%', '$3,750', '143 shares', 'Add 114 shares'],
        ['RECOMMENDED', '2.0%', '$5,000', '190 shares', 'Add 161 shares'],
        ['Moderate', '2.5%', '$6,250', '238 shares', 'Add 209 shares'],
        ['Aggressive', '3.0%', '$7,500', '285 shares', 'Add 256 shares'],
        ['Maximum (High Vol)', '5.0%', '$12,500', '475 shares', 'Add 446 shares']
    ]

    sizing_table = Table(sizing_data, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1.2*inch, 1.1*inch])
    sizing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#d5f4e6')),
        ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, 1), [colors.white]),
        ('ROWBACKGROUNDS', (0, 3), (-1, -1), [colors.HexColor('#f8f9fa'), colors.white])
    ]))
    elements.append(sizing_table)
    elements.append(Spacer(1, 0.2*inch))

    entry_strategy = """
    <b>Entry Strategy Recommendations:</b>
    <br/><br/>
    <b>SCENARIO 1: Maintain & Monitor (PREFERRED):</b><br/>
    • <b>Action:</b> Hold existing 29 shares, do NOT add at current price<br/>
    • <b>Rationale:</b> Recent -12.95% pullback suggests downward momentum; oversold indicators (Stochastic, Williams %R)
    often lead to further selling before reversal; bearish MACD crossover needs resolution<br/>
    • <b>Watchpoints:</b><br/>
    &nbsp;&nbsp;- Monitor Q4 2025 earnings (late Jan/early Feb 2026) for credit quality metrics<br/>
    &nbsp;&nbsp;- Watch for stabilization in personal loan delinquency rates<br/>
    &nbsp;&nbsp;- Await clearer momentum signal (MACD bullish crossover, RSI >50)
    <br/><br/>
    <b>SCENARIO 2: Tactical Add on Pullback:</b><br/>
    • <b>Entry Zone 1:</b> $24.00-$24.50 (near Bollinger lower band + psychological support)<br/>
    &nbsp;&nbsp;Action: Add 50-75 shares ($1,200-$1,838) to reach 1.5% portfolio allocation<br/>
    • <b>Entry Zone 2:</b> $22.00-$23.00 (15% pullback from current, tests 200-day MA)<br/>
    &nbsp;&nbsp;Action: Add 100-130 shares ($2,200-$2,990) to reach 2.0% recommended allocation<br/>
    • <b>Invalidation:</b> If price breaks below $21.00, reassess thesis (would signal credit concerns materializing)
    <br/><br/>
    <b>SCENARIO 3: Momentum Breakout (Alternative):</b><br/>
    • <b>Trigger:</b> Sustained break above $30.45 (Bollinger upper band) on strong volume<br/>
    • <b>Signal:</b> MACD bullish crossover + RSI >60 + positive earnings catalyst<br/>
    • <b>Action:</b> Add 80-100 shares ($2,436-$3,045) on breakout confirmation<br/>
    • <b>Stop Loss:</b> 7-8% below entry ($28.00 area) using 2× ATR guidance
    <br/><br/>
    <b>Risk Management:</b><br/>
    • <b>Maximum Position:</b> Cap at 3.0% ($7,500 / 285 shares) given high volatility<br/>
    • <b>Stop Loss:</b> Use 2× ATR = $2.81 trailing stop (~10-11% below entry)<br/>
    • <b>Portfolio Balance:</b> Ensure SOFI + other high-beta positions <15% of total portfolio<br/>
    • <b>Rebalancing:</b> If position appreciates to >4% of portfolio, trim to 2.5-3.0%
    <br/><br/>
    <b>Catalyst Calendar:</b><br/>
    • <b>Q4 2025 Earnings:</b> Late Jan/early Feb 2026 - Critical for credit quality assessment<br/>
    • <b>SoFi USD Launch:</b> 2026 (date TBD) - Monitor for stablecoin regulatory approval<br/>
    • <b>S&P 500 Rebalance:</b> Quarterly reviews (March, June, Sept, Dec 2026)<br/>
    • <b>Fed Rate Decisions:</b> Watch for policy shifts impacting net interest margin
    """

    elements.append(Paragraph(entry_strategy, body_style))
    elements.append(PageBreak())

    # PAGE 8: CONCLUSION & DISCLAIMER

    elements.append(Paragraph("INVESTMENT CONCLUSION", header_style))

    conclusion_text = """
    <b>Final Verdict: HOLD / Selective Moderate Buy</b>
    <br/><br/>
    SoFi Technologies presents a compelling but complex investment case. The company has executed exceptionally well
    on its transition from fintech disruptor to legitimate digital banking franchise, evidenced by 8 consecutive
    quarters of GAAP profitability, 35% member growth, and 86% YTD stock appreciation. The national bank charter
    provides a sustainable competitive moat through low-cost deposit funding, while the diversified revenue mix
    (55% financial services/tech, 45% lending) reduces single-product dependency.
    <br/><br/>
    <b>However, significant headwinds temper our enthusiasm:</b><br/>
    • Credit quality deterioration (330 bps net losses, rising delinquencies)<br/>
    • Elevated valuation with limited margin of safety<br/>
    • Extreme volatility (64% annual) and drawdown risk (47% max DD)<br/>
    • Recent equity dilution signaling management's view on valuation<br/>
    • Regulatory uncertainty around crypto and AI initiatives
    <br/><br/>
    <b>Given these factors, we recommend:</b>
    <br/><br/>
    <b>1. Current Holders (29 shares):</b> HOLD position without immediate additions. Your minimal exposure (~0.3%
    of portfolio) provides asymmetric upside if catalysts materialize (S&P inclusion, stablecoin success) while
    limiting downside from credit quality concerns.
    <br/><br/>
    <b>2. Portfolio Target:</b> If adding, build toward 2.0% allocation ($5,000 / 190 shares) using tactical
    entries on pullbacks to $24.00-$24.50 or $22.00-$23.00 zones. This provides meaningful exposure to fintech
    growth thesis while respecting high-volatility risk profile.
    <br/><br/>
    <b>3. Risk Management:</b> Use 2× ATR trailing stops ($2.81 / ~10%), cap maximum position at 3.0%, and
    rebalance if appreciation pushes allocation above 4%. Ensure total high-beta exposure (SOFI + similar
    holdings) stays below 15% of portfolio.
    <br/><br/>
    <b>4. Catalyst Monitoring:</b> Q4 2025 earnings (late Jan/early Feb 2026) represent critical inflection
    point. Watch for:<br/>
    • Personal loan delinquency trend reversal<br/>
    • Deposit growth sustainability ($32.9B base)<br/>
    • Member/product growth maintaining 30%+ trajectory<br/>
    • SoFi USD regulatory approval timeline
    <br/><br/>
    <b>Bottom Line:</b> SoFi is a SHOW ME story at current prices. The company has earned credibility through
    consistent execution, but valuation and credit risks create a narrow path to further upside. Patient investors
    who can tolerate extreme volatility may find tactical opportunities on pullbacks. For most portfolios, a
    2-3% allocation represents optimal risk/reward balance.
    <br/><br/>
    <b>Rating: 7.5/10</b> - Strong operational execution, meaningful growth runway, but elevated risks and
    stretched valuation limit conviction.
    """

    elements.append(Paragraph(conclusion_text, body_style))
    elements.append(Spacer(1, 0.3*inch))

    # Compliance Disclaimer
    elements.append(Paragraph("IMPORTANT DISCLAIMERS & RISK WARNINGS", header_style))

    disclaimer_text = """
    <b>EDUCATIONAL PURPOSES ONLY - NOT INVESTMENT ADVICE</b>
    <br/><br/>
    This report is provided for informational and educational purposes only and does not constitute investment advice,
    financial advice, trading advice, or any other sort of advice. The information contained herein is based on sources
    believed to be reliable but is not guaranteed for accuracy or completeness.
    <br/><br/>
    <b>No Recommendation:</b> Nothing in this report should be construed as a recommendation to buy, sell, or hold
    any security. You should not rely on this report as the primary basis for investment decisions.
    <br/><br/>
    <b>Consult Professionals:</b> Before making any investment decision, you should consult with your own financial
    advisor, accountant, and/or attorney who can provide advice based on your particular circumstances and financial
    situation.
    <br/><br/>
    <b>Risk of Loss:</b> Investing in securities involves substantial risk of loss, including the possible loss of
    principal. Past performance is not indicative of future results. SoFi Technologies (SOFI) exhibits high volatility
    (64% annual), high beta (2.41), and has experienced severe drawdowns (max: -47.31%). You could lose all or a
    substantial portion of your investment.
    <br/><br/>
    <b>Forward-Looking Statements:</b> This report contains forward-looking statements including price targets, growth
    projections, and catalyst timelines. Actual results may differ materially due to credit quality deterioration,
    competitive pressures, regulatory changes, macroeconomic conditions, and other unforeseen factors.
    <br/><br/>
    <b>Data Sources:</b> Market data provided by Yahoo Finance (yfinance), Finnhub. Analyst consensus from TipRanks,
    StockAnalysis, MarketBeat, Benzinga. Company information from SoFi investor relations, SEC filings, and news sources.
    All data subject to revision and may contain errors.
    <br/><br/>
    <b>No Relationship:</b> Finance Guru has no business relationship with SoFi Technologies, Inc. and receives no
    compensation from the company. This analysis is independent and unsolicited.
    <br/><br/>
    <b>Personal Positions:</b> The portfolio referenced (29 existing shares) represents actual holdings. Analysts may
    have personal positions in securities discussed.
    <br/><br/>
    Report Generated: December 18, 2025<br/>
    Finance Guru™ Research Division<br/>
    Powered by BMAD-CORE™ v6.0.0
    """

    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=body_style,
        fontSize=8,
        textColor=colors.HexColor('#555555'),
        leading=10
    )

    elements.append(Paragraph(disclaimer_text, disclaimer_style))

    # Build PDF
    doc.build(elements)
    print(f"\n✅ SOFI Analysis Report Generated Successfully!")
    print(f"📄 Location: {output_path}")
    print(f"📊 Report contains 8 pages of comprehensive analysis\n")

    return output_path

if __name__ == "__main__":
    create_sofi_report()
