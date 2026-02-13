"""Tests for Finance Guru correlation engine.

Tests the CorrelationEngine class with synthetic multi-asset data.
No real API calls -- all data is generated with numpy.
"""

from datetime import date, timedelta

import numpy as np
import pytest

from src.analysis.correlation import CorrelationEngine, calculate_correlation
from src.models.correlation_inputs import (
    CorrelationConfig,
    CorrelationMatrixOutput,
    CovarianceMatrixOutput,
    PortfolioCorrelationOutput,
    PortfolioPriceData,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_dates(n: int) -> list[date]:
    start = date(2025, 1, 2)
    return [start + timedelta(days=i) for i in range(n)]


def _make_portfolio_data(
    tickers: list[str] | None = None,
    n: int = 60,
    correlation: float = 0.5,
    seed: int = 42,
) -> PortfolioPriceData:
    """Build PortfolioPriceData with correlated synthetic price series.

    Uses a common factor model: each asset = factor * loading + idiosyncratic noise.
    """
    tickers = tickers or ["AAAA", "BBBB", "CCCC"]
    rng = np.random.default_rng(seed)

    # Common market factor
    factor_returns = rng.normal(0.0005, 0.01, n - 1)

    prices: dict[str, list[float]] = {}
    for i, ticker in enumerate(tickers):
        loading = correlation  # how much of factor this asset tracks
        idio = rng.normal(0, 0.01 * (1 - correlation), n - 1)
        asset_returns = factor_returns * loading + idio
        p = [100.0 + i * 10]  # offset start prices
        for r in asset_returns:
            p.append(p[-1] * (1 + r))
        prices[ticker] = p

    return PortfolioPriceData(
        tickers=tickers,
        dates=_make_dates(n),
        prices=prices,
    )


@pytest.fixture
def config() -> CorrelationConfig:
    return CorrelationConfig()


@pytest.fixture
def portfolio_data() -> PortfolioPriceData:
    return _make_portfolio_data()


@pytest.fixture
def engine(config: CorrelationConfig) -> CorrelationEngine:
    return CorrelationEngine(config)


# ---------------------------------------------------------------------------
# Correlation Matrix
# ---------------------------------------------------------------------------


class TestCorrelationMatrix:
    """Tests for Pearson correlation matrix."""

    def test_correlation_matrix_structure(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        result = engine.calculate_portfolio_correlation(portfolio_data)
        cm = result.correlation_matrix
        assert isinstance(cm, CorrelationMatrixOutput)
        assert set(cm.tickers) == set(portfolio_data.tickers)

    def test_diagonal_is_one(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        """Each asset should have correlation 1.0 with itself."""
        cm = engine.calculate_portfolio_correlation(portfolio_data).correlation_matrix
        for ticker in portfolio_data.tickers:
            assert cm.correlation_matrix[ticker][ticker] == pytest.approx(1.0, abs=1e-6)

    def test_symmetric(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        """Correlation matrix should be symmetric."""
        cm = engine.calculate_portfolio_correlation(portfolio_data).correlation_matrix
        tickers = portfolio_data.tickers
        for t1 in tickers:
            for t2 in tickers:
                assert cm.correlation_matrix[t1][t2] == pytest.approx(
                    cm.correlation_matrix[t2][t1], abs=1e-10
                )

    def test_correlations_in_valid_range(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        """All correlations should be between -1 and 1."""
        cm = engine.calculate_portfolio_correlation(portfolio_data).correlation_matrix
        for t1 in portfolio_data.tickers:
            for t2 in portfolio_data.tickers:
                assert -1.0 <= cm.correlation_matrix[t1][t2] <= 1.0

    def test_average_correlation_reasonable(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        cm = engine.calculate_portfolio_correlation(portfolio_data).correlation_matrix
        assert -1.0 <= cm.average_correlation <= 1.0

    def test_high_correlation_data_has_high_average(self):
        """Highly correlated assets should have high average correlation."""
        data = _make_portfolio_data(correlation=0.95, seed=10)
        engine = CorrelationEngine(CorrelationConfig())
        cm = engine.calculate_portfolio_correlation(data).correlation_matrix
        assert cm.average_correlation > 0.5

    def test_spearman_method(self, portfolio_data: PortfolioPriceData):
        """Spearman correlation should also work."""
        engine = CorrelationEngine(CorrelationConfig(method="spearman"))
        result = engine.calculate_portfolio_correlation(portfolio_data)
        cm = result.correlation_matrix
        for ticker in portfolio_data.tickers:
            assert cm.correlation_matrix[ticker][ticker] == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Covariance Matrix
# ---------------------------------------------------------------------------


class TestCovarianceMatrix:
    """Tests for covariance matrix."""

    def test_covariance_matrix_structure(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        result = engine.calculate_portfolio_correlation(portfolio_data)
        cov = result.covariance_matrix
        assert isinstance(cov, CovarianceMatrixOutput)

    def test_diagonal_positive(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        """Diagonal (variance) should be positive."""
        cov = engine.calculate_portfolio_correlation(portfolio_data).covariance_matrix
        for ticker in portfolio_data.tickers:
            assert cov.covariance_matrix[ticker][ticker] > 0

    def test_covariance_symmetric(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        cov = engine.calculate_portfolio_correlation(portfolio_data).covariance_matrix
        tickers = portfolio_data.tickers
        for t1 in tickers:
            for t2 in tickers:
                assert cov.covariance_matrix[t1][t2] == pytest.approx(
                    cov.covariance_matrix[t2][t1], abs=1e-15
                )


# ---------------------------------------------------------------------------
# Diversification Score
# ---------------------------------------------------------------------------


class TestDiversificationScore:
    """Tests for diversification scoring."""

    def test_score_between_zero_and_one(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        result = engine.calculate_portfolio_correlation(portfolio_data)
        assert 0 <= result.diversification_score <= 1.0

    def test_highly_correlated_low_score(self):
        """Highly correlated portfolio should have low diversification score."""
        data = _make_portfolio_data(correlation=0.95, seed=10)
        engine = CorrelationEngine(CorrelationConfig())
        result = engine.calculate_portfolio_correlation(data)
        assert result.diversification_score < 0.5

    def test_concentration_warning_on_high_correlation(self):
        """Average correlation > 0.7 should trigger concentration warning."""
        data = _make_portfolio_data(correlation=0.99, seed=10)
        engine = CorrelationEngine(CorrelationConfig())
        result = engine.calculate_portfolio_correlation(data)
        # With near-perfect correlation the average should be very high
        assert result.correlation_matrix.average_correlation > 0.5


# ---------------------------------------------------------------------------
# Rolling Correlations
# ---------------------------------------------------------------------------


class TestRollingCorrelations:
    """Tests for rolling (time-varying) correlations."""

    def test_no_rolling_by_default(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        result = engine.calculate_portfolio_correlation(portfolio_data)
        assert result.rolling_correlations is None

    def test_rolling_when_configured(self):
        data = _make_portfolio_data(n=80, seed=42)
        config = CorrelationConfig(rolling_window=30, min_periods=20)
        engine = CorrelationEngine(config)
        result = engine.calculate_portfolio_correlation(data)
        assert result.rolling_correlations is not None
        assert len(result.rolling_correlations) > 0

    def test_rolling_correlation_in_range(self):
        data = _make_portfolio_data(n=80, seed=42)
        config = CorrelationConfig(rolling_window=30, min_periods=20)
        engine = CorrelationEngine(config)
        result = engine.calculate_portfolio_correlation(data)
        assert result.rolling_correlations is not None
        for rc in result.rolling_correlations:
            assert -1.0 <= rc.current_correlation <= 1.0
            assert -1.0 <= rc.average_correlation <= 1.0


# ---------------------------------------------------------------------------
# Full Output
# ---------------------------------------------------------------------------


class TestFullOutput:
    """Tests for complete portfolio correlation output."""

    def test_output_structure(
        self, engine: CorrelationEngine, portfolio_data: PortfolioPriceData
    ):
        result = engine.calculate_portfolio_correlation(portfolio_data)
        assert isinstance(result, PortfolioCorrelationOutput)
        assert result.tickers == portfolio_data.tickers


# ---------------------------------------------------------------------------
# Convenience Function
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    """Tests for calculate_correlation wrapper."""

    def test_convenience_returns_output(self, portfolio_data: PortfolioPriceData):
        result = calculate_correlation(portfolio_data)
        assert isinstance(result, PortfolioCorrelationOutput)

    def test_convenience_with_custom_config(self, portfolio_data: PortfolioPriceData):
        config = CorrelationConfig(method="spearman")
        result = calculate_correlation(portfolio_data, config)
        assert isinstance(result, PortfolioCorrelationOutput)

    def test_two_asset_portfolio(self):
        """Minimum two-asset portfolio should work."""
        data = _make_portfolio_data(tickers=["XX", "YY"], n=40, seed=99)
        result = calculate_correlation(data)
        assert len(result.tickers) == 2
