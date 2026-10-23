"""Backtesting Framework for Finance Guru.

WHAT: Historical strategy validation with realistic cost modeling
WHY: Test investment strategies before risking real capital
ARCHITECTURE: Layer 2 of 3-layer type-safe architecture

FEATURES:
- Strategy execution simulation
- Transaction cost modeling (commissions + slippage)
- Performance metrics calculation
- Trade log generation
- Equity curve tracking
- Drawdown analysis

Used by: Strategy Advisor (hypothesis testing), Quant Analyst (model validation)
"""

from typing import Literal

import numpy as np
import pandas as pd

from src.models.backtest_inputs import (
    BacktestConfig,
    BacktestPerformanceMetrics,
    BacktestResults,
    TradeExecution,
    TradeSignal,
)
from src.utils.trading_calendar import TRADING_DAYS_PER_YEAR

OpenPositionOutcome = Literal["opened", "skipped_insufficient_capital"]


class Backtester:
    """WHAT: Executes and analyzes trading strategies on historical data
    WHY: Validates strategy performance before real capital deployment
    HOW: Uses Pydantic models for inputs/outputs, simulates realistic trading.

    EDUCATIONAL NOTE:
    A backtest answers: "If I had traded this strategy in the past, what would have happened?"

    CRITICAL REALISM FACTORS:
    1. **Look-ahead bias**: Can't use future data for past decisions
    2. **Survivor bias**: Don't just test stocks that succeeded
    3. **Transaction costs**: Include commissions and slippage
    4. **Market impact**: Your order affects the price (slippage models this)

    This backtester handles #3 and #4. YOU must handle #1 and #2 when creating signals!
    """

    def __init__(self, config: BacktestConfig):
        """Initialize backtester with configuration.

        Args:
            config: BacktestConfig with capital, costs, and sizing rules
        """
        self.config = config
        self.capital = config.initial_capital
        self.trades: list[TradeExecution] = []
        self.equity_curve: list[tuple[pd.Timestamp, float]] = []
        self.current_position: TradeExecution | None = None
        self.skipped_signals: list[TradeSignal] = []

    def run_backtest(
        self,
        signals: list[TradeSignal],
        ticker: str,
        strategy_name: str = "Unnamed Strategy",
    ) -> BacktestResults:
        """Execute backtest on a series of trading signals.

        EXPLANATION:
        This is the main entry point. It processes signals chronologically,
        executes trades with realistic costs, tracks performance, and generates
        a comprehensive results report.

        SIGNAL REQUIREMENTS:
        - Must be chronologically sorted (earliest first)
        - Must include prices (for execution simulation)
        - Should have BUY/SELL/HOLD actions

        Args:
            signals: TradeSignal objects in any order. They run by signal_date.
            ticker: Asset ticker being traded
            strategy_name: Descriptive name for the strategy

        Returns:
            BacktestResults with complete performance analysis
        """
        if not signals:
            raise ValueError("No signals provided for backtest")

        signals = sorted(signals, key=lambda x: x.signal_date)

        self.capital = self.config.initial_capital
        self.trades = []
        self.equity_curve = [(pd.Timestamp(signals[0].signal_date), self.capital)]
        self.current_position = None
        self.skipped_signals = []

        for signal in signals:
            self._process_signal(signal)

            current_equity = self._calculate_current_equity(signal.price)
            self.equity_curve.append((pd.Timestamp(signal.signal_date), current_equity))

        if self.current_position is not None:
            last_signal = signals[-1]
            self._close_position(
                last_signal.signal_date, last_signal.price, "Backtest end"
            )
            self.equity_curve[-1] = (
                pd.Timestamp(last_signal.signal_date),
                self.capital,
            )

        performance = self._calculate_performance_metrics()

        recommendation, reasoning = self._generate_recommendation(performance)

        equity_dates = [ts.date() for ts, _ in self.equity_curve]
        equity_values = [val for _, val in self.equity_curve]

        return BacktestResults(
            ticker=ticker,
            start_date=signals[0].signal_date,
            end_date=signals[-1].signal_date,
            strategy_name=strategy_name,
            config=self.config,
            performance=performance,
            trades=self.trades,
            equity_dates=equity_dates,
            equity_values=equity_values,
            recommendation=recommendation,
            reasoning=reasoning,
        )

    def _process_signal(self, signal: TradeSignal) -> None:
        """Process a single trading signal.

        LOGIC:
        - BUY: Open new position (if no current position)
        - SELL: Close current position (if holding)
        - HOLD: Do nothing

        Args:
            signal: TradeSignal to process
        """
        if signal.action == "BUY" and self.current_position is None:
            if self._open_position(signal) == "skipped_insufficient_capital":
                self.skipped_signals.append(signal)
        elif signal.action == "SELL" and self.current_position is not None:
            self._close_position(
                signal.signal_date, signal.price, signal.reason or "Sell signal"
            )

    def _open_position(self, signal: TradeSignal) -> OpenPositionOutcome:
        """Open a new trading position with realistic execution costs.

        EXECUTION MODEL:
        1. Calculate position size based on config
        2. Apply slippage to entry price (price moves against you)
        3. Deduct commission from capital
        4. Create TradeExecution record

        EDUCATIONAL NOTE:
        Slippage happens because:
        - Your order is large relative to available liquidity
        - Market moves while your order is being filled
        - You're using market orders (take whatever price is available)

        We model slippage as: actual_price = signal_price × (1 + slippage_pct)
        This means you always buy slightly higher than the signal price.

        Args:
            signal: BUY signal

        Returns:
            "opened", or "skipped_insufficient_capital" when the position plus
            commission costs more than the cash on hand, or the allocation cannot
            buy one whole share.
        """
        position_capital = self.capital * self.config.position_size_pct

        entry_price = signal.price * (1 + self.config.slippage_pct)

        shares = position_capital / entry_price

        if not self.config.allow_fractional_shares:
            shares = int(shares)
            if shares == 0:
                return "skipped_insufficient_capital"

        capital_needed = shares * entry_price

        commission = self.config.commission_per_trade

        if capital_needed + commission > self.capital:
            return "skipped_insufficient_capital"

        self.capital -= capital_needed + commission

        self.current_position = TradeExecution(
            entry_date=signal.signal_date,
            exit_date=None,
            ticker=signal.ticker,
            entry_price=entry_price,
            shares=shares,
            entry_commission=commission,
            exit_price=None,
            exit_commission=None,
            pnl=None,
            pnl_pct=None,
            signal_reason=signal.reason,
        )
        return "opened"

    def _close_position(self, exit_date, exit_price: float, reason: str) -> None:
        """Close the current position with realistic execution costs.

        EXECUTION MODEL:
        1. Apply slippage to exit price (price moves against you)
        2. Calculate proceeds from sale
        3. Deduct commission
        4. Add net proceeds to capital
        5. Calculate P&L
        6. Complete TradeExecution record

        EDUCATIONAL NOTE:
        When selling, slippage means you get a WORSE price than expected:
        actual_price = signal_price × (1 - slippage_pct)

        This is realistic - market makers/algorithms exploit your urgency!

        Args:
            exit_date: Date of exit
            exit_price: Exit price (signal price)
            reason: Reason for exit
        """
        if self.current_position is None:
            return

        actual_exit_price = exit_price * (1 - self.config.slippage_pct)

        proceeds = self.current_position.shares * actual_exit_price

        commission = self.config.commission_per_trade
        net_proceeds = proceeds - commission

        self.capital += net_proceeds

        entry_cost = self.current_position.shares * self.current_position.entry_price
        entry_cost_with_commission = entry_cost + self.current_position.entry_commission

        pnl = net_proceeds - entry_cost_with_commission
        pnl_pct = (pnl / entry_cost_with_commission) * 100

        self.current_position.exit_date = exit_date
        self.current_position.exit_price = actual_exit_price
        self.current_position.exit_commission = commission
        self.current_position.pnl = pnl
        self.current_position.pnl_pct = pnl_pct

        self.trades.append(self.current_position)

        self.current_position = None

    def _calculate_current_equity(self, current_price: float) -> float:
        """Calculate total account equity (cash + position value).

        Args:
            current_price: Current market price

        Returns:
            Total equity value
        """
        equity = self.capital

        if self.current_position is not None:
            position_value = self.current_position.shares * current_price
            equity += position_value

        return equity

    def _calculate_performance_metrics(self) -> BacktestPerformanceMetrics:
        """Calculate comprehensive performance statistics.

        METRICS CALCULATED:
        - Returns (total, percentage)
        - Risk metrics (Sharpe ratio, max drawdown)
        - Trade statistics (win rate, profit factor)
        - Cost analysis (commissions, slippage)

        Returns:
            BacktestPerformanceMetrics with all statistics
        """
        initial = self.config.initial_capital
        final = self.capital
        total_return = final - initial
        total_return_pct = (total_return / initial) * 100

        if len(self.equity_curve) > 1:
            equity_values = [val for _, val in self.equity_curve]
            returns = pd.Series(equity_values).pct_change().dropna()

            if len(returns) > 0 and returns.std() > 0:
                sharpe = float(
                    returns.mean() / returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
                )
            else:
                sharpe = None
        else:
            sharpe = None

        equity_values = [val for _, val in self.equity_curve]
        max_dd, max_dd_pct = self._calculate_max_drawdown(equity_values)

        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl and t.pnl > 0])
        losing_trades = len([t for t in self.trades if t.pnl and t.pnl < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        wins = [t.pnl for t in self.trades if t.pnl and t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl and t.pnl < 0]

        avg_win = float(np.mean(wins)) if wins else None
        avg_loss = float(np.mean(losses)) if losses else None

        gross_profits = sum(wins) if wins else 0.0
        gross_losses = abs(sum(losses)) if losses else 0.0
        profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else None

        total_commissions = sum(
            t.entry_commission + (t.exit_commission or 0) for t in self.trades
        )

        total_slippage = 0.0
        slippage_pct = self.config.slippage_pct
        for t in self.trades:
            entry_signal_price = t.entry_price / (1 + slippage_pct)
            entry_slippage = t.shares * entry_signal_price * slippage_pct
            total_slippage += entry_slippage

            if t.exit_price is not None:
                exit_signal_price = t.exit_price / (1 - slippage_pct)
                exit_slippage = t.shares * exit_signal_price * slippage_pct
                total_slippage += exit_slippage

        return BacktestPerformanceMetrics(
            initial_capital=initial,
            final_capital=final,
            total_return=total_return,
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            total_commissions=total_commissions,
            total_slippage=total_slippage,
        )

    def _calculate_max_drawdown(
        self, equity_values: list[float]
    ) -> tuple[float, float]:
        """Calculate maximum drawdown (worst peak-to-trough decline).

        FORMULA:
        Drawdown = (Trough - Peak) / Peak

        EDUCATIONAL NOTE:
        Max drawdown answers: "What's the worst losing streak I experienced?"

        This is CRITICAL because:
        - It's the psychological pain test (can you handle 30% drawdown?)
        - It determines position sizing (deeper drawdowns = smaller positions)
        - It's often the actual risk (not theoretical volatility)

        GUIDELINE:
        - Max DD < 10%: Very conservative strategy
        - Max DD 10-20%: Moderate risk
        - Max DD 20-30%: Aggressive (most people bail out here)
        - Max DD > 30%: Extremely aggressive (hard to recover psychologically)

        Args:
            equity_values: List of portfolio values over time

        Returns:
            Independent maximum drawdowns in dollars and percent.
        """
        if not equity_values:
            return 0.0, 0.0

        peak = equity_values[0]
        max_dd = 0.0
        max_dd_pct = 0.0

        for value in equity_values:
            if value > peak:
                peak = value

            drawdown = peak - value
            drawdown_pct = (drawdown / peak) * 100

            max_dd = max(max_dd, drawdown)
            max_dd_pct = max(max_dd_pct, drawdown_pct)

        return max_dd, max_dd_pct

    def _generate_recommendation(
        self,
        performance: BacktestPerformanceMetrics,
    ) -> tuple[Literal["DEPLOY", "OPTIMIZE", "REJECT"], str]:
        """Generate deployment recommendation based on performance.

        DECISION CRITERIA:
        - DEPLOY: Strong performance, acceptable risk
        - OPTIMIZE: Promising but needs improvement
        - REJECT: Poor performance or excessive risk

        THRESHOLDS (can be customized):
        - Total return > 10% AND
        - Sharpe ratio > 1.0 AND
        - Max drawdown < 25% AND
        - Win rate > 40%
        → DEPLOY

        Args:
            performance: BacktestPerformanceMetrics

        Returns:
            Tuple of (recommendation, reasoning)
        """
        reasons = []

        good_return = performance.total_return_pct > 10.0
        if good_return:
            reasons.append(f"Strong return ({performance.total_return_pct:.1f}%)")
        else:
            reasons.append(f"Low return ({performance.total_return_pct:.1f}%)")

        good_sharpe = (
            performance.sharpe_ratio is not None and performance.sharpe_ratio > 1.0
        )
        if good_sharpe:
            reasons.append(f"Good Sharpe ratio ({performance.sharpe_ratio:.2f})")
        else:
            if performance.sharpe_ratio is not None:
                reasons.append(f"Weak Sharpe ratio ({performance.sharpe_ratio:.2f})")
            else:
                reasons.append("Sharpe ratio unavailable")

        acceptable_dd = performance.max_drawdown_pct < 25.0
        if acceptable_dd:
            reasons.append(
                f"Acceptable max drawdown ({performance.max_drawdown_pct:.1f}%)"
            )
        else:
            reasons.append(
                f"Excessive max drawdown ({performance.max_drawdown_pct:.1f}%)"
            )

        decent_win_rate = performance.win_rate > 0.4
        if decent_win_rate:
            reasons.append(f"Decent win rate ({performance.win_rate * 100:.1f}%)")
        else:
            reasons.append(f"Low win rate ({performance.win_rate * 100:.1f}%)")

        if good_return and good_sharpe and acceptable_dd and decent_win_rate:
            recommendation: Literal["DEPLOY", "OPTIMIZE", "REJECT"] = "DEPLOY"
        elif (good_return or good_sharpe) and acceptable_dd:
            recommendation = "OPTIMIZE"
        else:
            recommendation = "REJECT"

        reasoning = ", ".join(reasons)

        return recommendation, reasoning
