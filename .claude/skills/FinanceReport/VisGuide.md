# VisGuide - Chart Selection & Visualization Standards

Guide for selecting appropriate chart types in Finance Guru reports.

## Chart Selection Dictionary

| Data Question | Chart Type | When to Use |
|--------------|------------|-------------|
| How has price changed over time? | **Line Chart** | Price history, trend visualization |
| Compare values across categories | **Horizontal Bar** | Risk metrics comparison, sector weights |
| Show distribution of values | **Vertical Bar** | Monthly returns, volume |
| Relationship between two variables | **Scatter Plot** | Risk vs return, correlation |
| Part-to-whole relationship | **Pie/Donut** | Portfolio allocation, sector breakdown |
| Show correlation matrix | **Heatmap** | Multi-asset correlation |
| Cumulative changes | **Waterfall** | Return attribution, P&L breakdown |
| Technical indicators | **Multi-line** | RSI, MACD with price overlay |

## Chart Type Specifications

### Line Chart (Price History)
```python
# Use for: Price trends, moving averages
chart_config = {
    'type': 'line',
    'figsize': (7, 3),
    'dpi': 150,
    'color': NAVY,
    'linewidth': 1.5,
    'grid': True,
    'grid_alpha': 0.3
}
```

**When to use:**
- Showing price movement over 90-252 days
- Comparing actual vs benchmark
- Moving average crossovers

### Horizontal Bar (Comparison)
```python
# Use for: Comparing metrics across categories
chart_config = {
    'type': 'barh',
    'figsize': (7, 3),
    'colors': [NAVY, GREEN, GOLD],
    'edge_color': 'none'
}
```

**When to use:**
- Risk metrics comparison (Sharpe, Sortino, Beta)
- Sector weights
- Peer comparison

### Heatmap (Correlation)
```python
# Use for: Correlation matrices
chart_config = {
    'type': 'heatmap',
    'figsize': (6, 5),
    'cmap': 'RdYlGn',  # Red=negative, Yellow=neutral, Green=positive
    'annot': True,
    'fmt': '.2f',
    'vmin': -1,
    'vmax': 1
}
```

**When to use:**
- Portfolio correlation analysis
- Sector interdependence
- Factor exposure

### Technical Indicator Chart
```python
# Use for: RSI, MACD overlays
chart_config = {
    'type': 'multi_axis',
    'figsize': (7, 4),
    'primary': {'color': NAVY, 'label': 'Price'},
    'secondary': {'color': GOLD, 'label': 'RSI'},
    'threshold_lines': [30, 70]  # Overbought/oversold
}
```

**When to use:**
- RSI with price
- MACD signal crossovers
- Bollinger Band visualization

## Color Coding Standards

### Signal Colors
| Signal | Color | Hex | Use Case |
|--------|-------|-----|----------|
| Positive/Buy | Green | #38a169 | Gains, uptrends, buy signals |
| Negative/Sell | Red | #e53e3e | Losses, downtrends, sell signals |
| Neutral/Hold | Gold | #d69e2e | Sideways, mixed signals |
| Primary | Navy | #1a365d | Default chart elements |

### Gradient Scales
```python
# For heatmaps and intensity charts
positive_scale = ['#c6f6d5', '#68d391', '#38a169', '#276749']  # Light to dark green
negative_scale = ['#fed7d7', '#fc8181', '#e53e3e', '#c53030']  # Light to dark red
neutral_scale = ['#edf2f7', '#a0aec0', '#718096', '#4a5568']   # Light to dark gray
```

## Labeling Standards

### Chart Title
- Font: Helvetica-Bold
- Size: 11pt
- Position: Above chart, left-aligned
- Example: "90-Day Price Performance vs SPY"

### Axis Labels
- Font: Helvetica
- Size: 9pt
- X-axis: Date format "MMM 'YY" (e.g., "Dec '25")
- Y-axis: Numeric with appropriate units ($, %, bp)

### Legend
- Position: Upper right or lower right (not covering data)
- Font: Helvetica, 8pt
- Box: Light gray background, thin border

### Annotations
- Font: Helvetica, 8pt
- Use sparingly for key events
- Arrow pointing to data point

## Chart Embedding in PDF

### Using matplotlib + ReportLab
```python
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.platypus import Image

def create_embedded_chart(data, chart_type, title):
    """Generate chart and return as ReportLab Image."""
    fig, ax = plt.subplots(figsize=(7, 3), dpi=150)

    # Plot data based on chart_type
    if chart_type == 'line':
        ax.plot(data['dates'], data['values'], color='#1a365d', linewidth=1.5)
    elif chart_type == 'barh':
        ax.barh(data['labels'], data['values'], color='#1a365d')

    ax.set_title(title, fontsize=11, fontweight='bold', loc='left')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    # Save to buffer
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    plt.close(fig)

    # Return as ReportLab Image
    return Image(buffer, width=6.5*inch, height=2.5*inch)
```

### Chart Sizing Guidelines
| Chart Purpose | Width | Height |
|---------------|-------|--------|
| Full-width main chart | 6.5" | 3.0" |
| Half-width comparison | 3.0" | 2.5" |
| Small indicator | 2.5" | 1.5" |
| Correlation heatmap | 5.0" | 4.5" |

## Data Source Integration

### From Finance Guru CLI Tools
```python
import subprocess
import json
import sys

def get_chart_data(ticker, module, days=90):
    """Run CLI tool and parse JSON output for charting."""
    result = subprocess.run(
        [sys.executable, '-m', module, ticker, '--days', str(days), '--output', 'json'],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

# Example usage
risk_data = get_chart_data('TSLA', 'src.analysis.risk_metrics_cli', 252)
momentum_data = get_chart_data('TSLA', 'src.utils.momentum_cli', 90)
```

## Accessibility Notes

- Always include alt-text description for charts
- Use patterns in addition to colors for colorblind accessibility
- Ensure sufficient contrast (WCAG AA: 4.5:1 ratio)
- Provide data tables as fallback for complex visualizations
