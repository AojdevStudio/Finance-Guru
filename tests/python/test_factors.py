"""Tests for Factor Analysis calculator.

Tests cover:
- CAPM (1-factor) regression
- Fama-French 3-factor model
- Carhart 4-factor model
- Factor exposure estimation
- Return attribution
- Summary and recommendation generation
- Convenience function

RUNNING TESTS:
    uv run pytest tests/python/test_factors.py -v
"""

import numpy as np
import pytest

from src.analysis.factors import HIGH_MARKET_BETA, FactorAnalyzer, analyze_factors
from src.models.factors_inputs import FactorDataInput

FIXTURE_MARKET_BETA = 1.2
AGGRESSIVE_MARKET_BETA = 2.0


def _make_factor_data(
    n=60, seed=42, include_smb=True, include_hml=True, include_mom=False
):
    """Build synthetic factor data with controlled randomness."""
    rng = np.random.RandomState(seed)

    market_returns = rng.normal(0.0004, 0.01, n).tolist()

    asset_returns = [
        m * FIXTURE_MARKET_BETA + rng.normal(0.0001, 0.005) for m in market_returns
    ]

    smb_returns = rng.normal(0.0001, 0.005, n).tolist() if include_smb else None
    hml_returns = rng.normal(-0.0001, 0.004, n).tolist() if include_hml else None
    mom_returns = rng.normal(0.0002, 0.006, n).tolist() if include_mom else None

    return FactorDataInput(
        ticker="TSLA",
        asset_returns=asset_returns,
        market_returns=market_returns,
        smb_returns=smb_returns,
        hml_returns=hml_returns,
        mom_returns=mom_returns,
        risk_free_rate=0.045,
    )


@pytest.fixture
def factor_data_1f():
    """CAPM (1-factor) data."""
    return _make_factor_data(include_smb=False, include_hml=False, include_mom=False)


@pytest.fixture
def factor_data_3f():
    """Fama-French 3-factor data."""
    return _make_factor_data(include_smb=True, include_hml=True, include_mom=False)


@pytest.fixture
def factor_data_4f():
    """Carhart 4-factor data."""
    return _make_factor_data(include_smb=True, include_hml=True, include_mom=True)


class TestFactorAnalyzer:
    def test_capm_analysis(self, factor_data_1f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_1f)

        assert result.exposure.ticker == "TSLA"
        assert result.exposure.market_beta is not None
        assert result.exposure.size_beta is None
        assert result.exposure.value_beta is None
        assert result.exposure.momentum_beta is None
        assert 0 <= result.exposure.r_squared <= 1

    def test_three_factor_analysis(self, factor_data_3f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_3f)

        assert result.exposure.market_beta is not None
        assert result.exposure.size_beta is not None
        assert result.exposure.value_beta is not None
        assert result.exposure.momentum_beta is None

    def test_four_factor_analysis(self, factor_data_4f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_4f)

        assert result.exposure.market_beta is not None
        assert result.exposure.size_beta is not None
        assert result.exposure.value_beta is not None
        assert result.exposure.momentum_beta is not None


class TestExposures:
    def test_market_beta_reasonable(self, factor_data_3f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_3f)

        assert 0.5 < result.exposure.market_beta < 2.5

    def test_r_squared_between_0_and_1(self, factor_data_3f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_3f)

        assert 0 <= result.exposure.r_squared <= 1

    def test_alpha_tstat_calculated(self, factor_data_3f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_3f)

        assert isinstance(result.exposure.alpha_tstat, float)
        assert isinstance(result.exposure.market_beta_tstat, float)


class TestAttribution:
    def test_attribution_has_market_component(self, factor_data_3f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_3f)

        assert result.attribution.market_attribution is not None
        assert isinstance(result.attribution.total_return, float)

    def test_attribution_has_size_and_value(self, factor_data_3f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_3f)

        assert result.attribution.size_attribution is not None
        assert result.attribution.value_attribution is not None

    def test_attribution_importance_bounded(self, factor_data_3f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_3f)

        assert 0 <= result.attribution.market_importance <= 1
        assert 0 <= result.attribution.alpha_importance <= 1


class TestSummaryAndRecommendations:
    def test_summary_is_string(self, factor_data_3f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_3f)

        assert isinstance(result.summary, str)
        assert "TSLA" in result.summary

    def test_recommendations_is_list(self, factor_data_3f):
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(factor_data_3f)

        assert isinstance(result.recommendations, list)

    def test_high_beta_recommendation(self):
        """A beta above HIGH_MARKET_BETA generates the hedging recommendation."""
        rng = np.random.RandomState(99)
        n = 60
        market_returns = rng.normal(0.0004, 0.01, n).tolist()
        asset_returns = [
            m * AGGRESSIVE_MARKET_BETA + rng.normal(0.0, 0.003) for m in market_returns
        ]

        data = FactorDataInput(
            ticker="TSLA",
            asset_returns=asset_returns,
            market_returns=market_returns,
        )
        analyzer = FactorAnalyzer()
        result = analyzer.analyze(data)

        assert result.exposure.market_beta > HIGH_MARKET_BETA
        assert any(rec.startswith("High market beta") for rec in result.recommendations)


class TestConvenienceFunction:
    def test_analyze_factors_capm(self):
        rng = np.random.RandomState(42)
        n = 60
        market_returns = rng.normal(0.0004, 0.01, n).tolist()
        asset_returns = [
            m * FIXTURE_MARKET_BETA + rng.normal(0.0001, 0.005) for m in market_returns
        ]

        result = analyze_factors(
            ticker="TSLA",
            asset_returns=asset_returns,
            market_returns=market_returns,
        )

        assert result.exposure.ticker == "TSLA"
        assert result.exposure.market_beta is not None

    def test_analyze_factors_with_all_factors(self):
        rng = np.random.RandomState(42)
        n = 60
        market_returns = rng.normal(0.0004, 0.01, n).tolist()
        asset_returns = [
            m * FIXTURE_MARKET_BETA + rng.normal(0.0001, 0.005) for m in market_returns
        ]
        smb = rng.normal(0.0001, 0.005, n).tolist()
        hml = rng.normal(-0.0001, 0.004, n).tolist()
        mom = rng.normal(0.0002, 0.006, n).tolist()

        result = analyze_factors(
            ticker="TSLA",
            asset_returns=asset_returns,
            market_returns=market_returns,
            smb_returns=smb,
            hml_returns=hml,
            mom_returns=mom,
        )

        assert result.exposure.size_beta is not None
        assert result.exposure.value_beta is not None
        assert result.exposure.momentum_beta is not None
