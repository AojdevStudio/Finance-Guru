#!/usr/bin/env python3
"""
CLI interface for strategy backtesting.

WHAT: Command-line tool for Finance Guru agents to backtest trading strategies
WHY: Validate strategies before deploying real capital
ARCHITECTURE: Layer 3 of 3-layer type-safe architecture

USAGE:
    # Backtest a simple RSI strategy
    uv run python src/strategies/backtester_cli.py TSLA \\
        --days 252 \\
        --strategy rsi \\
        --capital 100000

    # Custom backtest with transaction costs
    uv run python src/strategies/backtester_cli.py TSLA \\
        --days 252 \\
        --strategy rsi \\
        --capital 100000 \\
        --commission 5.0 \\
        --slippage 0.001

    # JSON output for programmatic analysis
    uv run python src/strategies/backtester_cli.py TSLA \\
        --days 252 \\
        --strategy rsi \\
        --output json

BUILT-IN STRATEGIES:
    - rsi: RSI mean reversion (buy when RSI < 30, sell when RSI > 70)
    - sma_cross: Simple moving average crossover
    - buy_hold: Buy and hold benchmark

AGENT USE CASES:
- Strategy Advisor: Test investment hypotheses before deployment
- Quant Analyst: Validate quantitative models, optimize parameters
- Compliance Officer: Assess strategy risk profile
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import yfinance as yf

from src.models.backtest_inputs import (
    BacktestConfig,
    TradeSignal,
)
from src.strategies.backtester import Backtester


def fetch_price_data(ticker: str, days: int) -> pd.DataFrame:
    """
    Fetch historical OHLC data for backtesting.

    Args:
        ticker: Stock symbol
        days: Number of days of historical data

    Returns:
        DataFrame with OHLC data

    Raises:
        ValueError: If data cannot be fetched
    """
    # Need ~1.5x calendar days to get requested trading days (accounts for weekends/holidays)
    start_date = datetime.now() - timedelta(days=int(days * 1.5))
    end_date = datetime.now()

    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)

    if hist.empty:
        raise ValueError(f"No data found for ticker {ticker}")

    # Take only requested number of days
    hist = hist.tail(days)

    if len(hist) < 30:
        raise ValueError(
            f"Insufficient data for {ticker}. Need at least 30 days, got {len(hist)}"
        )

    return hist


def generate_rsi_signals(
    df: pd.DataFrame, ticker: str, period: int = 14
) -> list[TradeSignal]:
    """
    Generate RSI mean reversion trading signals.

    STRATEGY LOGIC:
    - BUY when RSI < 30 (oversold)
    - SELL when RSI > 70 (overbought)
    - HOLD otherwise

    EDUCATIONAL NOTE:
    This is a classic mean reversion strategy. The idea:
    - When RSI is very low, price has fallen "too much" → bounce expected
    - When RSI is very high, price has risen "too much" → pullback expected

    This works in RANGE-BOUND markets but fails in TRENDING markets!

    Args:
        df: DataFrame with OHLC data
        ticker: Asset ticker
        period: RSI calculation period (default: 14)

    Returns:
        List of TradeSignal objects
    """
    # Calculate RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Generate signals
    signals = []
    in_position = False

    for i in range(len(df)):
        date = df.index[i].date()
        price = float(df["Close"].iloc[i])
        current_rsi = rsi.iloc[i]

        if pd.isna(current_rsi):
            # Not enough data yet
            continue

        if current_rsi < 30 and not in_position:
            # Oversold - BUY signal
            signals.append(
                TradeSignal(
                    signal_date=date,
                    ticker=ticker,
                    action="BUY",
                    price=price,
                    signal_strength=0.85,
                    reason=f"RSI oversold at {current_rsi:.1f}",
                )
            )
            in_position = True

        elif current_rsi > 70 and in_position:
            # Overbought - SELL signal
            signals.append(
                TradeSignal(
                    signal_date=date,
                    ticker=ticker,
                    action="SELL",
                    price=price,
                    signal_strength=0.85,
                    reason=f"RSI overbought at {current_rsi:.1f}",
                )
            )
            in_position = False

        else:
            # HOLD
            signals.append(
                TradeSignal(
                    signal_date=date,
                    ticker=ticker,
                    action="HOLD",
                    price=price,
                )
            )

    return signals


def generate_sma_crossover_signals(
    df: pd.DataFrame,
    ticker: str,
    fast_period: int = 50,
    slow_period: int = 200,
) -> list[TradeSignal]:
    """
    Generate simple moving average crossover signals.

    STRATEGY LOGIC:
    - BUY when fast SMA crosses ABOVE slow SMA (golden cross)
    - SELL when fast SMA crosses BELOW slow SMA (death cross)

    EDUCATIONAL NOTE:
    This is a classic trend-following strategy. The idea:
    - Golden cross = new uptrend beginning
    - Death cross = new downtrend beginning

    This works in TRENDING markets but gives false signals in RANGE-BOUND markets!
    (Opposite of RSI strategy)

    Args:
        df: DataFrame with OHLC data
        ticker: Asset ticker
        fast_period: Fast SMA period (default: 50)
        slow_period: Slow SMA period (default: 200)

    Returns:
        List of TradeSignal objects
    """
    # Calculate SMAs
    fast_sma = df["Close"].rolling(window=fast_period).mean()
    slow_sma = df["Close"].rolling(window=slow_period).mean()

    # Generate signals
    signals = []
    in_position = False
    prev_fast = None
    prev_slow = None

    for i in range(len(df)):
        date = df.index[i].date()
        price = float(df["Close"].iloc[i])
        current_fast = fast_sma.iloc[i]
        current_slow = slow_sma.iloc[i]

        if pd.isna(current_fast) or pd.isna(current_slow):
            # Not enough data yet
            continue

        # Check for crossover
        if prev_fast is not None and prev_slow is not None:
            # Golden cross (fast crosses above slow)
            if (
                prev_fast <= prev_slow
                and current_fast > current_slow
                and not in_position
            ):
                signals.append(
                    TradeSignal(
                        signal_date=date,
                        ticker=ticker,
                        action="BUY",
                        price=price,
                        signal_strength=0.80,
                        reason=f"Golden cross (SMA{fast_period} above SMA{slow_period})",
                    )
                )
                in_position = True

            # Death cross (fast crosses below slow)
            elif prev_fast >= prev_slow and current_fast < current_slow and in_position:
                signals.append(
                    TradeSignal(
                        signal_date=date,
                        ticker=ticker,
                        action="SELL",
                        price=price,
                        signal_strength=0.80,
                        reason=f"Death cross (SMA{fast_period} below SMA{slow_period})",
                    )
                )
                in_position = False
            else:
                # HOLD
                signals.append(
                    TradeSignal(
                        signal_date=date,
                        ticker=ticker,
                        action="HOLD",
                        price=price,
                    )
                )
        else:
            # First data point - HOLD
            signals.append(
                TradeSignal(
                    signal_date=date,
                    ticker=ticker,
                    action="HOLD",
                    price=price,
                )
            )

        prev_fast = current_fast
        prev_slow = current_slow

    return signals


def generate_buy_hold_signals(df: pd.DataFrame, ticker: str) -> list[TradeSignal]:
    """
    Generate buy-and-hold benchmark signals.

    STRATEGY LOGIC:
    - BUY on first day
    - HOLD forever

    EDUCATIONAL NOTE:
    This is the BENCHMARK. Most active strategies fail to beat buy-and-hold
    after accounting for taxes and fees!

    Use this to compare your strategy against doing nothing.

    Args:
        df: DataFrame with OHLC data
        ticker: Asset ticker

    Returns:
        List of TradeSignal objects
    """
    signals = []

    for i in range(len(df)):
        date = df.index[i].date()
        price = float(df["Close"].iloc[i])

        if i == 0:
            # Buy on first day
            signals.append(
                TradeSignal(
                    signal_date=date,
                    ticker=ticker,
                    action="BUY",
                    price=price,
                    signal_strength=1.0,
                    reason="Buy and hold benchmark",
                )
            )
        else:
            # Hold forever
            signals.append(
                TradeSignal(
                    signal_date=date,
                    ticker=ticker,
                    action="HOLD",
                    price=price,
                )
            )

    return signals


def format_human_output(result) -> str:
    """
    Format backtest results for human-readable display.

    Args:
        result: BacktestResults

    Returns:
        Formatted string output
    """
    lines = []
    lines.append(f"\n{'=' * 70}")
    lines.append(f"BACKTEST RESULTS: {result.ticker}")
    lines.append(f"Strategy: {result.strategy_name}")
    lines.append(f"Period: {result.start_date} to {result.end_date}")
    lines.append(f"{'=' * 70}\n")

    # Recommendation (most important)
    recommendation_emoji = {"DEPLOY": "🟢", "OPTIMIZE": "🟡", "REJECT": "🔴"}
    emoji = recommendation_emoji.get(result.recommendation, "⚪")

    lines.append(f"RECOMMENDATION: {emoji} {result.recommendation}")
    lines.append(f"Reasoning: {result.reasoning}")
    lines.append("")

    # Performance Summary
    perf = result.performance
    lines.append("PERFORMANCE SUMMARY")
    lines.append("-" * 70)
    lines.append(f"Initial Capital: ${perf.initial_capital:,.2f}")
    lines.append(f"Final Capital: ${perf.final_capital:,.2f}")
    lines.append(
        f"Total Return: ${perf.total_return:,.2f} ({perf.total_return_pct:+.2f}%)"
    )

    if perf.sharpe_ratio is not None:
        lines.append(f"Sharpe Ratio: {perf.sharpe_ratio:.3f}")
    else:
        lines.append("Sharpe Ratio: N/A")

    lines.append(
        f"Max Drawdown: ${perf.max_drawdown:,.2f} ({perf.max_drawdown_pct:.2f}%)"
    )
    lines.append("")

    # Trade Statistics
    lines.append("TRADE STATISTICS")
    lines.append("-" * 70)
    lines.append(f"Total Trades: {perf.total_trades}")
    lines.append(f"Winning Trades: {perf.winning_trades}")
    lines.append(f"Losing Trades: {perf.losing_trades}")
    lines.append(f"Win Rate: {perf.win_rate * 100:.1f}%")

    if perf.avg_win is not None:
        lines.append(f"Average Win: ${perf.avg_win:,.2f}")
    if perf.avg_loss is not None:
        lines.append(f"Average Loss: ${perf.avg_loss:,.2f}")
    if perf.profit_factor is not None:
        lines.append(f"Profit Factor: {perf.profit_factor:.2f}")

    lines.append("")

    # Cost Analysis
    lines.append("COST ANALYSIS")
    lines.append("-" * 70)
    lines.append(f"Total Commissions: ${perf.total_commissions:,.2f}")
    lines.append(f"Total Slippage: ${perf.total_slippage:,.2f}")
    lines.append(
        f"Total Transaction Costs: ${perf.total_commissions + perf.total_slippage:,.2f}"
    )
    lines.append("")

    # Recent Trades (last 5)
    if result.trades:
        lines.append("RECENT TRADES (Last 5)")
        lines.append("-" * 70)

        for trade in result.trades[-5:]:
            entry_str = f"{trade.entry_date} @ ${trade.entry_price:.2f}"
            if trade.exit_date:
                exit_str = f"{trade.exit_date} @ ${trade.exit_price:.2f}"
                pnl_str = f"P&L: ${trade.pnl:+,.2f} ({trade.pnl_pct:+.2f}%)"

                pnl_emoji = "✅" if trade.pnl > 0 else "❌"
                lines.append(
                    f"{pnl_emoji} {trade.ticker}: {entry_str} → {exit_str} | {pnl_str}"
                )

                if trade.signal_reason:
                    lines.append(f"   Reason: {trade.signal_reason}")
            else:
                lines.append(f"🔵 {trade.ticker}: {entry_str} → OPEN")

        lines.append("")

    # Equity Curve Summary
    lines.append("EQUITY CURVE")
    lines.append("-" * 70)
    lines.append(f"Starting Value: ${result.equity_values[0]:,.2f}")
    lines.append(f"Peak Value: ${max(result.equity_values):,.2f}")
    lines.append(f"Final Value: ${result.equity_values[-1]:,.2f}")
    lines.append("")

    lines.append(f"{'=' * 70}\n")

    return "\n".join(lines)


def format_json_output(result) -> str:
    """
    Format backtest results as JSON.

    Args:
        result: BacktestResults

    Returns:
        JSON string
    """
    return json.dumps(result.model_dump(), indent=2, default=str)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Backtest trading strategies for Finance Guru agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test RSI strategy
  uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy rsi

  # Test with custom capital and costs
  uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy rsi \\
      --capital 500000 --commission 5.0 --slippage 0.001

  # Test SMA crossover strategy
  uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy sma_cross

  # Buy-and-hold benchmark
  uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy buy_hold

  # JSON output for analysis
  uv run python src/strategies/backtester_cli.py TSLA --days 252 --strategy rsi --output json

Agent Use Cases:
  - Strategy Advisor: Validate investment hypotheses
  - Quant Analyst: Test quantitative models
  - Compliance Officer: Assess strategy risk
        """,
    )

    # Required arguments
    parser.add_argument(
        "ticker", type=str, help="Stock ticker symbol (e.g., TSLA, AAPL, SPY)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=252,
        help="Number of days to backtest (default: 252, one year)",
    )

    parser.add_argument(
        "--strategy",
        choices=["rsi", "sma_cross", "buy_hold"],
        default="rsi",
        help="Strategy to backtest (default: rsi)",
    )

    # Backtest configuration
    parser.add_argument(
        "--capital",
        type=float,
        default=100000.0,
        help="Initial capital (default: 100000)",
    )

    parser.add_argument(
        "--commission",
        type=float,
        default=0.0,
        help="Commission per trade (default: 0.0 for commission-free brokers)",
    )

    parser.add_argument(
        "--slippage",
        type=float,
        default=0.001,
        help="Slippage percentage (default: 0.001 = 0.1%%)",
    )

    parser.add_argument(
        "--position-size",
        type=float,
        default=1.0,
        help="Position size as fraction of capital (default: 1.0 = 100%%)",
    )

    # Output format
    parser.add_argument(
        "--output",
        choices=["human", "json"],
        default="human",
        help="Output format (default: human)",
    )

    args = parser.parse_args()

    try:
        # Fetch price data
        print(
            f"Fetching {args.days} days of data for {args.ticker}...", file=sys.stderr
        )
        df = fetch_price_data(args.ticker, args.days)

        # Generate signals based on strategy
        print(f"Generating {args.strategy} signals...", file=sys.stderr)

        if args.strategy == "rsi":
            signals = generate_rsi_signals(df, args.ticker)
            strategy_name = "RSI Mean Reversion (Buy<30, Sell>70)"
        elif args.strategy == "sma_cross":
            signals = generate_sma_crossover_signals(df, args.ticker)
            strategy_name = "SMA Crossover (50/200)"
        elif args.strategy == "buy_hold":
            signals = generate_buy_hold_signals(df, args.ticker)
            strategy_name = "Buy and Hold Benchmark"
        else:
            raise ValueError(f"Unknown strategy: {args.strategy}")

        # Create backtest config
        config = BacktestConfig(
            initial_capital=args.capital,
            commission_per_trade=args.commission,
            slippage_pct=args.slippage,
            position_size_pct=args.position_size,
            allow_fractional_shares=True,
        )

        # Run backtest
        print("Running backtest...", file=sys.stderr)
        backtester = Backtester(config)
        result = backtester.run_backtest(signals, args.ticker, strategy_name)

        # Output results
        if args.output == "json":
            print(format_json_output(result))
        else:
            print(format_human_output(result))

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
