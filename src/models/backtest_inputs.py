"""Pydantic models for backtesting framework.

WHAT: Data models for strategy backtesting and validation
WHY: Type-safe historical strategy testing for Finance Guru agents
ARCHITECTURE: Layer 1 of 3-layer type-safe architecture

Used by: Strategy Advisor, Quant Analyst, Compliance Officer workflows
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class BacktestConfig(BaseModel):
    """WHAT: Configuration for backtest execution
    WHY: Standardizes backtest parameters across all Finance Guru agents.

    EDUCATIONAL NOTE:
    These settings make backtests realistic by accounting for real-world costs:

    - **Initial Capital**: How much money you're starting with
    - **Commission**: Trading fees (e.g., $0 for Robinhood, $1-10 for traditional brokers)
    - **Slippage**: Price moves between decision and execution (usually 0.05-0.1%)
    - **Position Size**: How much to allocate per trade

    WITHOUT these costs, backtests look unrealistically good!
    """

    initial_capital: float = Field(
        default=100000.0, gt=0.0, description="Starting capital for backtest"
    )

    commission_per_trade: float = Field(
        default=0.0,
        ge=0.0,
        description="Commission per trade (e.g., 0.0 for commission-free brokers)",
    )

    slippage_pct: float = Field(
        default=0.001,
        ge=0.0,
        le=0.05,
        description="Slippage as percentage (0.001 = 0.1%)",
    )

    position_size_pct: float = Field(
        default=1.0,
        gt=0.0,
        le=1.0,
        description="Position size as % of capital (1.0 = 100%, all-in)",
    )

    allow_fractional_shares: bool = Field(
        default=True,
        description="Allow fractional share purchases (True for most modern brokers)",
    )


class TradeSignal(BaseModel):
    """WHAT: A single buy or sell signal from a strategy
    WHY: Defines when and what to trade during backtest.

    EDUCATIONAL NOTE:
    A trading strategy generates "signals" - instructions to buy or sell.
    Example signals:
    - "Buy TSLA when RSI < 30" (oversold)
    - "Sell TSLA when price crosses above upper Bollinger Band" (overbought)
    - "Buy SPY every Monday" (systematic DCA)

    This model captures those signals with validation.
    """

    signal_date: date = Field(..., description="Date of signal")
    ticker: str = Field(..., description="Asset ticker")
    action: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Trade action")
    price: float = Field(..., gt=0.0, description="Price at signal")
    signal_strength: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional signal strength (0-1, for position sizing)",
    )
    reason: str | None = Field(
        default=None, description="Optional reason for signal (for analysis)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "date": "2025-10-13",
                    "ticker": "TSLA",
                    "action": "BUY",
                    "price": 250.00,
                    "signal_strength": 0.85,
                    "reason": "RSI oversold below 30",
                }
            ]
        }
    }


class TradeExecution(BaseModel):
    """WHAT: A completed trade with actual execution details
    WHY: Records what actually happened (vs what was planned).

    EDUCATIONAL NOTE:
    The difference between SIGNAL and EXECUTION is critical:

    - Signal: "I want to buy TSLA at $250"
    - Execution: "I bought 10 shares at $250.50 with $5 commission"

    Slippage and fees mean execution differs from signal!
    This is why backtests WITHOUT these details are unrealistic.
    """

    entry_date: date = Field(..., description="Trade entry date")
    exit_date: date | None = Field(
        default=None, description="Trade exit date (None if still open)"
    )
    ticker: str = Field(..., description="Asset ticker")

    # Entry details
    entry_price: float = Field(
        ..., gt=0.0, description="Actual entry price (after slippage)"
    )
    shares: float = Field(..., gt=0.0, description="Number of shares traded")
    entry_commission: float = Field(..., ge=0.0, description="Commission paid on entry")

    # Exit details (if closed)
    exit_price: float | None = Field(
        default=None, description="Actual exit price (after slippage)"
    )
    exit_commission: float | None = Field(
        default=None, description="Commission paid on exit"
    )

    # Trade performance
    pnl: float | None = Field(default=None, description="Profit/Loss in dollars")
    pnl_pct: float | None = Field(default=None, description="Profit/Loss as percentage")

    # Metadata
    signal_reason: str | None = Field(
        default=None, description="Original signal reason"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entry_date": "2025-10-10",
                    "exit_date": "2025-10-13",
                    "ticker": "TSLA",
                    "entry_price": 250.50,
                    "shares": 10.0,
                    "entry_commission": 5.00,
                    "exit_price": 260.00,
                    "exit_commission": 5.00,
                    "pnl": 85.00,
                    "pnl_pct": 3.39,
                    "signal_reason": "RSI oversold",
                }
            ]
        }
    }


class BacktestPerformanceMetrics(BaseModel):
    """WHAT: Performance statistics for the backtest
    WHY: Comprehensive evaluation of strategy quality.

    EDUCATIONAL NOTE:
    These metrics answer key questions about your strategy:

    1. **Total Return**: How much did I make/lose?
    2. **Sharpe Ratio**: Was return worth the risk?
    3. **Max Drawdown**: Worst losing streak (can you stomach it?)
    4. **Win Rate**: What % of trades were profitable?
    5. **Profit Factor**: How much winners made vs losers lost

    A good strategy has:
    - Positive returns (obviously!)
    - Sharpe > 1.0 (good risk-adjusted returns)
    - Max drawdown < 25% (tolerable losses)
    - Win rate > 50% OR profit factor > 2.0 (winners outweigh losers)
    """

    # Capital metrics
    initial_capital: float = Field(..., description="Starting capital")
    final_capital: float = Field(..., description="Ending capital")
    total_return: float = Field(..., description="Total return in dollars")
    total_return_pct: float = Field(..., description="Total return as percentage")

    # Risk metrics
    sharpe_ratio: float | None = Field(
        default=None, description="Sharpe ratio (risk-adjusted return)"
    )
    max_drawdown: float = Field(..., description="Maximum peak-to-trough decline")
    max_drawdown_pct: float = Field(..., description="Max drawdown as percentage")

    # Trade statistics
    total_trades: int = Field(..., ge=0, description="Total number of trades executed")
    winning_trades: int = Field(..., ge=0, description="Number of profitable trades")
    losing_trades: int = Field(..., ge=0, description="Number of losing trades")
    win_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Win rate (winning trades / total trades)"
    )

    # Profit metrics
    avg_win: float | None = Field(
        default=None, description="Average profit on winning trades"
    )
    avg_loss: float | None = Field(
        default=None, description="Average loss on losing trades"
    )
    profit_factor: float | None = Field(
        default=None, description="Profit factor (gross profits / gross losses)"
    )

    # Cost analysis
    total_commissions: float = Field(..., ge=0.0, description="Total commissions paid")
    total_slippage: float = Field(..., ge=0.0, description="Total slippage cost")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "initial_capital": 100000.0,
                    "final_capital": 125000.0,
                    "total_return": 25000.0,
                    "total_return_pct": 25.0,
                    "sharpe_ratio": 1.45,
                    "max_drawdown": 8500.0,
                    "max_drawdown_pct": 8.5,
                    "total_trades": 50,
                    "winning_trades": 32,
                    "losing_trades": 18,
                    "win_rate": 0.64,
                    "avg_win": 1250.00,
                    "avg_loss": -450.00,
                    "profit_factor": 2.78,
                    "total_commissions": 250.00,
                    "total_slippage": 180.00,
                }
            ]
        }
    }


class BacktestResults(BaseModel):
    """WHAT: Complete backtest results with all trades and metrics
    WHY: Comprehensive strategy validation for Finance Guru agents.

    AGENT USE CASES:
    - Strategy Advisor: Validate investment hypotheses before deployment
    - Quant Analyst: Test quantitative models, optimize parameters
    - Compliance Officer: Assess strategy risk profile before approval
    """

    # Backtest metadata
    ticker: str = Field(..., description="Asset ticker tested")
    start_date: date = Field(..., description="Backtest start date")
    end_date: date = Field(..., description="Backtest end date")
    strategy_name: str = Field(..., description="Strategy name/description")

    # Configuration used
    config: BacktestConfig = Field(..., description="Backtest configuration")

    # Performance metrics
    performance: BacktestPerformanceMetrics = Field(
        ..., description="Performance statistics"
    )

    # Trade history
    trades: list[TradeExecution] = Field(..., description="All executed trades")

    # Equity curve data
    equity_dates: list[date] = Field(..., description="Dates for equity curve")
    equity_values: list[float] = Field(..., description="Portfolio values over time")

    # Verdict
    recommendation: Literal["DEPLOY", "OPTIMIZE", "REJECT"] = Field(
        ..., description="Backtest verdict based on performance"
    )
    reasoning: str = Field(..., description="Reasoning for recommendation")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticker": "TSLA",
                    "start_date": "2024-10-13",
                    "end_date": "2025-10-13",
                    "strategy_name": "RSI Mean Reversion",
                    "config": {},
                    "performance": {},
                    "trades": [],
                    "equity_dates": ["2024-10-13", "2025-10-13"],
                    "equity_values": [100000.0, 125000.0],
                    "recommendation": "DEPLOY",
                    "reasoning": "Strong Sharpe ratio (1.45), acceptable max drawdown (8.5%), high win rate (64%)",
                }
            ]
        }
    }
