"""Tests for Finance Guru risk metrics calculator.

Tests the RiskCalculator class and convenience function with synthetic data.
No real API calls -- all data is generated with numpy/pandas.
"""

import warnings
from datetime import date, timedelta

import numpy as np
import pytest

from src.analysis.risk_metrics import RiskCalculator, calculate_risk_metrics
from src.models.risk_inputs import (
    PriceDataInput,
    RiskCalculationConfig,
    RiskMetricsOutput,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_dates(n: int, start: date | None = None) -> list[date]:
    """Generate n sequential trading dates."""
    start = start or date(2025, 1, 2)
    return [start + timedelta(days=i) for i in range(n)]


def _make_price_data(
    ticker: str = "TEST",
    n: int = 100,
    start_price: float = 100.0,
    daily_return_mean: float = 0.0005,
    daily_return_std: float = 0.02,
    seed: int = 42,
) -> PriceDataInput:
    """Build a PriceDataInput with synthetic random-walk prices."""
    rng = np.random.default_rng(seed)
    returns = rng.normal(daily_return_mean, daily_return_std, n - 1)
    prices = [start_price]
    for r in returns:
        prices.append(prices[-1] * (1 + r))
    return PriceDataInput(
        ticker=ticker,
        prices=prices,
        dates=_make_dates(n),
    )


@pytest.fixture
def config() -> RiskCalculationConfig:
    return RiskCalculationConfig(
        confidence_level=0.95,
        var_method="historical",
        risk_free_rate=0.045,
    )


@pytest.fixture
def price_data() -> PriceDataInput:
    return _make_price_data()


@pytest.fixture
def calculator(config: RiskCalculationConfig) -> RiskCalculator:
    return RiskCalculator(config)


@pytest.fixture
def benchmark_data() -> PriceDataInput:
    return _make_price_data(ticker="SPY", seed=99, daily_return_std=0.01)


# ---------------------------------------------------------------------------
# RiskCalculator -- happy path
# ---------------------------------------------------------------------------


class TestRiskCalculatorHappyPath:
    """Core metric calculations with well-formed data."""

    def test_calculate_risk_metrics_returns_output_model(
        self, calculator: RiskCalculator, price_data: PriceDataInput
    ):
        result = calculator.calculate_risk_metrics(price_data)
        assert isinstance(result, RiskMetricsOutput)
        assert result.ticker == "TEST"

    def test_var_is_negative(
        self, calculator: RiskCalculator, price_data: PriceDataInput
    ):
        result = calculator.calculate_risk_metrics(price_data)
        assert result.var_95 < 0, "VaR should be negative (represents loss)"

    def test_cvar_more_extreme_than_var(
        self, calculator: RiskCalculator, price_data: PriceDataInput
    ):
        result = calculator.calculate_risk_metrics(price_data)
        assert result.cvar_95 <= result.var_95, "CVaR should be <= VaR"

    def test_max_drawdown_non_positive(
        self, calculator: RiskCalculator, price_data: PriceDataInput
    ):
        result = calculator.calculate_risk_metrics(price_data)
        assert result.max_drawdown <= 0

    def test_annual_volatility_positive(
        self, calculator: RiskCalculator, price_data: PriceDataInput
    ):
        result = calculator.calculate_risk_metrics(price_data)
        assert result.annual_volatility > 0

    def test_sharpe_ratio_finite(
        self, calculator: RiskCalculator, price_data: PriceDataInput
    ):
        result = calculator.calculate_risk_metrics(price_data)
        assert np.isfinite(result.sharpe_ratio)

    def test_sortino_ratio_finite(
        self, calculator: RiskCalculator, price_data: PriceDataInput
    ):
        result = calculator.calculate_risk_metrics(price_data)
        assert np.isfinite(result.sortino_ratio)

    def test_beta_alpha_none_without_benchmark(
        self, calculator: RiskCalculator, price_data: PriceDataInput
    ):
        result = calculator.calculate_risk_metrics(price_data)
        assert result.beta is None
        assert result.alpha is None

    def test_beta_alpha_populated_with_benchmark(
        self,
        calculator: RiskCalculator,
        price_data: PriceDataInput,
        benchmark_data: PriceDataInput,
    ):
        result = calculator.calculate_risk_metrics(price_data, benchmark_data)
        assert result.beta is not None
        assert result.alpha is not None
        assert np.isfinite(result.beta)
        assert np.isfinite(result.alpha)


# ---------------------------------------------------------------------------
# VaR methods
# ---------------------------------------------------------------------------


class TestVaRMethods:
    """Historical vs parametric VaR."""

    def test_historical_var(self, price_data: PriceDataInput):
        config = RiskCalculationConfig(var_method="historical")
        calc = RiskCalculator(config)
        result = calc.calculate_risk_metrics(price_data)
        assert result.var_95 < 0

    def test_parametric_var(self, price_data: PriceDataInput):
        config = RiskCalculationConfig(var_method="parametric")
        calc = RiskCalculator(config)
        result = calc.calculate_risk_metrics(price_data)
        assert result.var_95 < 0

    def test_parametric_and_historical_differ(self, price_data: PriceDataInput):
        hist = RiskCalculator(RiskCalculationConfig(var_method="historical"))
        param = RiskCalculator(RiskCalculationConfig(var_method="parametric"))
        r1 = hist.calculate_risk_metrics(price_data)
        r2 = param.calculate_risk_metrics(price_data)
        # They may be close but generally won't be identical
        assert r1.var_95 != pytest.approx(r2.var_95, abs=1e-10)


# ---------------------------------------------------------------------------
# Known-answer tests
# ---------------------------------------------------------------------------


class TestKnownAnswers:
    """Tests with synthetic data where expected results can be computed."""

    def test_zero_return_sharpe_is_negative(self):
        """A flat price series has zero return, so Sharpe should be negative
        (excess return below risk-free rate)."""
        n = 60
        prices = [100.0] * n
        # Add tiny jitter to avoid zero std (which would give nan)
        rng = np.random.default_rng(0)
        prices = [100.0 + rng.normal(0, 0.001) for _ in range(n)]
        prices.sort()  # ensure monotonic-ish for valid Pydantic dates
        data = PriceDataInput(
            ticker="FLAT",
            prices=prices,
            dates=_make_dates(n),
        )
        config = RiskCalculationConfig(risk_free_rate=0.045)
        result = RiskCalculator(config).calculate_risk_metrics(data)
        # With near-zero returns and positive risk-free rate, Sharpe < 0
        assert result.sharpe_ratio < 0

    def test_monotonically_increasing_no_drawdown(self):
        """Monotonically increasing prices should have zero max drawdown."""
        n = 60
        prices = [100.0 + i * 0.5 for i in range(n)]
        data = PriceDataInput(
            ticker="UP",
            prices=prices,
            dates=_make_dates(n),
        )
        config = RiskCalculationConfig()
        result = RiskCalculator(config).calculate_risk_metrics(data)
        assert result.max_drawdown == pytest.approx(0.0)

    def test_calmar_infinite_when_no_drawdown(self):
        """Calmar ratio should be inf when there is no drawdown."""
        n = 60
        prices = [100.0 + i * 0.5 for i in range(n)]
        data = PriceDataInput(
            ticker="UP",
            prices=prices,
            dates=_make_dates(n),
        )
        config = RiskCalculationConfig()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = RiskCalculator(config).calculate_risk_metrics(data)
        assert result.calmar_ratio == float("inf")

    def test_volatility_scales_with_return_std(self):
        """Higher daily std should produce higher annual volatility."""
        low_vol = _make_price_data(daily_return_std=0.005, seed=1)
        high_vol = _make_price_data(daily_return_std=0.04, seed=1)
        config = RiskCalculationConfig()
        r_low = RiskCalculator(config).calculate_risk_metrics(low_vol)
        r_high = RiskCalculator(config).calculate_risk_metrics(high_vol)
        assert r_high.annual_volatility > r_low.annual_volatility


# ---------------------------------------------------------------------------
# Beta / Alpha
# ---------------------------------------------------------------------------


class TestBetaAlpha:
    """Beta and Alpha calculations."""

    def test_beta_of_benchmark_vs_itself_is_one(self):
        """Beta of an asset against itself should be ~1.0."""
        data = _make_price_data(ticker="SPY", n=100, seed=42)
        config = RiskCalculationConfig()
        result = RiskCalculator(config).calculate_risk_metrics(data, data)
        assert result.beta == pytest.approx(1.0, abs=0.01)

    def test_beta_positive_for_correlated_assets(self):
        """Two positively-correlated assets should have positive beta."""
        rng = np.random.default_rng(42)
        n = 100
        market_returns = rng.normal(0.0005, 0.01, n - 1)
        asset_returns = market_returns * 1.5 + rng.normal(0, 0.005, n - 1)

        dates = _make_dates(n)
        mkt_prices = [100.0]
        ast_prices = [100.0]
        for mr, ar in zip(market_returns, asset_returns, strict=True):
            mkt_prices.append(mkt_prices[-1] * (1 + mr))
            ast_prices.append(ast_prices[-1] * (1 + ar))

        mkt_data = PriceDataInput(ticker="MKT", prices=mkt_prices, dates=dates)
        ast_data = PriceDataInput(ticker="AST", prices=ast_prices, dates=dates)
        config = RiskCalculationConfig()
        result = RiskCalculator(config).calculate_risk_metrics(ast_data, mkt_data)
        assert result.beta is not None
        assert result.beta > 0


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    """Tests for the calculate_risk_metrics() wrapper."""

    def test_convenience_function_returns_output(self):
        n = 60
        prices = [100.0 + i * 0.1 + (i % 3) * 0.5 for i in range(n)]
        date_strs = [str(date(2025, 1, 2) + timedelta(days=i)) for i in range(n)]
        result = calculate_risk_metrics(
            ticker="CONV",
            prices=prices,
            dates=date_strs,
        )
        assert isinstance(result, RiskMetricsOutput)
        assert result.ticker == "CONV"

    def test_convenience_with_benchmark(self):
        n = 60
        dates_list = [str(date(2025, 1, 2) + timedelta(days=i)) for i in range(n)]
        prices = [100.0 + i * 0.2 for i in range(n)]
        bench = [200.0 + i * 0.1 for i in range(n)]
        result = calculate_risk_metrics(
            ticker="CONV",
            prices=prices,
            dates=dates_list,
            benchmark_ticker="SPY",
            benchmark_prices=bench,
            benchmark_dates=dates_list,
        )
        assert result.beta is not None
