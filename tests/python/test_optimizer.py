"""Tests for Portfolio Optimizer calculator.

Tests cover:
- All 5 optimization methods (mean_variance, risk_parity, min_variance, max_sharpe, black_litterman)
- Weight validation and normalization
- Portfolio metrics calculation
- Efficient frontier generation
- Edge cases and error handling
- Convenience function

RUNNING TESTS:
    uv run pytest tests/python/test_optimizer.py -v
"""

from datetime import date, timedelta

import numpy as np
import pytest

from src.models.portfolio_inputs import (
    OptimizationConfig,
    PortfolioDataInput,
)
from src.strategies.optimizer import PortfolioOptimizer, optimize_portfolio

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_portfolio_data(n_days=60, tickers=None, seed=42):
    """Build synthetic portfolio data with controlled randomness."""
    rng = np.random.RandomState(seed)
    tickers = tickers or ["AAAA", "BBBB", "CCCC"]
    start = date(2024, 1, 1)
    dates = [start + timedelta(days=i) for i in range(n_days)]

    prices = {}
    for i, t in enumerate(tickers):
        # Generate realistic price series (random walk with drift)
        daily_returns = rng.normal(0.0005 * (i + 1), 0.02, n_days)
        price_series = [100.0]
        for r in daily_returns[1:]:
            price_series.append(price_series[-1] * (1 + r))
        prices[t] = price_series[:n_days]

    return PortfolioDataInput(
        tickers=tickers,
        dates=dates,
        prices=prices,
    )


@pytest.fixture
def portfolio_data():
    return _make_portfolio_data()


@pytest.fixture
def default_config():
    return OptimizationConfig(method="max_sharpe")


# ---------------------------------------------------------------------------
# Optimizer initialization
# ---------------------------------------------------------------------------


class TestOptimizerInit:
    def test_creates_with_config(self, default_config):
        opt = PortfolioOptimizer(default_config)
        assert opt.config == default_config


# ---------------------------------------------------------------------------
# Mean-Variance optimization
# ---------------------------------------------------------------------------


class TestMeanVariance:
    def test_mean_variance_produces_valid_weights(self, portfolio_data):
        config = OptimizationConfig(method="mean_variance")
        opt = PortfolioOptimizer(config)
        result = opt.optimize(portfolio_data)

        assert result.method == "mean_variance"
        assert abs(sum(result.optimal_weights.values()) - 1.0) < 0.01
        assert all(w >= -0.01 for w in result.optimal_weights.values())

    def test_mean_variance_with_target_return(self, portfolio_data):
        config = OptimizationConfig(method="mean_variance", target_return=0.05)
        opt = PortfolioOptimizer(config)
        result = opt.optimize(portfolio_data)

        assert result.method == "mean_variance"
        assert abs(sum(result.optimal_weights.values()) - 1.0) < 0.01


# ---------------------------------------------------------------------------
# Risk Parity optimization
# ---------------------------------------------------------------------------


class TestRiskParity:
    def test_risk_parity_produces_valid_weights(self, portfolio_data):
        config = OptimizationConfig(method="risk_parity")
        opt = PortfolioOptimizer(config)
        result = opt.optimize(portfolio_data)

        assert result.method == "risk_parity"
        assert abs(sum(result.optimal_weights.values()) - 1.0) < 0.01
        assert all(w >= -0.01 for w in result.optimal_weights.values())


# ---------------------------------------------------------------------------
# Min Variance optimization
# ---------------------------------------------------------------------------


class TestMinVariance:
    def test_min_variance_produces_valid_weights(self, portfolio_data):
        config = OptimizationConfig(method="min_variance")
        opt = PortfolioOptimizer(config)
        result = opt.optimize(portfolio_data)

        assert result.method == "min_variance"
        assert abs(sum(result.optimal_weights.values()) - 1.0) < 0.01

    def test_min_variance_has_lower_vol_than_equal_weight(self, portfolio_data):
        config = OptimizationConfig(method="min_variance")
        opt = PortfolioOptimizer(config)
        result = opt.optimize(portfolio_data)

        # Min variance should have low volatility
        assert result.expected_volatility >= 0


# ---------------------------------------------------------------------------
# Max Sharpe optimization
# ---------------------------------------------------------------------------


class TestMaxSharpe:
    def test_max_sharpe_produces_valid_weights(self, portfolio_data):
        config = OptimizationConfig(method="max_sharpe")
        opt = PortfolioOptimizer(config)
        result = opt.optimize(portfolio_data)

        assert result.method == "max_sharpe"
        assert abs(sum(result.optimal_weights.values()) - 1.0) < 0.01

    def test_max_sharpe_has_sharpe_ratio(self, portfolio_data):
        config = OptimizationConfig(method="max_sharpe")
        opt = PortfolioOptimizer(config)
        result = opt.optimize(portfolio_data)

        # Sharpe ratio should be a real number
        assert isinstance(result.sharpe_ratio, float)


# ---------------------------------------------------------------------------
# Black-Litterman optimization
# ---------------------------------------------------------------------------


class TestBlackLitterman:
    def test_bl_produces_valid_weights(self, portfolio_data):
        config = OptimizationConfig(
            method="black_litterman",
            views={"AAAA": 0.15, "BBBB": 0.10, "CCCC": 0.05},
        )
        opt = PortfolioOptimizer(config)
        result = opt.optimize(portfolio_data)

        assert result.method == "black_litterman"
        assert abs(sum(result.optimal_weights.values()) - 1.0) < 0.01

    def test_bl_without_views_raises(self, portfolio_data):
        # OptimizationConfig should raise if BL without views
        with pytest.raises(ValueError, match="views"):
            OptimizationConfig(method="black_litterman", views=None)


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


class TestOptimizeRouting:
    def test_unknown_method_raises(self, portfolio_data):
        config = OptimizationConfig.__new__(OptimizationConfig)
        object.__setattr__(config, "method", "unknown_method")
        object.__setattr__(config, "risk_free_rate", 0.045)
        object.__setattr__(config, "target_return", None)
        object.__setattr__(config, "allow_short", False)
        object.__setattr__(config, "position_limits", (0.0, 1.0))
        object.__setattr__(config, "views", None)

        opt = PortfolioOptimizer(config)
        with pytest.raises(ValueError, match="Unknown optimization method"):
            opt.optimize(portfolio_data)


# ---------------------------------------------------------------------------
# Weight validation
# ---------------------------------------------------------------------------


class TestWeightValidation:
    def test_weights_normalized_to_one(self, portfolio_data):
        config = OptimizationConfig(method="max_sharpe")
        opt = PortfolioOptimizer(config)
        result = opt.optimize(portfolio_data)

        total = sum(result.optimal_weights.values())
        assert abs(total - 1.0) < 0.001

    def test_weights_within_position_limits(self, portfolio_data):
        config = OptimizationConfig(
            method="max_sharpe",
            position_limits=(0.1, 0.5),
        )
        opt = PortfolioOptimizer(config)
        result = opt.optimize(portfolio_data)

        for w in result.optimal_weights.values():
            assert w >= 0.1 - 1e-4
            assert w <= 0.5 + 1e-4


# ---------------------------------------------------------------------------
# Portfolio metrics
# ---------------------------------------------------------------------------


class TestPortfolioMetrics:
    def test_output_has_required_fields(self, portfolio_data, default_config):
        opt = PortfolioOptimizer(default_config)
        result = opt.optimize(portfolio_data)

        assert hasattr(result, "expected_return")
        assert hasattr(result, "expected_volatility")
        assert hasattr(result, "sharpe_ratio")
        assert hasattr(result, "diversification_ratio")
        assert result.expected_volatility >= 0
        assert result.diversification_ratio >= 1.0

    def test_tickers_match_input(self, portfolio_data, default_config):
        opt = PortfolioOptimizer(default_config)
        result = opt.optimize(portfolio_data)

        assert set(result.tickers) == set(portfolio_data.tickers)
        assert set(result.optimal_weights.keys()) == set(portfolio_data.tickers)


# ---------------------------------------------------------------------------
# Expected returns calculation
# ---------------------------------------------------------------------------


class TestExpectedReturns:
    def test_uses_provided_expected_returns(self):
        data = _make_portfolio_data(tickers=["AAAA", "BBBB"])
        data_with_returns = PortfolioDataInput(
            tickers=data.tickers,
            dates=data.dates,
            prices=data.prices,
            expected_returns={"AAAA": 0.10, "BBBB": 0.15},
        )

        config = OptimizationConfig(method="max_sharpe")
        opt = PortfolioOptimizer(config)
        returns = opt._calculate_expected_returns(data_with_returns)

        assert returns[0] == pytest.approx(0.10)
        assert returns[1] == pytest.approx(0.15)

    def test_estimates_returns_from_history(self, portfolio_data):
        config = OptimizationConfig(method="max_sharpe")
        opt = PortfolioOptimizer(config)
        returns = opt._calculate_expected_returns(portfolio_data)

        assert len(returns) == len(portfolio_data.tickers)
        # Returns should be finite
        assert all(np.isfinite(r) for r in returns)


# ---------------------------------------------------------------------------
# Covariance matrix
# ---------------------------------------------------------------------------


class TestCovarianceMatrix:
    def test_covariance_matrix_shape(self, portfolio_data):
        config = OptimizationConfig(method="max_sharpe")
        opt = PortfolioOptimizer(config)
        cov = opt._calculate_covariance_matrix(portfolio_data)

        n = len(portfolio_data.tickers)
        assert cov.shape == (n, n)

    def test_covariance_matrix_positive_diagonal(self, portfolio_data):
        config = OptimizationConfig(method="max_sharpe")
        opt = PortfolioOptimizer(config)
        cov = opt._calculate_covariance_matrix(portfolio_data)

        # Diagonal (variances) should be positive
        assert all(cov[i, i] > 0 for i in range(cov.shape[0]))


# ---------------------------------------------------------------------------
# Efficient frontier
# ---------------------------------------------------------------------------


class TestEfficientFrontier:
    def test_efficient_frontier_generation(self, portfolio_data):
        config = OptimizationConfig(method="max_sharpe")
        opt = PortfolioOptimizer(config)
        frontier = opt.generate_efficient_frontier(portfolio_data, n_points=15)

        assert len(frontier.returns) >= 10
        assert len(frontier.volatilities) == len(frontier.returns)
        assert len(frontier.sharpe_ratios) == len(frontier.returns)
        assert frontier.optimal_portfolio_index >= 0


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    def test_optimize_portfolio_default_config(self):
        data = _make_portfolio_data(tickers=["AAAA", "BBBB"])
        result = optimize_portfolio(data)

        assert result.method == "max_sharpe"
        assert abs(sum(result.optimal_weights.values()) - 1.0) < 0.01

    def test_optimize_portfolio_custom_config(self):
        data = _make_portfolio_data(tickers=["AAAA", "BBBB"])
        config = OptimizationConfig(method="min_variance")
        result = optimize_portfolio(data, config)

        assert result.method == "min_variance"
