#!/usr/bin/env python3
"""
Generate AMZN Analysis Report PDF
Finance Guru™ Document Builder
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib import colors
from datetime import datetime
import os

# Output path
OUTPUT_DIR = "/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "AMZN-analysis-2025-12-18.pdf")

# Ensure directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Colors
DARK_BLUE = HexColor("#1a365d")
LIGHT_BLUE = HexColor("#3182ce")
DARK_GRAY = HexColor("#2d3748")
LIGHT_GRAY = HexColor("#e2e8f0")
GREEN = HexColor("#38a169")
RED = HexColor("#e53e3e")
YELLOW = HexColor("#d69e2e")

def create_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    # Title style
    styles.add(ParagraphStyle(
        name='ReportTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=DARK_BLUE,
        spaceAfter=6,
        alignment=TA_CENTER
    ))

    # Subtitle
    styles.add(ParagraphStyle(
        name='ReportSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=DARK_GRAY,
        spaceAfter=20,
        alignment=TA_CENTER
    ))

    # Section heading
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=DARK_BLUE,
        spaceBefore=20,
        spaceAfter=10,
        borderColor=LIGHT_BLUE,
        borderWidth=2,
        borderPadding=5
    ))

    # Subsection heading
    styles.add(ParagraphStyle(
        name='SubHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=DARK_BLUE,
        spaceBefore=12,
        spaceAfter=6
    ))

    # Body text (override existing)
    styles['BodyText'].fontSize = 10
    styles['BodyText'].textColor = DARK_GRAY
    styles['BodyText'].spaceAfter = 8
    styles['BodyText'].alignment = TA_JUSTIFY

    # Bullet points
    styles.add(ParagraphStyle(
        name='BulletPoint',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_GRAY,
        leftIndent=20,
        spaceAfter=4
    ))

    # Disclaimer
    styles.add(ParagraphStyle(
        name='Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=DARK_GRAY,
        alignment=TA_CENTER,
        spaceBefore=10,
        spaceAfter=10
    ))

    # Footer
    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=DARK_GRAY,
        alignment=TA_CENTER
    ))

    return styles

def create_table(data, col_widths=None, header=True):
    """Create a styled table."""
    if col_widths is None:
        col_widths = [2*inch] * len(data[0])

    table = Table(data, colWidths=col_widths)

    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    if not header:
        style_commands = [cmd for cmd in style_commands if cmd[1] != (0, 0) or cmd[0] not in ['BACKGROUND', 'TEXTCOLOR', 'FONTNAME']]

    table.setStyle(TableStyle(style_commands))
    return table

def build_report():
    """Build the complete PDF report."""
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = create_styles()
    story = []

    # ========== COVER PAGE ==========
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("FINANCE GURU™", styles['ReportSubtitle']))
    story.append(Paragraph("Amazon.com Inc (AMZN)", styles['ReportTitle']))
    story.append(Paragraph("Comprehensive 2026 Watchlist Analysis", styles['ReportSubtitle']))
    story.append(Spacer(1, 0.5*inch))

    # Cover info table
    cover_data = [
        ["Prepared For:", "Ossie Irondi - Private Family Office"],
        ["Prepared By:", "Finance Guru™ Market Intelligence Team"],
        ["Date:", "December 18, 2025"],
        ["Data As Of:", "December 17, 2025 (Market Close)"],
        ["Classification:", "Internal Use Only"],
    ]
    cover_table = create_table(cover_data, [2*inch, 4.5*inch], header=False)
    story.append(cover_table)

    story.append(Spacer(1, 0.5*inch))
    story.append(HRFlowable(width="80%", thickness=2, color=LIGHT_BLUE))
    story.append(Spacer(1, 0.3*inch))

    # Disclaimer box
    disclaimer_text = """<b>COMPLIANCE DISCLAIMER</b><br/>
    This analysis is for educational purposes only and does not constitute personalized investment advice.
    Past performance does not guarantee future results. Consult a licensed financial advisor before making investment decisions."""
    story.append(Paragraph(disclaimer_text, styles['Disclaimer']))

    story.append(PageBreak())

    # ========== EXECUTIVE SUMMARY ==========
    story.append(Paragraph("1. Executive Summary", styles['SectionHeading']))

    story.append(Paragraph("<b>Investment Thesis</b>", styles['SubHeading']))
    story.append(Paragraph(
        "Amazon.com (NASDAQ: AMZN) represents a unique multi-engine growth story combining dominant AWS cloud infrastructure, "
        "rapidly expanding AI capabilities, e-commerce market leadership, and a high-margin advertising business. With massive "
        "AI infrastructure investments ($125B+ in 2025, growing in 2026), custom Trainium chips achieving multi-billion dollar "
        "revenue run rates, and AWS positioned as 'the biggest inference engine in the world,' AMZN is strategically positioned "
        "for the AI-driven future while maintaining strong fundamentals across all business segments.",
        styles['BodyText']
    ))

    story.append(Paragraph("<b>Key Findings</b>", styles['SubHeading']))
    findings = [
        "• <b>AWS Acceleration:</b> Best quarter in recent memory with 20% YoY growth. AWS accounts for 18% of revenue but 66% of operating income—critical profit driver.",
        "• <b>AI Infrastructure Dominance:</b> $125B capex in 2025 (up from $118B forecast), $50B committed to US government AI infrastructure alone. Trainium2 reached multi-billion dollar annual run rate with 150% QoQ growth.",
        "• <b>Custom Silicon Success:</b> Trainium3 delivers 4x performance vs Trainium2 at lower power. CEO Andy Jassy: 'Bedrock could be as big a business as EC2' (AWS's foundational service).",
        "• <b>Advertising Juggernaut:</b> $60B+ in 2025 retail media ad revenue, projected $70B+ in 2026. Prime Video ads gaining traction with 200M+ viewers.",
        "• <b>E-commerce Fortress:</b> 38-40% US market share, 75% of US households are Prime members—unmatched moat.",
        "• <b>2026 Price Targets:</b> Wall Street consensus $295 (+30% from current levels). Long-term 2030 projections exceed $400.",
    ]
    for finding in findings:
        story.append(Paragraph(finding, styles['BulletPoint']))

    story.append(Paragraph("<b>Quantitative Profile</b>", styles['SubHeading']))
    quant_summary = [
        "• <b>Risk-Adjusted Returns:</b> Sharpe 0.05 (poor short-term), Sortino 0.07 (below expectations)",
        "• <b>Volatility:</b> 34.50% annual (medium), -30.88% max drawdown—recent underperformance weighing on metrics",
        "• <b>Market Relationship:</b> Beta 1.33 (higher systematic risk), Alpha -9.56% (underperforming in 2025 but poised for reversal)",
        "• <b>Momentum Signals:</b> MIXED—oversold conditions (Stochastic %K: 1.56, Williams %R: -98.44) suggest potential reversal, but MACD bearish",
        "• <b>Portfolio Correlation:</b> High correlation with VOO (0.759), moderate with NVDA (0.571), TSLA (0.533), PLTR (0.505)",
    ]
    for item in quant_summary:
        story.append(Paragraph(item, styles['BulletPoint']))

    story.append(Paragraph("<b>Final Verdict: STRONG BUY for 2026</b>", styles['SubHeading']))
    story.append(Paragraph(
        "Despite modest 2025 performance (+4% vs SPY +16%), AMZN's strategic positioning in AI infrastructure, AWS reacceleration, "
        "advertising growth, and massive capital deployment create compelling 2026 catalysts. Current price represents attractive entry "
        "point with 30%+ upside potential. Recommended position: 10-15% of aggressive growth portfolio.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== COMPANY OVERVIEW ==========
    story.append(Paragraph("2. Company Overview & Market Position", styles['SectionHeading']))

    overview_data = [
        ["Attribute", "Details"],
        ["Full Name", "Amazon.com, Inc."],
        ["Ticker", "NASDAQ: AMZN"],
        ["Headquarters", "Seattle, Washington"],
        ["Sector", "Technology - Internet Retail & Cloud Services"],
        ["Current Price", "$226.76 (Dec 18, 2025)"],
        ["52-Week Range", "$170 - $240 (estimated)"],
        ["2025 YTD Performance", "+4% (underperformed SPY +16%)"],
    ]
    story.append(create_table(overview_data, [2*inch, 4.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Business Segments: The Four-Engine Growth Model</b>", styles['SubHeading']))

    # AWS
    story.append(Paragraph("<b>1. Amazon Web Services (AWS) - The Profit Engine</b>", styles['SubHeading']))
    aws_data = [
        ["Metric", "Details"],
        ["Revenue Contribution", "18% of total revenue"],
        ["Operating Income", "66% of total operating income"],
        ["Q3 2025 Growth", "20% YoY (best quarter in recent memory)"],
        ["2026 Projection", "30%+ revenue growth (analyst estimate)"],
        ["Key Products", "EC2, S3, Lambda, Bedrock (AI), Trainium chips, SageMaker"],
    ]
    story.append(create_table(aws_data, [2*inch, 4.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    # E-commerce
    story.append(Paragraph("<b>2. E-commerce - The Market Share Fortress</b>", styles['SubHeading']))
    ecomm_data = [
        ["Metric", "Details"],
        ["US Market Share", "38-40% of total retail e-commerce sales"],
        ["Prime Membership", "75% of US households (200M+ members globally)"],
        ["Fulfillment Network", "Industry-leading logistics infrastructure"],
        ["Competitive Moat", "Scale, speed, selection—nearly insurmountable advantage"],
    ]
    story.append(create_table(ecomm_data, [2*inch, 4.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    # Advertising
    story.append(Paragraph("<b>3. Advertising - The High-Margin Rocket Ship</b>", styles['SubHeading']))
    ad_data = [
        ["Metric", "Details"],
        ["2025 Revenue", "$60B+ (retail media ads)"],
        ["2026 Projection", "$70B+ (WARC forecast)"],
        ["Growth Rate", "22% YoY (Q2 2025, fastest-growing segment)"],
        ["Market Position", "#3 digital advertiser globally (behind Google, Meta)"],
        ["Prime Video Ads", "$3.5B-$5B projected 2025 revenue (BofA estimate)"],
    ]
    story.append(create_table(ad_data, [2*inch, 4.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    # AI Infrastructure
    story.append(Paragraph("<b>4. AI Infrastructure - The 2026 Catalyst</b>", styles['SubHeading']))
    ai_data = [
        ["Initiative", "Details"],
        ["2025 Capex", "$125B (up from $118B forecast)"],
        ["US Gov AI Investment", "$50B committed to government agency infrastructure"],
        ["Trainium Chips", "Multi-billion dollar annual run rate, 150% QoQ growth"],
        ["Bedrock Platform", "100,000+ organizations using generative AI"],
        ["Strategic Goal", "'Biggest inference engine in the world'—Jassy"],
    ]
    story.append(create_table(ai_data, [2*inch, 4.5*inch]))

    story.append(PageBreak())

    # ========== QUANTITATIVE ANALYSIS ==========
    story.append(Paragraph("3. Quantitative Analysis", styles['SectionHeading']))

    story.append(Paragraph("<b>Risk Metrics (252-Day vs SPY)</b>", styles['SubHeading']))
    risk_data = [
        ["Metric", "Value", "Interpretation"],
        ["Sharpe Ratio", "0.05", "Poor—reflects 2025 underperformance"],
        ["Sortino Ratio", "0.07", "Below expectations—downside weighed heavily"],
        ["Beta", "1.33", "Higher systematic risk than market"],
        ["Alpha", "-9.56%", "Underperformed SPY in 2025 (setup for reversal)"],
        ["95% VaR (Daily)", "-3.09%", "95% of days, losses won't exceed 3.09%"],
        ["95% CVaR", "-4.81%", "Tail risk: average 4.81% loss when breached"],
        ["Maximum Drawdown", "-30.88%", "Significant peak-to-trough decline"],
        ["Calmar Ratio", "0.20", "Low risk-adjusted return vs max drawdown"],
        ["Annual Volatility", "34.50%", "Medium volatility (20-40% range)"],
    ]
    story.append(create_table(risk_data, [2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Context:</b> Poor short-term risk metrics reflect AMZN's 2025 underperformance (+4% vs SPY +16%). "
        "However, this creates attractive entry point for 2026 catalysts (AI infrastructure, AWS reacceleration, advertising growth).",
        styles['BodyText']
    ))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Momentum Indicators (90-Day)</b>", styles['SubHeading']))
    momentum_data = [
        ["Indicator", "Value", "Signal"],
        ["RSI (14)", "39.76", "Neutral (no extreme)"],
        ["MACD Line", "-2.00", "—"],
        ["MACD Signal", "-1.03", "Bearish (MACD below signal)"],
        ["MACD Histogram", "-0.97", "Downward momentum"],
        ["Stochastic %K", "1.56", "OVERSOLD—potential reversal up"],
        ["Stochastic %D", "5.18", "OVERSOLD confirmation"],
        ["Williams %R", "-98.44", "OVERSOLD—strong buy signal potential"],
        ["Rate of Change", "-5.39%", "Bearish (negative momentum)"],
        ["Bullish Signals", "2/5", "—"],
        ["Bearish Signals", "2/5", "—"],
        ["Confluence", "MIXED", "No clear direction—watch for breakout"],
    ]
    story.append(create_table(momentum_data, [2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Interpretation:</b> Oversold conditions (Stochastic, Williams %R) suggest AMZN is approaching a floor. "
        "Mixed signals warrant cautious entry—consider dollar-cost averaging or waiting for MACD crossover confirmation.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    story.append(Paragraph("<b>Volatility Profile (90-Day)</b>", styles['SubHeading']))
    vol_data = [
        ["Metric", "Value", "Assessment"],
        ["Volatility Regime", "LOW", "Favorable for position sizing"],
        ["Position Sizing Guidance", "10-20%", "Can use larger positions in low vol regime"],
        ["ATR (14)", "$5.07", "—"],
        ["ATR %", "2.23%", "—"],
        ["Suggested Stop Loss", "$10.13", "2x ATR from entry"],
        ["Daily Volatility", "0.0146", "—"],
        ["Annual Volatility", "23.14%", "Historical measure"],
        ["Bollinger Bands Upper", "$237.11", "—"],
        ["Bollinger Bands Middle", "$227.58", "—"],
        ["Bollinger Bands Lower", "$218.06", "—"],
        ["Bollinger %B", "0.457", "Price within normal range"],
        ["Bollinger Bandwidth", "8.37%", "Narrow bands—'the squeeze' (breakout setup)"],
    ]
    story.append(create_table(vol_data, [2.2*inch, 1.5*inch, 2.8*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Key Insight:</b> LOW volatility regime + narrow Bollinger Bands = potential breakout setup. "
        "Historically, 'the squeeze' precedes significant price moves. Given 2026 catalysts, bias toward upside breakout.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    story.append(Paragraph("<b>Portfolio Correlation Analysis (252-Day)</b>", styles['SubHeading']))
    corr_matrix = [
        ["Asset", "AMZN", "PLTR", "TSLA", "NVDA", "VOO"],
        ["AMZN", "1.000", "0.505", "0.533", "0.571", "0.759"],
        ["PLTR", "0.505", "1.000", "0.523", "0.577", "0.608"],
        ["TSLA", "0.533", "0.523", "1.000", "0.517", "0.685"],
        ["NVDA", "0.571", "0.577", "0.517", "1.000", "0.731"],
        ["VOO", "0.759", "0.608", "0.685", "0.731", "1.000"],
    ]
    story.append(create_table(corr_matrix, [1.3*inch]*5))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Key Insights</b>", styles['SubHeading']))
    corr_insights = [
        ["Correlation", "Value", "Interpretation"],
        ["AMZN / VOO", "+0.759", "VERY HIGH—tracks market closely"],
        ["AMZN / NVDA", "+0.571", "HIGH—AI infrastructure overlap"],
        ["AMZN / TSLA", "+0.533", "MODERATE-HIGH—tech beta exposure"],
        ["AMZN / PLTR", "+0.505", "MODERATE—lowest correlation in portfolio"],
        ["Diversification Score", "0.399", "MODERATE—limited diversification benefit"],
        ["Avg Correlation", "0.601", "—"],
    ]
    story.append(create_table(corr_insights, [2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Portfolio Impact:</b> Adding AMZN to your tech-heavy portfolio provides limited diversification (high VOO correlation). "
        "However, AMZN's unique AWS/advertising/e-commerce mix offers different growth drivers than pure-play tech (NVDA chips, TSLA EVs, PLTR software). "
        "Recommend 10-15% position—large enough for meaningful impact, small enough to manage concentration risk.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== AWS & AI DEEP DIVE ==========
    story.append(Paragraph("4. AWS & AI Infrastructure Deep Dive", styles['SectionHeading']))

    story.append(Paragraph("<b>AWS Performance Acceleration</b>", styles['SubHeading']))
    story.append(Paragraph(
        "AWS delivered its strongest quarter in recent memory during Q3 2025, with 20% YoY revenue growth. "
        "This reacceleration is critical—AWS represents only 18% of total revenue but accounts for 66% of operating income, "
        "making it the primary profit driver. Wall Street analysts project AWS revenue could grow 30%+ over the next year.",
        styles['BodyText']
    ))

    story.append(Paragraph("<b>AI Infrastructure Investment Scale</b>", styles['SubHeading']))
    ai_invest_data = [
        ["Investment Category", "Amount", "Strategic Purpose"],
        ["2025 Total Capex", "$125B", "Up from $118B forecast—aggressive AI buildout"],
        ["US Gov AI Infrastructure", "$50B", "Dedicated to US government agency AI systems"],
        ["2026 Expected Capex", ">$125B", "Continued growth to support AI megatrend"],
        ["Project Rainier", "500K chips", "Trainium2 deployment, targeting 1M by year-end"],
    ]
    story.append(create_table(ai_invest_data, [2.2*inch, 1.8*inch, 2.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Custom Silicon: Trainium Chips</b>", styles['SubHeading']))
    trainium_data = [
        ["Metric", "Details"],
        ["Trainium2 Revenue", "Multi-billion dollar annual run rate"],
        ["Trainium2 Growth", "150% quarter-over-quarter"],
        ["Trainium2 Deployments", "1M+ chips (approaching by year-end 2025)"],
        ["Trainium3 Performance", "4x faster than Trainium2, lower power consumption"],
        ["Trainium3 UltraServers", "Announced at AWS re:Invent 2025"],
        ["Graviton5 CPU", "Most powerful and efficient AWS CPU to date"],
        ["Strategic Advantage", "Reduces dependency on Nvidia, controls AI stack end-to-end"],
    ]
    story.append(create_table(trainium_data, [2*inch, 4.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Why This Matters:</b> AWS's custom silicon strategy (Trainium, Graviton) allows margin expansion by reducing "
        "reliance on expensive third-party chips (Nvidia). CEO Andy Jassy stated Trainium has already become a 'multibillion-dollar "
        "business' growing 150% QoQ—this is a massive revenue stream in early stages of hypergrowth.",
        styles['BodyText']
    ))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Amazon Bedrock: The 'Biggest Inference Engine in the World'</b>", styles['SubHeading']))
    bedrock_data = [
        ["Metric", "Details"],
        ["Bedrock Users", "100,000+ organizations worldwide"],
        ["Customer Base", "Startups to global enterprises across all industries"],
        ["Amazon Nova Models", "New foundation models announced at re:Invent 2025"],
        ["AgentCore Platform", "Scaling secure AI agents—announced Dec 2025"],
        ["CEO Vision", "'Bedrock could be as big a business as EC2'—Jassy"],
    ]
    story.append(create_table(bedrock_data, [2*inch, 4.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Strategic Context:</b> EC2 (Elastic Compute Cloud) is AWS's foundational service—the engine that built AWS into a "
        "$100B+ revenue business. Jassy comparing Bedrock to EC2 signals Amazon expects generative AI inference to become a revenue "
        "stream of similar magnitude. With 100K+ organizations already using Bedrock, this isn't speculative—it's happening now.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== ADVERTISING BUSINESS ==========
    story.append(Paragraph("5. Advertising Business: The Silent Juggernaut", styles['SectionHeading']))

    story.append(Paragraph("<b>Revenue Trajectory</b>", styles['SubHeading']))
    ad_revenue_data = [
        ["Year", "Retail Media Ad Revenue", "Growth Rate", "Source"],
        ["2024", "$56B", "+18% YoY", "Amazon earnings"],
        ["2025 (Projected)", "$60.6B+", "~8-9%", "WARC Media"],
        ["2026 (Projected)", "$70B+", "~15-16%", "WARC Media, eMarketer"],
        ["2030 (Projected)", "$79B+", "—", "WARC Media"],
    ]
    story.append(create_table(ad_revenue_data, [1.5*inch, 2*inch, 1.5*inch, 1.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Market Position</b>", styles['SubHeading']))
    story.append(Paragraph(
        "Amazon is the #3 digital advertising company globally, behind only Google and Meta. In Q2 2025, advertising maintained "
        "its position as Amazon's fastest-growing segment for the second consecutive quarter with 22% growth—only AWS comes close to "
        "matching this consistency.",
        styles['BodyText']
    ))

    story.append(Paragraph("<b>Prime Video Advertising (New Frontier)</b>", styles['SubHeading']))
    prime_video_data = [
        ["Metric", "Details"],
        ["Launch Date", "2024 (ads introduced to Prime Video)"],
        ["Viewer Access", "200M+ viewers worldwide"],
        ["2025 Revenue (Projected)", "$3.5B - $5B (Bank of America estimate)"],
        ["Growth Potential", "Early innings—massive upside as format matures"],
    ]
    story.append(create_table(prime_video_data, [2*inch, 4.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Investment Insight:</b> Advertising is Amazon's highest-margin business segment, and it's barely penetrated. "
        "With 200M+ Prime Video viewers and increasing retail media sophistication, Amazon could realistically challenge Meta for "
        "the #2 digital advertising spot within 3-5 years. This is a multi-decade growth runway.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== 2026 CATALYSTS ==========
    story.append(Paragraph("6. 2026 Catalysts & Price Targets", styles['SectionHeading']))

    story.append(Paragraph("<b>Key Catalysts for 2026</b>", styles['SubHeading']))
    catalysts = [
        "• <b>AWS Reacceleration:</b> Sustained 20-30% growth driven by AI workload migration to Bedrock and Trainium infrastructure",
        "• <b>Advertising Revenue Milestones:</b> Crossing $70B threshold, Prime Video ads scaling rapidly",
        "• <b>AI Infrastructure Payoff:</b> $125B+ capex investment begins generating material revenue (Trainium, Bedrock, SageMaker)",
        "• <b>Margin Expansion:</b> Custom silicon (Trainium, Graviton) reduces costs, high-margin advertising scales",
        "• <b>Enterprise AI Adoption:</b> 100K+ Bedrock customers expand usage, new Fortune 500 wins",
        "• <b>Government Contracts:</b> $50B US government AI infrastructure commitment materializes",
    ]
    for catalyst in catalysts:
        story.append(Paragraph(catalyst, styles['BulletPoint']))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Analyst Price Targets</b>", styles['SubHeading']))
    targets_data = [
        ["Timeframe", "Price Target", "Upside from $226.76", "Source"],
        ["End of 2025", "$224-$234", "~0-3%", "Long Forecast"],
        ["End of 2026", "$295", "+30%", "Wall Street consensus (Motley Fool)"],
        ["2026 (Conservative)", "$255", "+12%", "CoinPriceForest trough"],
        ["2026 (Optimistic)", "$305", "+34%", "CoinPriceForest peak"],
        ["2030 Long-Term", "$400+", "+76%", "AI-driven growth (multiple sources)"],
    ]
    story.append(create_table(targets_data, [1.8*inch, 1.5*inch, 2*inch, 1.2*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Price Target Rationale:</b> The consensus $295 2026 target (+30%) reflects AWS growth reacceleration, advertising "
        "scaling, and AI infrastructure monetization. Conservative investors should expect $255-$270 range (+12-19%), while "
        "aggressive scenarios (full AI thesis playing out) support $300-$320 (+32-41%).",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== STRATEGY RECOMMENDATIONS ==========
    story.append(Paragraph("7. Strategy Recommendations", styles['SectionHeading']))

    story.append(Paragraph("<b>Investment Thesis Summary</b>", styles['SubHeading']))
    thesis_ratings = [
        ["Thesis Component", "Rating (1-10)", "Rationale"],
        ["AWS Growth Acceleration", "9/10", "20% Q3 growth, 30%+ projected, AI-driven demand"],
        ["AI Infrastructure Leadership", "9/10", "Trainium success, Bedrock scale, $125B capex commitment"],
        ["Advertising Revenue Growth", "8/10", "$60B → $70B+ trajectory, Prime Video upside"],
        ["E-commerce Market Position", "9/10", "40% market share, 75% Prime penetration—unassailable"],
        ["Valuation Entry Point", "7/10", "30 PE is premium but justified by multi-engine growth"],
        ["2026 Catalyst Certainty", "8/10", "Multiple confirmed catalysts, not speculative"],
    ]
    story.append(create_table(thesis_ratings, [2.5*inch, 1.5*inch, 2.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Position Sizing Recommendation</b>", styles['SubHeading']))
    sizing_data = [
        ["Portfolio Type", "Recommended Position", "Rationale"],
        ["Aggressive Growth (Your Profile)", "10-15%", "Large enough for impact, respects correlation"],
        ["Balanced Growth", "7-10%", "Conservative exposure to mega-cap tech"],
        ["Income-Focused", "0-5%", "AMZN pays no dividend, not suitable for Layer 2"],
        ["Conservative", "5-7%", "Defensive mega-cap with multiple moats"],
    ]
    story.append(create_table(sizing_data, [2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph(
        "<b>Your Portfolio Context:</b> With existing tech exposure (PLTR, TSLA, NVDA, VOO), adding 10-15% AMZN increases "
        "concentration risk but offers differentiated growth drivers (AWS services, advertising, e-commerce vs pure-play tech). "
        "AMZN's high VOO correlation (0.759) means it tracks market closely—good for reducing portfolio volatility vs adding "
        "another high-beta name.",
        styles['BodyText']
    ))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Entry Strategy</b>", styles['SubHeading']))
    entry_strategies = [
        "• <b>Immediate Entry (50% position):</b> Oversold conditions (Stochastic, Williams %R) + narrow Bollinger Bands suggest potential reversal. Deploy half position now ($226-$230 range).",
        "• <b>Dollar-Cost Average (Remaining 50%):</b> Split over 3-6 months to average down if pullback, average up if breakout confirms.",
        "• <b>MACD Confirmation Entry:</b> Wait for MACD bullish crossover (MACD line crosses above signal line) before entering—reduces risk but may sacrifice 5-10% upside.",
        "• <b>Support Level Entry:</b> Set limit orders at $218 (Bollinger lower band) and $210 (next support) for opportunistic fills.",
    ]
    for strategy in entry_strategies:
        story.append(Paragraph(strategy, styles['BulletPoint']))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Risk Management</b>", styles['SubHeading']))
    risk_mgmt = [
        "• <b>Stop Loss:</b> Set at $216.63 (current price $226.76 - 2x ATR $10.13). Adjust upward as position moves in your favor.",
        "• <b>Take Profit Targets:</b> 25% at $260 (+15%), 25% at $295 (+30%), 50% hold for $350+ long-term.",
        "• <b>Rebalancing Trigger:</b> If AMZN position exceeds 20% due to appreciation, trim to maintain portfolio balance.",
        "• <b>Catalyst Monitoring:</b> Track AWS quarterly revenue growth, advertising segment performance, Trainium deployment milestones.",
    ]
    for item in risk_mgmt:
        story.append(Paragraph(item, styles['BulletPoint']))

    story.append(PageBreak())

    # ========== RISKS ==========
    story.append(Paragraph("8. Risk Analysis", styles['SectionHeading']))

    story.append(Paragraph("<b>Key Risks</b>", styles['SubHeading']))
    risks_data = [
        ["Risk Category", "Description", "Severity", "Mitigation"],
        ["Valuation Premium", "30 PE is expensive; vulnerable to multiple compression", "MEDIUM", "Strong growth justifies premium; diversify entry"],
        ["AWS Competition", "Microsoft Azure, Google Cloud intensifying AI competition", "MEDIUM", "AWS market leadership + Trainium differentiation"],
        ["Regulatory Scrutiny", "Antitrust concerns, potential breakup scenarios", "MEDIUM", "Diversified business units operate independently"],
        ["AI Capex Risk", "$125B+ spend may not generate expected returns", "MEDIUM-HIGH", "Early Trainium success validates investment thesis"],
        ["E-commerce Saturation", "US market share may have peaked at 40%", "LOW", "International expansion + advertising offset"],
        ["Margin Compression", "Competition forcing price cuts", "LOW", "AWS + advertising provide margin cushion"],
    ]
    story.append(create_table(risks_data, [1.5*inch, 2*inch, 1*inch, 2*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Valuation Risk: Is 30 PE Too High?</b>", styles['SubHeading']))
    story.append(Paragraph(
        "AMZN's historical average PE is ~60-80 during growth phases, ~20-30 during mature phases. Current 30 PE is at the "
        "lower end of the range, suggesting market is pricing in 2025 underperformance but NOT fully pricing in 2026 AI catalysts. "
        "If AWS sustains 30% growth and Bedrock scales as projected, 35-40 PE is justified—implying $260-$300 price targets are "
        "achievable without multiple expansion.",
        styles['BodyText']
    ))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>What Could Go Wrong?</b>", styles['SubHeading']))
    downside_scenarios = [
        "• <b>AWS Growth Stalls:</b> If AWS decelerates to <15% growth, destroys investment thesis → SELL signal",
        "• <b>Trainium Adoption Fails:</b> Customers prefer Nvidia chips, custom silicon ROI collapses → downgrade to HOLD",
        "• <b>Regulatory Breakup:</b> Government forces AWS spinoff → short-term negative, long-term unlocks value",
        "• <b>Macro Recession:</b> Consumer spending crunch + AWS enterprise budget cuts → expect $180-$200 range",
        "• <b>AI Hype Deflation:</b> If AI fails to deliver enterprise value, capex cuts likely → $200-$220 consolidation",
    ]
    for scenario in downside_scenarios:
        story.append(Paragraph(scenario, styles['BulletPoint']))

    story.append(PageBreak())

    # ========== FINAL VERDICT ==========
    story.append(Paragraph("9. Final Verdict & Action Plan", styles['SectionHeading']))

    story.append(Paragraph("<b>Overall Rating: STRONG BUY</b>", styles['SubHeading']))

    verdict_summary = [
        ["Category", "Score (1-10)", "Justification"],
        ["Growth Potential", "9/10", "Multi-engine growth: AWS, AI, advertising, e-commerce"],
        ["Competitive Position", "9/10", "Market leadership across all segments"],
        ["Financial Strength", "8/10", "AWS 66% operating margin, strong cash flow"],
        ["Valuation", "7/10", "30 PE premium justified by growth, not cheap but fair"],
        ["Risk-Reward", "8/10", "30%+ upside, manageable downside with stops"],
        ["2026 Catalyst Certainty", "9/10", "Confirmed investments, not speculative bets"],
        ["<b>OVERALL RATING</b>", "<b>8.3/10</b>", "<b>STRONG BUY for 2026 watchlist</b>"],
    ]
    story.append(create_table(verdict_summary, [2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Action Plan for Ossie's Portfolio</b>", styles['SubHeading']))
    action_plan = [
        ["Action", "Timeline", "Details"],
        ["Initial Position (5-7%)", "Immediate", "Enter at $226-$230 to capture oversold bounce"],
        ["Scale to 10%", "Jan-Feb 2026", "Add on MACD confirmation or dip to $218 support"],
        ["Monitor AWS Q4 Earnings", "Late Jan 2026", "Confirm 20%+ growth continues—buy signal"],
        ["Scale to 15% (if bullish)", "Mar-Apr 2026", "If AWS >25% growth + Bedrock traction, max position"],
        ["Take Profit 25%", "Mid-2026", "At $260-$270 (+15-20%), lock gains"],
        ["Hold 75% Long-Term", "2027+", "Ride AWS/AI/advertising secular trends to $350+"],
    ]
    story.append(create_table(action_plan, [2*inch, 1.5*inch, 3*inch]))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Key Monitoring Metrics (Track Quarterly)</b>", styles['SubHeading']))
    monitoring = [
        "• <b>AWS Revenue Growth:</b> Must maintain 20%+ YoY (target: 25-30%)",
        "• <b>Advertising Revenue:</b> Track quarterly to $70B+ 2026 target",
        "• <b>Trainium Deployments:</b> Watch for customer adoption announcements, chip volume milestones",
        "• <b>Bedrock Customer Count:</b> Growth from 100K+ organizations signals AI traction",
        "• <b>Operating Margin:</b> Watch for expansion (custom silicon cost savings + advertising scale)",
        "• <b>Capex Guidance:</b> Confirm 2026 capex >$125B signals continued AI commitment",
    ]
    for metric in monitoring:
        story.append(Paragraph(metric, styles['BulletPoint']))

    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("<b>Investment Thesis in One Sentence</b>", styles['SubHeading']))
    story.append(Paragraph(
        "Amazon's 2025 underperformance (+4%) created an attractive entry point for a multi-engine growth story (AWS reaccelerating, "
        "AI infrastructure scaling, advertising exploding) with 30%+ upside to $295 by end-2026, backed by confirmed catalysts "
        "($125B+ capex, Trainium success, Bedrock adoption), making it a STRONG BUY for aggressive growth portfolios.",
        styles['BodyText']
    ))

    story.append(PageBreak())

    # ========== SOURCES ==========
    story.append(Paragraph("10. Sources & Citations", styles['SectionHeading']))

    sources_data = [
        ["Source", "Data Used", "Date"],
        ["Yahoo Finance (yfinance)", "Price data, risk metrics, technical analysis", "Dec 17, 2025"],
        ["The Motley Fool", "2026 price predictions, AWS analysis", "Dec 10, 2025"],
        ["Benzinga", "Price forecasts, market outlook", "2025"],
        ["CoinCodex", "Stock price predictions 2025-2030", "2025"],
        ["Long Forecast", "Amazon share price predictions", "2025"],
        ["About Amazon (Official)", "AWS re:Invent 2025, Trainium chips, Nova models", "Dec 2025"],
        ["TechCrunch", "AWS AI chip roadmap, Trainium3 details", "Dec 2, 2025"],
        ["The AI Insider", "AWS AI hardware strategy, Nvidia competition", "Dec 4, 2025"],
        ["WARC Media", "Advertising revenue forecasts 2025-2026", "2025"],
        ["eMarketer", "E-commerce market share, advertising stats", "2025"],
        ["Sequence Commerce", "Amazon advertising statistics 2025", "2025"],
        ["Finance Guru CLI Tools", "Risk metrics, momentum, volatility, correlation", "Dec 18, 2025"],
    ]
    story.append(create_table(sources_data, [2.2*inch, 2.8*inch, 1.5*inch]))

    story.append(Spacer(1, 0.5*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=LIGHT_GRAY))
    story.append(Spacer(1, 0.2*inch))

    # Footer
    footer_text = """<b>COMPLIANCE DISCLAIMERS</b><br/>
    • Educational Analysis: This report is for educational purposes only and does not constitute personalized investment advice.<br/>
    • No Guarantee: Past performance does not guarantee future results. All investments involve risk of loss.<br/>
    • Professional Advice: Consult a licensed financial advisor before making any investment decisions.<br/>
    • Risk Disclosure: Amazon.com stock involves significant risk, including volatility, competition, regulatory changes, and macroeconomic factors.<br/><br/>
    <b>Report ID:</b> AMZN-2026-WATCHLIST-001 | <b>Version:</b> 1.0.0<br/>
    Generated by Finance Guru™ v2.0.0 | BMAD-CORE™ v6.0.0<br/>
    December 18, 2025"""
    story.append(Paragraph(footer_text, styles['Footer']))

    # Build the PDF
    doc.build(story)
    print(f"✅ PDF Report generated: {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    build_report()
