#!/usr/bin/env python3
"""ChartKit - Finance Guru Chart Generation CLI.

Generates publication-quality charts for PDF reports.
Supports line, bar, scatter, heatmap, and technical indicator charts.

Usage:
    uv run python ChartKit.py --ticker TSLA --chart-type line --days 90
    uv run python ChartKit.py --ticker TSLA --chart-type heatmap --tickers TSLA,PLTR,NVDA
"""

import argparse
import json
import subprocess
import sys
from io import BytesIO
from typing import Any

# Lazy loading for optional dependencies
_plt = None
_np = None


def _import_dependencies():
    """Import matplotlib and numpy lazily."""
    global _plt, _np
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        _plt = plt
        _np = np
    except ImportError:
        print("ChartKit requires matplotlib and numpy.")
        print("Install with: uv add matplotlib numpy")
        sys.exit(1)


# Finance Guru Brand Colors
COLORS = {
    "navy": "#1a365d",
    "gold": "#d69e2e",
    "green": "#38a169",
    "red": "#e53e3e",
    "dark_gray": "#2d3748",
    "light_gray": "#e2e8f0",
}


def run_cli_tool(tool_path: str, args: list[str]) -> dict[str, Any]:
    """Run a Finance Guru CLI tool and parse JSON output."""
    cmd = ["uv", "run", "python", tool_path] + args + ["--output", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running {tool_path}: {e.stderr}")
        return {}
    except json.JSONDecodeError:
        print(f"Error parsing JSON from {tool_path}")
        return {}


def create_line_chart(
    data: dict[str, Any],
    title: str,
    ylabel: str = "Price ($)",
    figsize: tuple = (7, 3),
    dpi: int = 150,
) -> BytesIO:
    """Create a line chart for price history or metrics."""
    _import_dependencies()

    fig, ax = _plt.subplots(figsize=figsize, dpi=dpi)

    if "dates" in data and "values" in data:
        ax.plot(data["dates"], data["values"], color=COLORS["navy"], linewidth=1.5)
    elif "x" in data and "y" in data:
        ax.plot(data["x"], data["y"], color=COLORS["navy"], linewidth=1.5)

    ax.set_title(title, fontsize=11, fontweight="bold", loc="left")
    ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="both", labelsize=8)

    # Rotate x-axis labels if dates
    if len(ax.get_xticklabels()) > 10:
        _plt.xticks(rotation=45, ha="right")

    _plt.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", facecolor="white")
    buffer.seek(0)
    _plt.close(fig)

    return buffer


def create_bar_chart(
    data: dict[str, Any],
    title: str,
    horizontal: bool = True,
    figsize: tuple = (7, 3),
    dpi: int = 150,
) -> BytesIO:
    """Create a bar chart for metric comparison."""
    _import_dependencies()

    fig, ax = _plt.subplots(figsize=figsize, dpi=dpi)

    labels = data.get("labels", [])
    values = data.get("values", [])

    # Color bars based on positive/negative
    colors = [COLORS["green"] if v >= 0 else COLORS["red"] for v in values]

    if horizontal:
        ax.barh(labels, values, color=colors)
        ax.set_xlabel(data.get("xlabel", ""), fontsize=9)
    else:
        ax.bar(labels, values, color=colors)
        ax.set_ylabel(data.get("ylabel", ""), fontsize=9)

    ax.set_title(title, fontsize=11, fontweight="bold", loc="left")
    ax.grid(True, alpha=0.3, axis="x" if horizontal else "y")
    ax.tick_params(axis="both", labelsize=8)

    _plt.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", facecolor="white")
    buffer.seek(0)
    _plt.close(fig)

    return buffer


def create_heatmap(
    correlation_matrix: list[list[float]],
    labels: list[str],
    title: str = "Correlation Matrix",
    figsize: tuple = (6, 5),
    dpi: int = 150,
) -> BytesIO:
    """Create a correlation heatmap."""
    _import_dependencies()

    fig, ax = _plt.subplots(figsize=figsize, dpi=dpi)

    matrix = _np.array(correlation_matrix)

    # Create heatmap
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=-1, vmax=1)

    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.tick_params(labelsize=8)

    # Set ticks and labels
    ax.set_xticks(_np.arange(len(labels)))
    ax.set_yticks(_np.arange(len(labels)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)

    # Rotate x labels
    _plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Add value annotations
    for i in range(len(labels)):
        for j in range(len(labels)):
            text_color = "white" if abs(matrix[i, j]) > 0.5 else "black"
            ax.text(
                j,
                i,
                f"{matrix[i, j]:.2f}",
                ha="center",
                va="center",
                color=text_color,
                fontsize=8,
            )

    ax.set_title(title, fontsize=11, fontweight="bold", loc="left")
    _plt.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", facecolor="white")
    buffer.seek(0)
    _plt.close(fig)

    return buffer


def create_technical_chart(
    price_data: list[float],
    indicator_data: list[float],
    dates: list[str],
    price_label: str = "Price",
    indicator_label: str = "RSI",
    thresholds: list[float] | None = None,
    title: str = "Technical Analysis",
    figsize: tuple = (7, 4),
    dpi: int = 150,
) -> BytesIO:
    """Create a dual-axis technical indicator chart."""
    _import_dependencies()

    fig, ax1 = _plt.subplots(figsize=figsize, dpi=dpi)

    # Primary axis (price)
    ax1.plot(dates, price_data, color=COLORS["navy"], linewidth=1.5, label=price_label)
    ax1.set_ylabel(price_label, color=COLORS["navy"], fontsize=9)
    ax1.tick_params(axis="y", labelcolor=COLORS["navy"], labelsize=8)
    ax1.tick_params(axis="x", labelsize=8)

    # Secondary axis (indicator)
    ax2 = ax1.twinx()
    ax2.plot(
        dates,
        indicator_data,
        color=COLORS["gold"],
        linewidth=1.2,
        label=indicator_label,
    )
    ax2.set_ylabel(indicator_label, color=COLORS["gold"], fontsize=9)
    ax2.tick_params(axis="y", labelcolor=COLORS["gold"], labelsize=8)

    # Add threshold lines
    if thresholds:
        for thresh in thresholds:
            ax2.axhline(
                y=thresh, color=COLORS["light_gray"], linestyle="--", linewidth=0.8
            )

    ax1.set_title(title, fontsize=11, fontweight="bold", loc="left")
    ax1.grid(True, alpha=0.3)

    # Rotate x-axis labels
    if len(dates) > 10:
        _plt.xticks(rotation=45, ha="right")

    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8)

    _plt.tight_layout()

    buffer = BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", facecolor="white")
    buffer.seek(0)
    _plt.close(fig)

    return buffer


def save_chart(buffer: BytesIO, output_path: str):
    """Save chart buffer to file."""
    with open(output_path, "wb") as f:
        f.write(buffer.getvalue())
    print(f"Chart saved to: {output_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ChartKit - Finance Guru Chart Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Generate line chart:
    uv run python ChartKit.py --ticker TSLA --chart-type line --days 90

  Generate heatmap:
    uv run python ChartKit.py --chart-type heatmap --tickers TSLA,PLTR,NVDA,AAPL

  Generate bar chart:
    uv run python ChartKit.py --chart-type bar --data '{"labels":["Sharpe","Sortino","Beta"],"values":[1.5,2.1,1.2]}'
        """,
    )

    parser.add_argument("--ticker", type=str, help="Stock ticker symbol")
    parser.add_argument(
        "--tickers", type=str, help="Comma-separated tickers for correlation"
    )
    parser.add_argument(
        "--chart-type",
        type=str,
        required=True,
        choices=["line", "bar", "barh", "heatmap", "technical"],
        help="Type of chart to generate",
    )
    parser.add_argument(
        "--days", type=int, default=90, help="Days of data (default: 90)"
    )
    parser.add_argument(
        "--data", type=str, help="JSON data for chart (alternative to CLI tools)"
    )
    parser.add_argument("--title", type=str, help="Chart title")
    parser.add_argument(
        "--output", type=str, default="chart.png", help="Output file path"
    )
    parser.add_argument(
        "--figsize", type=str, default="7,3", help="Figure size as width,height"
    )
    parser.add_argument("--dpi", type=int, default=150, help="Output DPI")

    args = parser.parse_args()

    # Parse figsize
    figsize = tuple(map(float, args.figsize.split(",")))

    # Generate chart based on type
    if args.chart_type == "line":
        if args.data:
            data = json.loads(args.data)
        else:
            # Use momentum CLI to get price data
            data = run_cli_tool(
                "src/utils/momentum_cli.py", [args.ticker, "--days", str(args.days)]
            )

        title = args.title or f"{args.ticker} - {args.days} Day Price History"
        buffer = create_line_chart(data, title, figsize=figsize, dpi=args.dpi)

    elif args.chart_type in ["bar", "barh"]:
        if args.data:
            data = json.loads(args.data)
        else:
            # Use risk metrics CLI
            data = run_cli_tool(
                "src/analysis/risk_metrics_cli.py", [args.ticker, "--days", "252"]
            )

        title = args.title or f"{args.ticker} - Risk Metrics"
        horizontal = args.chart_type == "barh"
        buffer = create_bar_chart(
            data, title, horizontal=horizontal, figsize=figsize, dpi=args.dpi
        )

    elif args.chart_type == "heatmap":
        tickers = args.tickers.split(",") if args.tickers else [args.ticker]

        # Use correlation CLI
        data = run_cli_tool(
            "src/analysis/correlation_cli.py", tickers + ["--days", "252"]
        )

        title = args.title or "Correlation Matrix"
        buffer = create_heatmap(
            data.get("matrix", []),
            data.get("tickers", tickers),
            title=title,
            figsize=figsize,
            dpi=args.dpi,
        )

    elif args.chart_type == "technical":
        if args.data:
            data = json.loads(args.data)
        else:
            data = run_cli_tool(
                "src/utils/momentum_cli.py", [args.ticker, "--days", str(args.days)]
            )

        title = args.title or f"{args.ticker} - Technical Analysis"
        buffer = create_technical_chart(
            price_data=data.get("prices", []),
            indicator_data=data.get("rsi", []),
            dates=data.get("dates", []),
            thresholds=[30, 70],
            title=title,
            figsize=figsize,
            dpi=args.dpi,
        )

    else:
        print(f"Unknown chart type: {args.chart_type}")
        sys.exit(1)

    # Save chart
    save_chart(buffer, args.output)


if __name__ == "__main__":
    main()
