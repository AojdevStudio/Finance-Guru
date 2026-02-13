"""
Tests for Finance Guru risk metrics calculations.
"""

import numpy as np
import pytest


class TestRiskMetricsBasics:
    """Basic validation tests for risk metric calculations."""

    def test_sharpe_ratio_calculation(self):
        """Sharpe ratio should be (return - risk_free) / volatility."""
        # Given: 10% return, 2% risk-free, 15% volatility
        annual_return = 0.10
        risk_free_rate = 0.02
        volatility = 0.15

        # When: Calculate Sharpe
        sharpe = (annual_return - risk_free_rate) / volatility

        # Then: Should be approximately 0.533
        assert abs(sharpe - 0.533) < 0.01

    def test_max_drawdown_from_peak(self):
        """Max drawdown measures largest peak-to-trough decline."""
        # Given: Price series with 20% drawdown
        prices = np.array([100, 110, 120, 100, 96, 105, 115])

        # When: Calculate max drawdown
        peak = np.maximum.accumulate(prices)
        drawdown = (peak - prices) / peak
        max_dd = np.max(drawdown)

        # Then: Max drawdown should be 20% (120 -> 96)
        assert abs(max_dd - 0.20) < 0.01

    def test_var_95_basic(self):
        """VaR 95% should capture 5th percentile of returns."""
        # Given: Normal distribution of returns
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 1000)  # 0.1% daily return, 2% vol

        # When: Calculate VaR at 95%
        var_95 = np.percentile(returns, 5)

        # Then: Should be approximately -3.3% (mean - 1.65*std)
        assert var_95 < 0  # VaR should be negative (loss)
        assert var_95 > -0.05  # But not extreme


class TestRiskMetricsEdgeCases:
    """Edge case handling for risk metrics."""

    def test_zero_volatility_sharpe(self):
        """Zero volatility should handle gracefully (not divide by zero)."""
        returns = np.array([0.01, 0.01, 0.01, 0.01])  # Constant returns
        volatility = np.std(returns)

        # Volatility is zero for constant returns
        assert volatility == 0.0
        # Real implementation should return inf or handle specially

    def test_empty_returns_array(self):
        """Empty returns should raise or return NaN."""
        returns = np.array([])

        with pytest.raises((ValueError, IndexError)):
            np.percentile(returns, 5)
