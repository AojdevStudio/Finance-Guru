"""Tests for Backtester calculator.

Tests cover:
- Backtest execution with buy/sell signals
- Transaction cost modeling (slippage + commission)
- Performance metrics calculation (Sharpe, drawdown, win rate)
- Recommendation generation
- Edge cases (no trades, single trade, insufficient capital)

RUNNING TESTS:
    uv run pytest tests/python/test_backtester.py -v
"""

from datetime import date

import pytest

from src.models.backtest_inputs import BacktestConfig, TradeSignal
from src.strategies.backtester import Backtester


@pytest.fixture
def default_config():
    return BacktestConfig(
        initial_capital=100_000.0,
        commission_per_trade=0.0,
        slippage_pct=0.0,
        position_size_pct=1.0,
        allow_fractional_shares=True,
    )


@pytest.fixture
def config_with_costs():
    return BacktestConfig(
        initial_capital=100_000.0,
        commission_per_trade=10.0,
        slippage_pct=0.001,
        position_size_pct=0.5,
        allow_fractional_shares=True,
    )


def _make_signals(prices, actions, ticker="TSLA"):
    """Helper to build signals from price/action lists."""
    signals = []
    start = date(2025, 1, 1)
    for i, (price, action) in enumerate(zip(prices, actions, strict=True)):
        signals.append(
            TradeSignal(
                signal_date=date(start.year, start.month, start.day + i),
                ticker=ticker,
                action=action,
                price=price,
            )
        )
    return signals


class TestBacktesterInit:
    def test_initializes_with_config(self, default_config):
        bt = Backtester(default_config)
        assert bt.config == default_config
        assert bt.capital == 100_000.0

    def test_initializes_empty_trades(self, default_config):
        bt = Backtester(default_config)
        assert bt.trades == []
        assert bt.current_position is None


class TestBacktestExecution:
    def test_empty_signals_raises(self, default_config):
        bt = Backtester(default_config)
        with pytest.raises(ValueError, match="No signals"):
            bt.run_backtest([], "TSLA")

    def test_single_buy_and_sell(self, default_config):
        signals = _make_signals([100.0, 120.0], ["BUY", "SELL"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA", "Test Strategy")

        assert result.ticker == "TSLA"
        assert result.strategy_name == "Test Strategy"
        assert len(result.trades) == 1
        assert result.trades[0].pnl > 0

    def test_hold_signal_does_nothing(self, default_config):
        signals = _make_signals([100.0, 110.0, 120.0], ["HOLD", "HOLD", "HOLD"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert len(result.trades) == 0
        assert result.performance.total_trades == 0

    def test_open_position_closed_at_end(self, default_config):
        signals = _make_signals([100.0, 110.0, 120.0], ["BUY", "HOLD", "HOLD"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert len(result.trades) == 1
        assert result.trades[0].exit_date is not None

    def test_sell_without_position_ignored(self, default_config):
        signals = _make_signals([100.0, 110.0], ["SELL", "SELL"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert len(result.trades) == 0

    def test_buy_when_already_holding_ignored(self, default_config):
        signals = _make_signals([100.0, 110.0, 120.0], ["BUY", "BUY", "SELL"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert len(result.trades) == 1

    def test_multiple_round_trips(self):
        config = BacktestConfig(
            initial_capital=100_000.0,
            commission_per_trade=0.0,
            slippage_pct=0.0,
            position_size_pct=0.5,
            allow_fractional_shares=True,
        )
        prices = [100.0, 120.0, 110.0, 130.0]
        actions = ["BUY", "SELL", "BUY", "SELL"]
        signals = _make_signals(prices, actions)
        bt = Backtester(config)
        result = bt.run_backtest(signals, "TSLA")

        assert len(result.trades) == 2
        assert result.performance.total_trades == 2


class TestTransactionCosts:
    @pytest.mark.parametrize("last_action", ["HOLD", "SELL"])
    def test_final_equity_includes_sale_costs(self, last_action):
        config = BacktestConfig(
            initial_capital=20_000.0,
            position_size_pct=0.5,
            slippage_pct=0.01,
            commission_per_trade=10.0,
        )
        signals = _make_signals([100.0, 100.0], ["BUY", last_action])

        result = Backtester(config).run_backtest(signals, "TSLA")

        assert result.equity_values[-1] == pytest.approx(
            result.performance.final_capital
        )
        assert result.performance.max_drawdown == pytest.approx(
            -result.performance.total_return
        )

    @pytest.mark.parametrize(
        ("exit_price", "expected_slippage"),
        [(50.0, 750.0), (100.0, 1000.0), (200.0, 1500.0)],
    )
    def test_total_slippage_matches_execution_cost(self, exit_price, expected_slippage):
        config = BacktestConfig(
            initial_capital=21_000.0,
            position_size_pct=0.5,
            slippage_pct=0.05,
            commission_per_trade=0.0,
        )
        signals = _make_signals([100.0, exit_price], ["BUY", "SELL"])

        result = Backtester(config).run_backtest(signals, "TSLA")

        assert result.trades[0].shares == pytest.approx(100.0)
        assert result.performance.total_slippage == pytest.approx(expected_slippage)

    def test_slippage_increases_buy_price(self):
        config = BacktestConfig(
            initial_capital=100_000.0,
            slippage_pct=0.01,
            commission_per_trade=0.0,
        )
        signals = _make_signals([100.0, 100.0], ["BUY", "SELL"])
        bt = Backtester(config)
        result = bt.run_backtest(signals, "TSLA")

        trade = result.trades[0]
        assert trade.entry_price == pytest.approx(101.0, rel=1e-6)
        assert trade.exit_price == pytest.approx(99.0, rel=1e-6)

    def test_commission_deducted(self):
        config = BacktestConfig(
            initial_capital=100_000.0,
            commission_per_trade=50.0,
            slippage_pct=0.0,
            position_size_pct=0.5,
        )
        signals = _make_signals([100.0, 100.0], ["BUY", "SELL"])
        bt = Backtester(config)
        result = bt.run_backtest(signals, "TSLA")

        assert result.performance.total_commissions == 100.0

    def test_insufficient_capital_skips_trade(self):
        config = BacktestConfig(
            initial_capital=100.0,
            commission_per_trade=200.0,
            slippage_pct=0.0,
        )
        signals = _make_signals([100.0, 120.0], ["BUY", "SELL"])
        bt = Backtester(config)
        result = bt.run_backtest(signals, "TSLA")

        assert len(result.trades) == 0
        assert bt.skipped_signals == [signals[0]]

    def test_integer_shares_when_fractional_disabled(self):
        config = BacktestConfig(
            initial_capital=100_000.0,
            allow_fractional_shares=False,
            slippage_pct=0.0,
            commission_per_trade=0.0,
        )
        signals = _make_signals([33.0, 40.0], ["BUY", "SELL"])
        bt = Backtester(config)
        result = bt.run_backtest(signals, "TSLA")

        trade = result.trades[0]
        assert trade.shares == int(trade.shares)

    def test_position_sizing(self):
        config = BacktestConfig(
            initial_capital=100_000.0,
            position_size_pct=0.5,
            slippage_pct=0.0,
            commission_per_trade=0.0,
        )
        signals = _make_signals([100.0, 120.0], ["BUY", "SELL"])
        bt = Backtester(config)
        result = bt.run_backtest(signals, "TSLA")

        trade = result.trades[0]
        assert trade.shares == pytest.approx(500.0)


class TestPerformanceMetrics:
    def test_profitable_trade_metrics(self, default_config):
        signals = _make_signals([100.0, 150.0], ["BUY", "SELL"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        perf = result.performance
        assert perf.total_return > 0
        assert perf.total_return_pct == pytest.approx(50.0, rel=0.01)
        assert perf.winning_trades == 1
        assert perf.losing_trades == 0
        assert perf.win_rate == 1.0

    def test_losing_trade_metrics(self, default_config):
        signals = _make_signals([100.0, 50.0], ["BUY", "SELL"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        perf = result.performance
        assert perf.total_return < 0
        assert perf.winning_trades == 0
        assert perf.losing_trades == 1
        assert perf.win_rate == 0.0

    def test_profit_factor_calculated(self, default_config):
        prices = [100.0, 120.0, 100.0, 80.0]
        actions = ["BUY", "SELL", "BUY", "SELL"]
        signals = _make_signals(prices, actions)
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        perf = result.performance
        assert perf.profit_factor is not None
        assert perf.profit_factor > 0

    def test_no_trades_zero_metrics(self, default_config):
        signals = _make_signals([100.0, 110.0], ["HOLD", "HOLD"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        perf = result.performance
        assert perf.total_trades == 0
        assert perf.win_rate == 0.0
        assert perf.total_commissions == 0.0

    def test_equity_curve_has_correct_length(self, default_config):
        signals = _make_signals([100.0, 110.0, 120.0], ["BUY", "HOLD", "SELL"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert len(result.equity_dates) == 4
        assert len(result.equity_values) == 4

    def test_cost_analysis_with_slippage(self):
        config = BacktestConfig(
            initial_capital=100_000.0,
            slippage_pct=0.01,
            commission_per_trade=10.0,
            position_size_pct=0.5,
        )
        signals = _make_signals([100.0, 120.0], ["BUY", "SELL"])
        bt = Backtester(config)
        result = bt.run_backtest(signals, "TSLA")

        perf = result.performance
        assert perf.total_slippage > 0
        assert perf.total_commissions == 20.0


class TestMaxDrawdown:
    @pytest.mark.parametrize(
        ("trough_price", "expected_drawdown", "recommendation"),
        [(50.0, 50.0, "REJECT"), (75.0, 25.0, "REJECT"), (90.0, 10.0, "DEPLOY")],
    )
    def test_worst_percent_loss_survives_later_growth(
        self, default_config, trough_price, expected_drawdown, recommendation
    ):
        """A later larger dollar loss cannot erase an earlier percentage loss."""
        signals = _make_signals(
            [100.0, trough_price, 1000.0, 900.0], ["BUY", "HOLD", "HOLD", "SELL"]
        )

        result = Backtester(default_config).run_backtest(signals, "TSLA")

        assert result.performance.max_drawdown == pytest.approx(100_000.0)
        assert result.performance.max_drawdown_pct == pytest.approx(expected_drawdown)
        assert result.recommendation == recommendation

    def test_no_drawdown_when_always_up(self, default_config):
        bt = Backtester(default_config)
        dd, dd_pct = bt._calculate_max_drawdown([100, 110, 120, 130])
        assert dd == 0.0
        assert dd_pct == 0.0

    def test_drawdown_calculated_correctly(self, default_config):
        bt = Backtester(default_config)
        dd, dd_pct = bt._calculate_max_drawdown([100, 120, 90, 110])
        assert dd == pytest.approx(30.0)
        assert dd_pct == pytest.approx(25.0)

    def test_empty_equity_values(self, default_config):
        bt = Backtester(default_config)
        dd, dd_pct = bt._calculate_max_drawdown([])
        assert dd == 0.0


class TestRecommendations:
    def test_deploy_recommendation(self, default_config):
        """Strong performance should recommend DEPLOY."""
        prices = [100.0, 120.0, 100.0, 125.0, 100.0, 130.0, 100.0, 135.0, 100.0, 140.0]
        actions = [
            "BUY",
            "SELL",
            "BUY",
            "SELL",
            "BUY",
            "SELL",
            "BUY",
            "SELL",
            "BUY",
            "SELL",
        ]
        signals = _make_signals(prices, actions)
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert result.recommendation in ("DEPLOY", "OPTIMIZE")

    def test_reject_recommendation_for_poor_performance(self, default_config):
        """Poor performance should recommend REJECT."""
        prices = [100.0, 50.0, 100.0, 50.0]
        actions = ["BUY", "SELL", "BUY", "SELL"]
        signals = _make_signals(prices, actions)
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert result.recommendation == "REJECT"

    def test_recommendation_with_none_sharpe(self, default_config):
        """Should handle None Sharpe ratio gracefully."""
        signals = _make_signals([100.0, 100.0], ["BUY", "SELL"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert result.recommendation in ("DEPLOY", "OPTIMIZE", "REJECT")
        assert (
            "Sharpe ratio unavailable" in result.reasoning
            or "Sharpe" in result.reasoning
        )


class TestBacktestResults:
    def test_results_contain_dates(self, default_config):
        signals = _make_signals([100.0, 120.0], ["BUY", "SELL"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert result.start_date == date(2025, 1, 1)
        assert result.end_date == date(2025, 1, 2)

    def test_results_contain_config(self, default_config):
        signals = _make_signals([100.0, 120.0], ["BUY", "SELL"])
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert result.config == default_config

    def test_signals_sorted_by_date(self, default_config):
        """Signals should be sorted defensively even if out of order."""
        signals = [
            TradeSignal(
                signal_date=date(2025, 1, 3), ticker="TSLA", action="SELL", price=120.0
            ),
            TradeSignal(
                signal_date=date(2025, 1, 1), ticker="TSLA", action="BUY", price=100.0
            ),
            TradeSignal(
                signal_date=date(2025, 1, 2), ticker="TSLA", action="HOLD", price=110.0
            ),
        ]
        bt = Backtester(default_config)
        result = bt.run_backtest(signals, "TSLA")

        assert result.start_date == date(2025, 1, 1)
        assert len(result.trades) == 1
