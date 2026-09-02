# StyleGuide - Finance Guru Report Branding

Brand standards for Finance Guru PDF reports.

## Color Palette

```python
# Primary Colors
NAVY = "#1a365d"       # Brand primary - titles, headers, borders
GOLD = "#d69e2e"       # Accents, highlights, separators
GREEN = "#38a169"      # Positive signals, buy ratings
RED = "#e53e3e"        # Warnings, risks, sell signals

# Neutral Colors
DARK_GRAY = "#2d3748"  # Body text
LIGHT_GRAY = "#e2e8f0" # Table backgrounds, alternating rows
WHITE = "#ffffff"      # Page background
BLACK = "#000000"      # Emphasis text
```

## Typography Hierarchy

| Element | Font | Size | Color | Alignment |
|---------|------|------|-------|-----------|
| Brand Header | Helvetica-Bold | 24pt | Navy | Center |
| Subtitle | Helvetica | 14pt | Gold | Center |
| Section Header | Helvetica-Bold | 16pt | Navy | Left |
| Subsection | Helvetica-Bold | 12pt | Navy | Left |
| Body Text | Helvetica | 10pt | Dark Gray | Justified |
| Bullet Points | Helvetica | 10pt | Dark Gray | Left |
| Disclaimer | Helvetica-Oblique | 8pt | Dark Gray | Center |
| Footer | Helvetica | 8pt | Dark Gray | Center |

## Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    0.5" top margin                          │
├─────┬─────────────────────────────────────────────────┬─────┤
│     │                                                 │     │
│0.5" │             CONTENT AREA (7.5" wide)            │0.5" │
│     │                                                 │     │
│     │     Page Size: 8.5" x 11" (letter)             │     │
│     │     Content Width: 7.5"                         │     │
│     │     Content Height: 10"                         │     │
│     │                                                 │     │
├─────┴─────────────────────────────────────────────────┴─────┤
│                    0.5" bottom margin                       │
└─────────────────────────────────────────────────────────────┘
```

**Margins**: 0.5 inches all sides (tighter than default for more content)

## VGT-Style Header Format

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    FINANCE GURU™                            │
│             Family Office Investment Analysis               │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│              VGT - Vanguard Information Technology ETF      │
│           2026 Watchlist Analysis & Investment Report       │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Report Date:      December 18, 2025                        │
│  Analyst Team:     Finance Guru Multi-Agent System          │
│                    • Market Researcher (Dr. Aleksandr Petrov) │
│                    • Quant Analyst                          │
│                    • Strategy Advisor                       │
│  Current Price:    <market price>                           │
│  YTD Performance:  +24.89%                                  │
│  Expense Ratio:    0.10%                                    │
└─────────────────────────────────────────────────────────────┘
```

## Table Styling

### ⚠️ CRITICAL: Text Wrapping in Tables

**PROBLEM**: Plain strings in ReportLab tables DO NOT wrap. They overflow cell boundaries.

**SOLUTION**: Wrap ALL table cell content in `Paragraph` objects.

```python
# ❌ WRONG - Text will overflow
data = [
    ['Metric', 'This is a very long description that will overflow'],
]

# ✅ CORRECT - Text wraps within cell
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

cell_style = ParagraphStyle(
    name='TableCell',
    fontSize=9,
    fontName='Helvetica',
    wordWrap='CJK'  # Enables better word wrapping
)

data = [
    [Paragraph('Metric', cell_style),
     Paragraph('This is a very long description that will wrap nicely', cell_style)],
]
```

### Column Width Guidelines

Page content width = 7.5 inches. Table widths MUST fit within this.

| Table Type | Columns | Width Distribution |
|------------|---------|-------------------|
| 2-column | Label, Value | 2" + 5.5" = 7.5" |
| 3-column | Metric, Value, Assessment | 2" + 2" + 3.5" = 7.5" |
| 4-column | Metric, Value, Benchmark, Assessment | 1.5" + 1.5" + 1.5" + 3" = 7.5" |

### Header Row
```python
('BACKGROUND', (0, 0), (-1, 0), NAVY)
# Note: Text color handled by TableHeaderCell ParagraphStyle (white text)
('BOTTOMPADDING', (0, 0), (-1, 0), 10)
('TOPPADDING', (0, 0), (-1, 0), 10)
```

### Data Rows
```python
('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GRAY])  # Alternating
# Note: Font styling handled by TableCell ParagraphStyle
('TOPPADDING', (0, 1), (-1, -1), 8)
('BOTTOMPADDING', (0, 1), (-1, -1), 8)
('LEFTPADDING', (0, 0), (-1, -1), 6)
('RIGHTPADDING', (0, 0), (-1, -1), 6)
('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
('GRID', (0, 0), (-1, -1), 0.5, DARK_GRAY)
```

## Verdict Box Styling

### Strong Buy (Green)
```python
('BACKGROUND', (0, 0), (-1, 0), GREEN)
('TEXTCOLOR', (0, 0), (-1, 0), WHITE)
('FONTSIZE', (0, 0), (-1, 0), 14)
```

### Conditional Buy (Gold)
```python
('BACKGROUND', (0, 0), (-1, 0), GOLD)
('TEXTCOLOR', (0, 0), (-1, 0), BLACK)
```

### Hold (Light Gray)
```python
('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY)
('TEXTCOLOR', (0, 0), (-1, 0), BLACK)
```

### Sell (Red)
```python
('BACKGROUND', (0, 0), (-1, 0), RED)
('TEXTCOLOR', (0, 0), (-1, 0), WHITE)
```

## Section Separators

### Horizontal Rule
```python
HRFlowable(width="100%", thickness=2, color=NAVY)
```

### Section Spacer
```python
Spacer(1, 0.3*inch)  # Standard between sections
Spacer(1, 0.15*inch) # Small within sections
```

## Disclaimer Text - UNIFORM STANDARD

**FORMAT (matching FTNT analysis):**

```
─────────────────────────────────────────────────────────────
DISCLAIMER: This analysis is provided for educational and informational
purposes only. It does not constitute investment advice, financial advice,
trading advice, or any other sort of advice. Finance Guru is a personal
family office system and does not provide recommendations to third parties.
Past performance is not indicative of future results. All investments
involve risk, including the possible loss of principal. Consult with a
qualified financial professional before making any investment decisions.

                    Powered by Finance Guru™
                   Report Date: {date_display}
─────────────────────────────────────────────────────────────
```

**CRITICAL REQUIREMENTS:**
- "Powered by Finance Guru™" is REQUIRED on every report
- Must be bold, Navy color, centered
- Report date below in italics
- Horizontal rule separators above and below

### Disclaimer Style Code
```python
# Disclaimer text style
disclaimer_style = ParagraphStyle(
    name='Disclaimer',
    fontSize=8,
    textColor=DARK_GRAY,
    alignment=TA_CENTER,
    fontName='Helvetica-Oblique'
)

# "Powered by Finance Guru™" branding style
powered_by_style = ParagraphStyle(
    name='PoweredBy',
    fontSize=9,
    fontName='Helvetica-Bold',
    textColor=NAVY,
    alignment=TA_CENTER,
    spaceAfter=4
)
```

## ReportLab Import Template

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether, Image
)

# Brand Colors
NAVY = HexColor("#1a365d")
GOLD = HexColor("#d69e2e")
GREEN = HexColor("#38a169")
RED = HexColor("#e53e3e")
DARK_GRAY = HexColor("#2d3748")
LIGHT_GRAY = HexColor("#e2e8f0")
```
