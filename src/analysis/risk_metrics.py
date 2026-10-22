"""Risk Metrics Calculator for Finance Guru™.

This module implements comprehensive risk calculations using validated Pydantic models.
All calculations follow industry-standard financial engineering formulas.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (risk_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Each calculation includes detailed explanations of:
- WHAT: The metric being calculated
- WHY: Why this metric matters for risk assessment
- HOW: The mathematical formula being used
- INTERPRETATION: How to read the results

RISK METRICS IMPLEMENTED:
1. Value at Risk (VaR) - Historical & Parametric methods
2. Conditional VaR (CVaR) - Expected Shortfall
3. Sharpe Ratio - Risk-adjusted return
4. Sortino Ratio - Downside risk-adjusted return
5. Maximum Drawdown - Worst peak-to-trough decline
6. Calmar Ratio - Return per unit of max drawdown
7. Annual Volatility - Annualized standard deviation
8. Beta - Market sensitivity
9. Alpha - Excess return vs benchmark

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

import math
import warnings

import numpy as np
import pandas as pd
from scipy import stats

from src.models.risk_inputs import (
    PriceDataInput,
    RiskCalculationConfig,
    RiskMetricsOutput,
    RiskRatioName,
    RiskRatioUnavailableReason,
)
from src.utils.trading_calendar import TRADING_DAYS_PER_YEAR


def _cvar_at_var_threshold(var: float) -> float:
    """Return CVaR for an empty tail: no return falls at or below VaR, so report VaR."""
    warnings.warn(
        f"No returns found beyond VaR threshold of {var:.4f}. "
        "This suggests insufficient data or unusual return distribution."
    )
    return var


def _zero_risk_sharpe(mean_excess_return: float) -> float:
    """Return the Sharpe limit for a series with zero volatility.

    With no risk in the denominator the ratio is unbounded in the direction of
    the excess return, and zero when there is no excess return either.
    """
    warnings.warn(
        "Return volatility is zero, so the Sharpe ratio has zero risk in its "
        "denominator. Reporting its limit."
    )
    if mean_excess_return == 0:
        return 0.0
    return math.copysign(math.inf, mean_excess_return)


def _calmar_without_drawdown() -> float:
    """Return the Calmar ratio for a series that never fell from a peak."""
    warnings.warn(
        "Maximum drawdown is zero. Calmar ratio is undefined. "
        "This suggests the price only went up (very rare) or insufficient data."
    )
    return math.inf


class RiskCalculator:
    """Comprehensive risk metrics calculator.

    WHAT: Calculates all major risk metrics for Finance Guru agents
    WHY: Provides validated, type-safe risk analysis for portfolio decisions
    HOW: Uses Pydantic models for I/O, numpy/pandas for calculations

    USAGE EXAMPLE:
        # Create configuration
        config = RiskCalculationConfig(
            confidence_level=0.95,
            var_method="historical",
            rolling_window=252,
            risk_free_rate=0.045
        )

        # Create calculator
        calculator = RiskCalculator(config)

        # Calculate risk metrics
        results = calculator.calculate_risk_metrics(price_data)

        # Access results (all validated by Pydantic)
        print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
        print(f"Max Drawdown: {results.max_drawdown:.2%}")
    """

    def __init__(self, config: RiskCalculationConfig):
        """Initialize calculator with configuration.

        Args:
            config: Validated configuration (Pydantic model ensures correctness)

        EDUCATIONAL NOTE:
        By accepting a Pydantic model, we KNOW the config is valid.
        We don't need to check if confidence_level is between 0 and 1,
        or if risk_free_rate is reasonable - Pydantic already validated it.
        """
        self.config = config

    def calculate_risk_metrics(
        self,
        price_data: PriceDataInput,
        benchmark_data: PriceDataInput | None = None,
    ) -> RiskMetricsOutput:
        """Calculate all risk metrics for a given price series.

        Args:
            price_data: Historical price data (validated by Pydantic)
            benchmark_data: Optional benchmark for beta/alpha (e.g., SPY)

        Returns:
            RiskMetricsOutput: All calculated metrics (validated structure)

        EDUCATIONAL NOTE:
        This method orchestrates all calculations. It:
        1. Converts validated data to pandas (for easy math)
        2. Calculates returns (daily % changes)
        3. Calls private methods for each metric
        4. Returns a validated output model

        The flow is: Validated Input → Calculations → Validated Output
        This prevents calculation errors from propagating to agents.
        """
        df = pd.DataFrame(
            {
                "date": price_data.dates,
                "price": price_data.prices,
            }
        )
        df = df.set_index("date")

        returns = df["price"].pct_change().dropna()

        var_95 = self._calculate_var(returns, self.config.confidence_level)
        cvar_95 = self._calculate_cvar(returns, self.config.confidence_level)
        sharpe = self._calculate_sharpe(returns, self.config.risk_free_rate)
        sortino = self._calculate_sortino(returns, self.config.risk_free_rate)
        max_dd = self._calculate_max_drawdown(df["price"])
        calmar = self._calculate_calmar(returns, max_dd, self.config.risk_free_rate)
        vol = self._calculate_annual_volatility(returns)

        beta_val = None
        alpha_val = None
        if benchmark_data is not None:
            beta_val, alpha_val = self._calculate_beta_alpha(
                returns,
                benchmark_data,
                self.config.risk_free_rate,
            )

        ratio_values: dict[RiskRatioName, float] = {
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
        }
        reasons: dict[RiskRatioName, RiskRatioUnavailableReason] = {}
        if vol == 0:
            reasons["sharpe_ratio"] = "zero_volatility"
            reasons["sortino_ratio"] = "zero_volatility"
        elif not math.isfinite(sortino):
            reasons["sortino_ratio"] = "no_downside_volatility"
        if max_dd == 0:
            reasons["calmar_ratio"] = "no_drawdown"
        for name, value in ratio_values.items():
            if not math.isfinite(value) and name not in reasons:
                reasons[name] = "non_finite"

        return RiskMetricsOutput(
            ticker=price_data.ticker,
            calculation_date=price_data.dates[-1],
            var_95=var_95,
            cvar_95=cvar_95,
            sharpe_ratio=None if "sharpe_ratio" in reasons else sharpe,
            sortino_ratio=None if "sortino_ratio" in reasons else sortino,
            max_drawdown=max_dd,
            calmar_ratio=None if "calmar_ratio" in reasons else calmar,
            ratio_unavailable_reasons=reasons,
            annual_volatility=vol,
            beta=beta_val,
            alpha=alpha_val,
        )

    def _calculate_var(self, returns: pd.Series, confidence: float) -> float:
        """Calculate Value at Risk using configured method.

        WHAT: VaR is the maximum expected loss at a given confidence level
        WHY: Answers "What's the most I can lose on a typical bad day?"
        HOW: Two methods available:
            - Historical: Use actual historical percentile
            - Parametric: Assume normal distribution

        FORMULA (Historical):
            VaR = percentile(returns, (1 - confidence) * 100)

        FORMULA (Parametric):
            VaR = mean + (z-score * std_dev)
            where z-score for 95% confidence = -1.645

        INTERPRETATION:
            VaR of -0.035 at 95% confidence means:
            "95% of days, losses won't exceed 3.5%"
            Or equivalently: "1 in 20 days, losses will exceed 3.5%"

        Args:
            returns: Daily return series
            confidence: Confidence level (0.95 = 95%)

        Returns:
            VaR value (negative number representing loss)
        """
        if self.config.var_method == "historical":
            var = float(np.percentile(returns, (1 - confidence) * 100))
        else:
            mean_return = returns.mean()
            std_return = returns.std()
            z_score = stats.norm.ppf(1 - confidence)
            var = float(mean_return + (z_score * std_return))

        return var

    def _calculate_cvar(self, returns: pd.Series, confidence: float) -> float:
        """Calculate Conditional VaR (Expected Shortfall).

        WHAT: CVaR is the expected loss WHEN losses exceed VaR
        WHY: VaR only tells you a threshold, CVaR tells you how bad it gets beyond that
        HOW: Average of all returns worse than VaR

        FORMULA:
            CVaR = mean(returns where returns <= VaR)

        INTERPRETATION:
            If VaR is -3.5% and CVaR is -4.8%:
            "When losses DO exceed 3.5% (the worst 5% of days),
             the average loss on those days is 4.8%"

        EDUCATIONAL NOTE:
        CVaR is also called "Expected Shortfall" or "Tail VaR".
        It's considered superior to VaR because:
        1. It captures tail risk (extreme events)
        2. It's a "coherent" risk measure (mathematically well-behaved)
        3. Regulators increasingly prefer it over VaR

        Args:
            returns: Daily return series
            confidence: Confidence level (0.95 = 95%)

        Returns:
            CVaR value (negative number, more extreme than VaR)
        """
        var = self._calculate_var(returns, confidence)
        tail_returns = returns[returns <= var]

        if len(tail_returns) == 0:
            return _cvar_at_var_threshold(var)

        return float(tail_returns.mean())

    def _calculate_sharpe(self, returns: pd.Series, risk_free_rate: float) -> float:
        """Calculate Sharpe Ratio.

        WHAT: Risk-adjusted return metric
        WHY: Answers "Am I being paid enough for the risk I'm taking?"
        HOW: Excess return divided by total volatility

        FORMULA:
            Sharpe = (mean_return - risk_free_rate) / std_dev
            (Annualized by multiplying by sqrt(252))

        INTERPRETATION:
            Sharpe of 1.25 means:
            "For every 1% of volatility you endure, you earn 1.25% excess return"

            Rule of thumb:
            < 1.0: Poor risk-adjusted return
            1.0-2.0: Good risk-adjusted return
            > 2.0: Excellent risk-adjusted return

        EDUCATIONAL NOTE:
        The Sharpe Ratio was developed by William Sharpe in 1966.
        It's the most widely used risk-adjusted performance metric.
        Higher is better - it rewards high returns and penalizes volatility.

        Args:
            returns: Daily return series
            risk_free_rate: Annual risk-free rate (e.g., 0.045 = 4.5%)

        Returns:
            Annualized Sharpe Ratio
        """
        daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR

        excess_returns = returns - daily_rf
        volatility = returns.std()
        if volatility == 0:
            return _zero_risk_sharpe(excess_returns.mean())

        sharpe = excess_returns.mean() / volatility

        annualized_sharpe = sharpe * np.sqrt(TRADING_DAYS_PER_YEAR)

        return float(annualized_sharpe)

    def _calculate_sortino(self, returns: pd.Series, risk_free_rate: float) -> float:
        """Calculate Sortino Ratio.

        WHAT: Downside risk-adjusted return metric
        WHY: Like Sharpe but only penalizes downside volatility
        HOW: Excess return divided by downside deviation

        FORMULA:
            Sortino = (mean_return - risk_free_rate) / downside_std
            where downside_std = std(returns where returns < 0)

        INTERPRETATION:
            Sortino of 1.58 means:
            "For every 1% of DOWNSIDE volatility, you earn 1.58% excess return"

        WHY IT MATTERS:
        The Sortino Ratio is superior to Sharpe for asymmetric strategies:
        - Investors don't mind upside volatility (big gains are good!)
        - We only care about downside volatility (losses)
        - Sortino captures this by only penalizing negative returns

        EDUCATIONAL NOTE:
        Named after Frank Sortino, who argued that Sharpe unfairly penalizes
        upside volatility. If a stock goes up 50% one day and down 2% the next,
        Sharpe sees high volatility (bad), but Sortino sees limited downside (good).

        Args:
            returns: Daily return series
            risk_free_rate: Annual risk-free rate

        Returns:
            Annualized Sortino Ratio
        """
        daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR

        excess_returns = returns - daily_rf

        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            warnings.warn(
                "No negative returns found. Sortino ratio may be unreliable. "
                "This suggests either insufficient data or an unusual return distribution."
            )
            return self._calculate_sharpe(returns, risk_free_rate)

        downside_std = downside_returns.std()

        sortino = excess_returns.mean() / downside_std

        annualized_sortino = sortino * np.sqrt(TRADING_DAYS_PER_YEAR)

        return float(annualized_sortino)

    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate Maximum Drawdown.

        WHAT: Largest peak-to-trough decline
        WHY: Answers "What was the worst loss from peak to bottom?"
        HOW: Track running maximum, calculate % decline from each peak

        FORMULA:
            For each point: drawdown = (price - running_max) / running_max
            Max Drawdown = minimum(all drawdowns)

        INTERPRETATION:
            Max Drawdown of -0.32 means:
            "At the worst point, the security was down 32% from its peak"

        WHY IT MATTERS:
        Max Drawdown tells you about pain tolerance:
        - -10%: Mild correction, most investors can handle
        - -20%: Bear market territory, tests conviction
        - -50%: Catastrophic loss, many investors capitulate

        EDUCATIONAL NOTE:
        Max Drawdown is a measure of "worst-case" historical loss.
        It's particularly relevant for:
        1. Aggressive portfolios (how bad can it get?)
        2. Leveraged strategies (drawdowns amplified)
        3. Psychological resilience (can you stomach this?)

        Args:
            prices: Price series (NOT returns)

        Returns:
            Maximum drawdown (negative value or zero)
        """
        running_max = prices.expanding().max()

        drawdowns = (prices - running_max) / running_max

        max_dd = float(drawdowns.min())

        return max_dd

    def _calculate_calmar(
        self, returns: pd.Series, max_drawdown: float, risk_free_rate: float
    ) -> float:
        """Calculate Calmar Ratio.

        WHAT: Return per unit of maximum drawdown
        WHY: Measures risk-adjusted return using worst-case loss
        HOW: Annualized return divided by absolute max drawdown

        FORMULA:
            Calmar = annualized_return / abs(max_drawdown)

        INTERPRETATION:
            Calmar of 0.85 means:
            "For every 1% of maximum drawdown, you earned 0.85% annual return"

        WHY IT MATTERS:
        The Calmar Ratio is particularly useful for:
        1. Comparing strategies with different drawdown profiles
        2. Evaluating hedge funds (focuses on downside protection)
        3. Risk-averse investors (prioritizes avoiding large losses)

        Higher is better - it rewards strategies that minimize drawdowns
        while maximizing returns.

        EDUCATIONAL NOTE:
        Named after the newsletter "California Managed Accounts Reports".
        Originally designed for evaluating commodity trading advisors (CTAs).
        Typically uses 3-year performance data.

        Args:
            returns: Daily return series
            max_drawdown: Pre-calculated maximum drawdown
            risk_free_rate: Annual risk-free rate

        Returns:
            Calmar Ratio
        """
        annualized_return = returns.mean() * TRADING_DAYS_PER_YEAR

        if max_drawdown == 0:
            return _calmar_without_drawdown()

        calmar = annualized_return / abs(max_drawdown)

        return float(calmar)

    def _calculate_annual_volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility.

        WHAT: Annualized standard deviation of returns
        WHY: Measures how much the price "bounces around"
        HOW: Standard deviation of daily returns, annualized

        FORMULA:
            Annual Volatility = daily_std * sqrt(252)

        INTERPRETATION:
            Volatility of 0.42 means:
            "Annual price movements have a standard deviation of 42%"

        In practical terms:
        - ~68% of years will have returns within ±42% of the mean
        - ~95% of years will have returns within ±84% of the mean (2 * 42%)

        BENCHMARKS:
            0.10-0.20: Low volatility (large-cap stocks, bonds)
            0.20-0.40: Medium volatility (typical stocks)
            0.40-0.80: High volatility (growth stocks, small caps)
            0.80+: Extreme volatility (crypto, penny stocks)

        EDUCATIONAL NOTE:
        Volatility is the square root of variance. We annualize by
        multiplying by sqrt(252) because:
        1. Variance scales linearly with time
        2. Std dev is sqrt(variance)
        3. Therefore std dev scales with sqrt(time)
        4. sqrt(252 days) annualizes daily std dev

        Args:
            returns: Daily return series

        Returns:
            Annualized volatility (always positive)
        """
        daily_std = returns.std()

        annual_vol = daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)

        return float(annual_vol)

    def _calculate_beta_alpha(
        self,
        returns: pd.Series,
        benchmark_data: PriceDataInput,
        risk_free_rate: float,
    ) -> tuple[float, float]:
        """Calculate Beta and Alpha vs a benchmark.

        WHAT:
            - Beta: Sensitivity to benchmark movements
            - Alpha: Excess return beyond what beta predicts

        WHY:
            - Beta tells you systematic risk (market-related)
            - Alpha tells you idiosyncratic return (skill or luck)

        HOW: Linear regression of asset returns vs benchmark returns

        FORMULAS:
            Beta = covariance(asset, benchmark) / variance(benchmark)
            Alpha = mean_return - (risk_free_rate + beta * benchmark_excess_return)

        INTERPRETATION:
            Beta of 1.8 means:
            "When the market moves 1%, this stock typically moves 1.8%"

            Beta Categories:
            < 0: Inverse relationship (rare, e.g., gold during crises)
            0-0.5: Low systematic risk (defensive stocks)
            0.5-1.5: Average systematic risk (typical stocks)
            > 1.5: High systematic risk (aggressive/volatile stocks)

            Alpha of 0.05 (5%) means:
            "This stock outperformed what its beta predicts by 5% annually"

        EDUCATIONAL NOTE:
        Beta and Alpha come from the Capital Asset Pricing Model (CAPM):
            Expected Return = Risk-Free Rate + Beta * Market Risk Premium

        Alpha is the difference between actual return and CAPM expected return.
        Positive alpha suggests skill (or luck), negative alpha suggests
        underperformance relative to risk taken.

        Args:
            returns: Asset daily returns
            benchmark_data: Benchmark price data (e.g., SPY for S&P 500)
            risk_free_rate: Annual risk-free rate

        Returns:
            Tuple of (beta, alpha)
        """
        benchmark_df = pd.DataFrame(
            {
                "date": benchmark_data.dates,
                "price": benchmark_data.prices,
            }
        )
        benchmark_df = benchmark_df.set_index("date")
        benchmark_returns = benchmark_df["price"].pct_change().dropna()

        aligned_data = pd.DataFrame(
            {
                "asset": returns,
                "benchmark": benchmark_returns,
            }
        ).dropna()

        if len(aligned_data) < 30:
            warnings.warn(
                f"Only {len(aligned_data)} overlapping data points for beta/alpha. "
                "Recommend at least 30 points for reliable estimates. "
                "Results may be unreliable."
            )

        asset_returns = aligned_data["asset"]
        bench_returns = aligned_data["benchmark"]

        covariance = asset_returns.cov(bench_returns)
        benchmark_variance = bench_returns.var()

        beta = float(covariance / benchmark_variance)

        daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR

        asset_excess_return = (asset_returns.mean() - daily_rf) * TRADING_DAYS_PER_YEAR
        benchmark_excess_return = (
            bench_returns.mean() - daily_rf
        ) * TRADING_DAYS_PER_YEAR

        expected_return = risk_free_rate + beta * benchmark_excess_return

        alpha = float(asset_excess_return - expected_return + risk_free_rate)

        return (beta, alpha)


def calculate_risk_metrics(
    ticker: str,
    prices: list[float],
    dates: list[str],
    benchmark_ticker: str | None = None,
    benchmark_prices: list[float] | None = None,
    benchmark_dates: list[str] | None = None,
    **config_kwargs,
) -> RiskMetricsOutput:
    """Convenience function for calculating risk metrics without manually creating models.

    EDUCATIONAL NOTE:
    This function is a "wrapper" that handles the Pydantic model creation for you.
    It's useful for quick calculations, but for production code, prefer creating
    the models explicitly (better type checking and IDE support).

    Args:
        ticker: Stock ticker symbol
        prices: List of historical prices
        dates: List of corresponding dates (YYYY-MM-DD format)
        benchmark_ticker: Optional benchmark ticker
        benchmark_prices: Optional benchmark prices
        benchmark_dates: Optional benchmark dates
        **config_kwargs: Additional config options (confidence_level, var_method, etc.)

    Returns:
        RiskMetricsOutput with all calculated metrics

    Example:
        results = calculate_risk_metrics(
            ticker="TSLA",
            prices=[250.0, 252.5, 248.0, ...],
            dates=["2025-09-01", "2025-09-02", ...],
            confidence_level=0.95,
            var_method="historical"
        )
    """
    from datetime import date as date_type

    date_objects = [date_type.fromisoformat(d) for d in dates]

    price_data = PriceDataInput(
        ticker=ticker,
        prices=prices,
        dates=date_objects,
    )

    benchmark_data = None
    if benchmark_ticker and benchmark_prices and benchmark_dates:
        benchmark_date_objects = [date_type.fromisoformat(d) for d in benchmark_dates]
        benchmark_data = PriceDataInput(
            ticker=benchmark_ticker,
            prices=benchmark_prices,
            dates=benchmark_date_objects,
        )

    config = RiskCalculationConfig(**config_kwargs)

    calculator = RiskCalculator(config)
    return calculator.calculate_risk_metrics(price_data, benchmark_data)


__all__ = [
    "RiskCalculator",
    "calculate_risk_metrics",
]
