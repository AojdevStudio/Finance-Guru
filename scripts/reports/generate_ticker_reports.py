#!/usr/bin/env python3
"""
Finance Guru™ - Generic Ticker Report Generator
Generates PDF reports for any ticker analysis
"""

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
BRAND_RED = HexColor("#e53e3e")
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


def generate_report(ticker: str, company: str, sector: str, price: str, verdict: str,
                   verdict_type: str, thesis_data: list, quant_data: list,
                   catalysts: list, risks: list, recommendation: list, key_insight: str,
                   output_path: str):
    """Generate a ticker analysis PDF report"""
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = create_styles()
    story = []

    # Header
    story.append(Paragraph("Finance Guru™", styles['ReportTitle']))
    story.append(Paragraph("2026 Watchlist Analysis Report", styles['SubSection']))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GOLD))
    story.append(Spacer(1, 10))

    # Ticker info
    ticker_info = [
        ["Ticker", ticker], ["Company", company], ["Sector", sector],
        ["Current Price", price], ["Analysis Date", datetime.now().strftime("%B %d, %Y")],
    ]
    story.append(create_table(ticker_info, col_widths=[2*inch, 4.5*inch]))
    story.append(Spacer(1, 20))

    # Verdict
    verdict_style = 'VerdictBuy' if verdict_type == 'buy' else ('VerdictSpec' if verdict_type == 'spec' else 'VerdictHold')
    story.append(Paragraph(f"VERDICT: {verdict}", styles[verdict_style]))
    story.append(Spacer(1, 10))

    # Investment Thesis
    story.append(Paragraph("Investment Thesis Summary", styles['SectionHeader']))
    story.append(create_table(thesis_data, col_widths=[2*inch, 3*inch, 1.5*inch]))
    story.append(Spacer(1, 15))

    # Key Insight
    if key_insight:
        story.append(Paragraph(f"<b>Key Insight:</b> {key_insight}", styles['ReportBody']))
        story.append(Spacer(1, 10))

    # Quantitative Analysis
    story.append(Paragraph("Quantitative Analysis", styles['SectionHeader']))
    story.append(create_table(quant_data, col_widths=[2*inch, 2*inch, 2.5*inch]))
    story.append(Spacer(1, 15))

    # Catalysts
    story.append(Paragraph("2026 Catalysts", styles['SectionHeader']))
    story.append(create_table(catalysts, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 15))

    # Risks
    story.append(Paragraph("Key Risks", styles['SectionHeader']))
    story.append(create_table(risks, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 15))

    # Recommendation
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_GOLD))
    story.append(Spacer(1, 10))
    final_table = Table(recommendation, colWidths=[6.5*inch])
    bg_color = HexColor("#e6fffa") if verdict_type == 'buy' else (HexColor("#fefcbf") if verdict_type == 'spec' else HexColor("#f7fafc"))
    final_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_NAVY), ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12), ('BACKGROUND', (0, 1), (-1, -1), bg_color),
        ('TEXTCOLOR', (0, 1), (-1, -1), BRAND_NAVY), ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11), ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8), ('GRID', (0, 0), (-1, -1), 1, BRAND_NAVY),
    ]))
    story.append(final_table)
    story.append(Spacer(1, 20))

    # Disclaimer
    story.append(Paragraph(
        "⚠️ DISCLAIMER: All Finance Guru™ outputs are for educational purposes only. "
        "Not investment advice. Consult professionals before investing.",
        styles['Disclaimer']
    ))
    story.append(Paragraph(f"Finance Guru™ v2.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Disclaimer']))

    doc.build(story)
    print(f"✅ Report generated: {output_path}")


# APLD Report
def generate_apld():
    output_dir = Path("/Users/ossieirondi/Documents/Irondi-Household/family-office/docs/fin-guru/analysis/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    generate_report(
        ticker="APLD",
        company="Applied Digital Corporation",
        sector="AI/HPC Data Center Infrastructure",
        price="$23.90 (+8.64%)",
        verdict="SPECULATIVE BUY ⚠️",
        verdict_type="spec",
        thesis_data=[
            ["Dimension", "Assessment", "Rating"],
            ["Business Quality", "AI data center infrastructure leader", "★★★★☆"],
            ["Growth Trajectory", "Earnings +105%/yr forecast", "★★★★★"],
            ["Valuation", "High growth premium", "★★★☆☆"],
            ["Volatility", "EXTREME (127% annual)", "★☆☆☆☆"],
            ["Portfolio Fit", "Low correlation, good diversifier", "★★★★☆"],
            ["Risk Level", "HIGH RISK / HIGH REWARD", "★★☆☆☆"],
        ],
        key_insight="NVIDIA-backed AI infrastructure play with $2.35B expansion funding. 200% yearly gains but 68% max drawdown history.",
        quant_data=[
            ["Metric", "Value", "Interpretation"],
            ["VaR (95%)", "-9.46%", "Extreme daily risk"],
            ["Sharpe Ratio", "1.19", "Good risk-adjusted return"],
            ["Max Drawdown", "-67.76%", "EXTREME"],
            ["Annual Volatility", "127.41%", "EXTREME"],
            ["Beta vs SPY", "2.17", "Very high systematic risk"],
            ["Alpha vs SPY", "+133.04%", "EXCEPTIONAL outperformance"],
            ["Williams %R", "-99.46", "Extremely oversold"],
            ["Correlation to PLTR", "0.285", "Low - good diversifier"],
        ],
        catalysts=[
            ["Catalyst", "Details"],
            ["AI Infrastructure Boom", "Riding NVIDIA GPU demand wave"],
            ["$2.35B Financing", "Senior secured notes for expansion"],
            ["Polaris Forge 100MW", "Phase II complete, ready for service"],
            ["HPC Revenue Growth", "Next-gen AI data centers"],
            ["Corintis Investment", "$25M for data center tech innovation"],
        ],
        risks=[
            ["Risk", "Impact"],
            ["Extreme Volatility", "127% annual vol, -68% max drawdown possible"],
            ["Execution Risk", "Must deliver on capacity expansion"],
            ["Funding Risk", "Heavy debt load from $2.35B notes"],
            ["Competition", "Other data center players entering"],
            ["Bitcoin Exposure", "Legacy crypto mining business"],
        ],
        recommendation=[
            ["FINAL RECOMMENDATION"],
            ["Action: SPECULATIVE BUY"],
            ["Size: 1-2% max ($2,500-$5,000)"],
            ["Entry: Now - Deeply oversold"],
            ["Stop Loss: -30% from entry"],
            ["Risk Level: EXTREME"],
            ["Time Horizon: 12-24 months"],
        ],
        output_path=str(output_dir / f"APLD-analysis-{datetime.now().strftime('%Y-%m-%d')}.pdf")
    )


if __name__ == "__main__":
    generate_apld()
