#!/usr/bin/env python3
"""Generate PDF reports for IREN, GOOG, MSFT, SOFI, VTV"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from pathlib import Path

BRAND_NAVY = HexColor("#1a365d")
BRAND_GOLD = HexColor("#d69e2e")
BRAND_GREEN = HexColor("#38a169")
BRAND_ORANGE = HexColor("#dd6b20")
BRAND_GRAY = HexColor("#718096")

def create_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle', parent=styles['Heading1'], fontSize=24, textColor=BRAND_NAVY, spaceAfter=20, alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SectionHeader', parent=styles['Heading2'], fontSize=14, textColor=BRAND_NAVY, spaceBefore=15, spaceAfter=10))
    styles.add(ParagraphStyle(name='SubSection', parent=styles['Heading3'], fontSize=12, textColor=BRAND_NAVY, spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name='ReportBody', parent=styles['Normal'], fontSize=10, spaceAfter=8, leading=14))
    styles.add(ParagraphStyle(name='VerdictBuy', parent=styles['Heading1'], fontSize=18, textColor=BRAND_GREEN, alignment=TA_CENTER, spaceBefore=10, spaceAfter=10))
    styles.add(ParagraphStyle(name='VerdictSpec', parent=styles['Heading1'], fontSize=18, textColor=BRAND_ORANGE, alignment=TA_CENTER, spaceBefore=10, spaceAfter=10))
    styles.add(ParagraphStyle(name='VerdictHold', parent=styles['Heading1'], fontSize=18, textColor=BRAND_GRAY, alignment=TA_CENTER, spaceBefore=10, spaceAfter=10))
    styles.add(ParagraphStyle(name='Disclaimer', parent=styles['Normal'], fontSize=8, textColor=BRAND_GRAY, alignment=TA_CENTER, spaceBefore=20))
    return styles

def create_table(data, col_widths=None):
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_NAVY), ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10), ('BOTTOMPADDING', (0, 0), (-1, 0), 10), ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor("#f7fafc")), ('TEXTCOLOR', (0, 1), (-1, -1), black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6), ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, BRAND_GRAY), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return table

def generate_report(ticker, company, sector, price, verdict, verdict_type, thesis_data, quant_data, catalysts, risks, recommendation, key_insight, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = create_styles()
    story = []
    story.append(Paragraph("Finance Guru™", styles['ReportTitle']))
    story.append(Paragraph("2026 Watchlist Analysis Report", styles['SubSection']))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GOLD))
    story.append(Spacer(1, 10))
    ticker_info = [["Ticker", ticker], ["Company", company], ["Sector", sector], ["Current Price", price], ["Analysis Date", datetime.now().strftime("%B %d, %Y")]]
    story.append(create_table(ticker_info, col_widths=[2*inch, 4.5*inch]))
    story.append(Spacer(1, 20))
    verdict_style = 'VerdictBuy' if verdict_type == 'buy' else ('VerdictSpec' if verdict_type == 'spec' else 'VerdictHold')
    story.append(Paragraph(f"VERDICT: {verdict}", styles[verdict_style]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Investment Thesis Summary", styles['SectionHeader']))
    story.append(create_table(thesis_data, col_widths=[2*inch, 3*inch, 1.5*inch]))
    story.append(Spacer(1, 15))
    if key_insight:
        story.append(Paragraph(f"<b>Key Insight:</b> {key_insight}", styles['ReportBody']))
        story.append(Spacer(1, 10))
    story.append(Paragraph("Quantitative Analysis", styles['SectionHeader']))
    story.append(create_table(quant_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 15))
    story.append(Paragraph("2026 Catalysts", styles['SectionHeader']))
    story.append(create_table(catalysts, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Key Risks", styles['SectionHeader']))
    story.append(create_table(risks, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GOLD))
    story.append(Spacer(1, 10))
    final_table = Table(recommendation, colWidths=[6.5*inch])
    bg_color = HexColor("#e6fffa") if verdict_type == 'buy' else (HexColor("#fefcbf") if verdict_type == 'spec' else HexColor("#f7fafc"))
    final_table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), BRAND_NAVY), ('TEXTCOLOR', (0, 0), (-1, 0), white), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 12), ('BACKGROUND', (0, 1), (-1, -1), bg_color), ('TEXTCOLOR', (0, 1), (-1, -1), BRAND_NAVY), ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 11), ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 8), ('GRID', (0, 0), (-1, -1), 1, BRAND_NAVY)]))
    story.append(final_table)
    story.append(Spacer(1, 20))
    story.append(Paragraph("⚠️ DISCLAIMER: All Finance Guru™ outputs are for educational purposes only. Not investment advice.", styles['Disclaimer']))
    story.append(Paragraph(f"Finance Guru™ v2.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Disclaimer']))
    doc.build(story)
    print(f"✅ {ticker}: {output_path}")

output_dir = Path("/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports")
output_dir.mkdir(parents=True, exist_ok=True)
date_str = datetime.now().strftime('%Y-%m-%d')

# IREN Report
generate_report(
    ticker="IREN", company="Iris Energy Limited", sector="AI Cloud / Bitcoin Mining / Data Centers",
    price="$35.80 (+5.98%)", verdict="SPECULATIVE BUY ⚠️", verdict_type="spec",
    thesis_data=[["Dimension", "Assessment", "Rating"], ["Business Quality", "Pivoting from BTC to AI cloud", "★★★★☆"], ["Growth Trajectory", "$9.7B Microsoft contract", "★★★★★"], ["Valuation", "High growth premium", "★★★☆☆"], ["Volatility", "EXTREME (98% annual)", "★☆☆☆☆"], ["Portfolio Fit", "Similar to APLD - data center", "★★★☆☆"], ["Risk Level", "HIGH RISK / HIGH REWARD", "★★☆☆☆"]],
    key_insight="$9.7B 5-year Microsoft contract secured. Targeting $3.4B AI Cloud ARR by end of 2026. Transitioning from Bitcoin mining to GPU cloud services.",
    quant_data=[["Metric", "Value", "Interpretation"], ["VaR (95%)", "-9.61%", "Extreme daily risk"], ["Sharpe Ratio", "1.32", "Good risk-adjusted"], ["Max Drawdown", "-65.56%", "EXTREME"], ["Annual Volatility", "97.75%", "EXTREME"], ["Beta vs SPY", "2.16", "Very high systematic risk"], ["Alpha vs SPY", "+110.46%", "EXCEPTIONAL"]],
    catalysts=[["Catalyst", "Details"], ["$9.7B Microsoft Contract", "5-year GPU cloud services deal"], ["AI Cloud Pivot", "Transition from BTC mining to AI infrastructure"], ["Childress 750MW", "Accelerating construction for MSFT"], ["$3.4B ARR Target", "By end of 2026"]],
    risks=[["Risk", "Impact"], ["Extreme Volatility", "98% annual vol, -66% max drawdown"], ["Execution Risk", "Must deliver on massive expansion"], ["Bitcoin Exposure", "Legacy BTC mining volatility"], ["Competition", "APLD, other data center operators"]],
    recommendation=[["FINAL RECOMMENDATION"], ["Action: SPECULATIVE BUY"], ["Size: 1-2% max ($2,500-$5,000)"], ["Note: Similar profile to APLD - consider one or the other"], ["Stop Loss: -30% from entry"], ["Time Horizon: 12-24 months"]],
    output_path=str(output_dir / f"IREN-analysis-{date_str}.pdf")
)

# GOOG Report
generate_report(
    ticker="GOOG", company="Alphabet Inc.", sector="Big Tech / AI / Cloud / Advertising",
    price="$303.75 (+1.91%)", verdict="BUY ✓", verdict_type="buy",
    thesis_data=[["Dimension", "Assessment", "Rating"], ["Business Quality", "Dominant AI/Search/Cloud leader", "★★★★★"], ["Growth Trajectory", "Gemini AI + Cloud momentum", "★★★★★"], ["Valuation", "Reasonable for big tech", "★★★★☆"], ["Volatility", "Medium (33% annual)", "★★★★☆"], ["Portfolio Fit", "Already own 6 shares GOOGL", "★★★★☆"], ["Risk Level", "Moderate", "★★★★☆"]],
    key_insight="Top AI stock for 2026. Gemini AI advancing rapidly. Could reach $4T market cap. Strong Sharpe (1.64) and alpha (+45%).",
    quant_data=[["Metric", "Value", "Interpretation"], ["VaR (95%)", "-2.93%", "Moderate daily risk"], ["Sharpe Ratio", "1.64", "Good risk-adjusted return"], ["Sortino Ratio", "2.62", "Excellent downside protection"], ["Max Drawdown", "-29.35%", "Manageable"], ["Annual Volatility", "32.76%", "Medium"], ["Beta vs SPY", "1.04", "Market average"], ["Alpha vs SPY", "+44.95%", "Strong outperformance"]],
    catalysts=[["Catalyst", "Details"], ["Gemini AI", "Advancing multimodal AI capabilities"], ["Cloud Growth", "Google Cloud Platform momentum"], ["YouTube/Ads", "AI-enhanced advertising"], ["Waymo", "Autonomous vehicle optionality"], ["$4T Potential", "Could reach $4T market cap in 2026"]],
    risks=[["Risk", "Impact"], ["Regulatory", "DOJ antitrust concerns"], ["AI Competition", "OpenAI, Anthropic, Meta challenging"], ["Ad Market", "Economic sensitivity"], ["Execution", "AI monetization must accelerate"]],
    recommendation=[["FINAL RECOMMENDATION"], ["Action: BUY (Add to existing position)"], ["Size: 3-5% ($7,500-$12,500)"], ["Note: Already own 6 shares GOOGL"], ["Entry: Now or on dips to $280-290"], ["Time Horizon: 12-36 months"]],
    output_path=str(output_dir / f"GOOG-analysis-{date_str}.pdf")
)

# MSFT Report
generate_report(
    ticker="MSFT", company="Microsoft Corporation", sector="Big Tech / AI / Cloud / Enterprise",
    price="$483.98 (+1.65%)", verdict="HOLD / WAIT ⏸️", verdict_type="hold",
    thesis_data=[["Dimension", "Assessment", "Rating"], ["Business Quality", "Best-in-class enterprise tech", "★★★★★"], ["Growth Trajectory", "Azure 40% growth, Copilot", "★★★★☆"], ["Valuation", "Premium (expensive)", "★★★☆☆"], ["Volatility", "Medium (24% annual)", "★★★★☆"], ["Portfolio Fit", "Would add big tech exposure", "★★★☆☆"], ["Recent Performance", "Underperforming SPY", "★★☆☆☆"]],
    key_insight="Despite Azure 40% growth and Copilot momentum, MSFT is underperforming SPY with negative alpha (-1.22%). Wall Street targets $625-650 but poor Sharpe (0.26) suggests wait for better entry.",
    quant_data=[["Metric", "Value", "Interpretation"], ["VaR (95%)", "-2.34%", "Low daily risk"], ["Sharpe Ratio", "0.26", "POOR risk-adjusted return"], ["Sortino Ratio", "0.40", "Poor downside protection"], ["Max Drawdown", "-21.83%", "Manageable"], ["Annual Volatility", "24.32%", "Medium"], ["Beta vs SPY", "0.88", "Slightly defensive"], ["Alpha vs SPY", "-1.22%", "Underperforming!"]],
    catalysts=[["Catalyst", "Details"], ["Azure AI", "40% growth, AI workloads"], ["Copilot", "Enterprise AI adoption"], ["OpenAI Partnership", "GPT integration across products"], ["Gaming", "Xbox/Activision synergies"], ["$650 Target", "Wall Street consensus"]],
    risks=[["Risk", "Impact"], ["Valuation", "Premium pricing limits upside"], ["Underperformance", "Negative alpha vs SPY"], ["Competition", "AWS, Google Cloud in cloud"], ["Execution", "AI monetization expectations high"]],
    recommendation=[["FINAL RECOMMENDATION"], ["Action: HOLD / WAIT FOR DIP"], ["Reason: Poor Sharpe (0.26), negative alpha"], ["Better Entry: Wait for $420-450 dip"], ["Alternative: GOOG offers better risk-adjusted returns"], ["If must buy: Small position only (2%)"]],
    output_path=str(output_dir / f"MSFT-analysis-{date_str}.pdf")
)

# SOFI Report
generate_report(
    ticker="SOFI", company="SoFi Technologies Inc.", sector="Fintech / Digital Banking",
    price="$26.29 (+4.04%)", verdict="ADD TO POSITION ✓", verdict_type="buy",
    thesis_data=[["Dimension", "Assessment", "Rating"], ["Business Quality", "Leading digital bank/fintech", "★★★★☆"], ["Growth Trajectory", "Strong member growth", "★★★★☆"], ["Valuation", "Growth premium reasonable", "★★★☆☆"], ["Volatility", "High (64% annual)", "★★☆☆☆"], ["Portfolio Fit", "Already own 29 shares (+81%)", "★★★★★"], ["Risk Level", "High but you know it", "★★★☆☆"]],
    key_insight="Already own 29 shares with +81% gain. Strong alpha (+43%) but high volatility. Fintech provides diversification from pure tech. Consider adding on pullbacks.",
    quant_data=[["Metric", "Value", "Interpretation"], ["VaR (95%)", "-6.29%", "High daily risk"], ["Sharpe Ratio", "0.98", "Borderline acceptable"], ["Sortino Ratio", "1.47", "Decent downside protection"], ["Max Drawdown", "-47.31%", "Significant"], ["Annual Volatility", "64.31%", "High"], ["Beta vs SPY", "2.41", "Very high systematic risk"], ["Alpha vs SPY", "+42.61%", "Strong outperformance"]],
    catalysts=[["Catalyst", "Details"], ["Bank Charter", "Full banking capabilities"], ["Member Growth", "Expanding user base"], ["Cross-Selling", "Loans, investing, banking"], ["Profitability", "Path to GAAP profitability"], ["Rate Environment", "Benefits from rate changes"]],
    risks=[["Risk", "Impact"], ["High Volatility", "64% annual vol, -47% max DD"], ["Fintech Competition", "Robinhood, traditional banks"], ["Regulatory", "Banking regulation changes"], ["Credit Risk", "Loan portfolio quality"]],
    recommendation=[["FINAL RECOMMENDATION"], ["Action: ADD TO POSITION"], ["Current: 29 shares (+81% gain)"], ["Add: 10-20 more shares on dips"], ["Target Add Price: $22-24 range"], ["Time Horizon: 12-24 months"]],
    output_path=str(output_dir / f"SOFI-analysis-{date_str}.pdf")
)

# VTV Report
generate_report(
    ticker="VTV", company="Vanguard Value ETF", sector="Value Factor ETF",
    price="$190.86 (-0.06%)", verdict="BUY (DIVERSIFIER) ✓", verdict_type="buy",
    thesis_data=[["Dimension", "Assessment", "Rating"], ["Business Quality", "Vanguard quality ETF", "★★★★★"], ["Growth Trajectory", "Defensive, steady", "★★★☆☆"], ["Valuation", "Value stocks = cheap", "★★★★★"], ["Volatility", "LOW (15% annual)", "★★★★★"], ["Portfolio Fit", "EXCELLENT diversifier", "★★★★★"], ["Risk Level", "Low", "★★★★★"]],
    key_insight="Your portfolio is heavily growth/tech weighted. VTV provides value factor exposure with LOW volatility (15%). Similar to BRK.B as defensive anchor. Not for alpha, for risk management.",
    quant_data=[["Metric", "Value", "Interpretation"], ["VaR (95%)", "-1.18%", "Very low daily risk"], ["Sharpe Ratio", "0.35", "Poor (value lagging growth)"], ["Sortino Ratio", "0.45", "Poor but stable"], ["Max Drawdown", "-13.75%", "Very manageable"], ["Annual Volatility", "15.22%", "LOW"], ["Beta vs SPY", "0.68", "Defensive"], ["Alpha vs SPY", "-0.50%", "Slight underperformance"]],
    catalysts=[["Catalyst", "Details"], ["Value Rotation", "If growth/tech corrects, value outperforms"], ["Dividend Income", "~2.3% yield"], ["Rate Normalization", "Value benefits in higher rate env"], ["Portfolio Balance", "Reduces overall portfolio risk"], ["Market Hedge", "Protects against growth selloff"]],
    risks=[["Risk", "Impact"], ["Value Lag", "Value has underperformed growth"], ["Slow Growth", "Lower return potential"], ["Opportunity Cost", "Money not in growth stocks"], ["No Alpha", "Won't beat market significantly"]],
    recommendation=[["FINAL RECOMMENDATION"], ["Action: BUY (Portfolio Diversifier)"], ["Size: 5-10% ($12,500-$25,000)"], ["Purpose: Risk management, not alpha"], ["Pairs With: BRK.B as defensive anchors"], ["Time Horizon: Long-term hold"]],
    output_path=str(output_dir / f"VTV-analysis-{date_str}.pdf")
)

print("\n✅ All 5 remaining reports generated!")
