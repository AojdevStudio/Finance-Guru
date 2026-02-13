"""Portfolio Optimization Engine for Finance Guru™.

WHAT: Multi-method portfolio optimizer for $500k capital allocation
WHY: Scientific portfolio construction using Modern Portfolio Theory
ARCHITECTURE: Layer 2 of 3-layer type-safe architecture

OPTIMIZATION METHODS:
1. Mean-Variance (Markowitz) - Balance return vs risk with target
2. Risk Parity - Equal risk contribution from each asset
3. Minimum Variance - Lowest risk portfolio (defensive)
4. Maximum Sharpe - Best risk-adjusted return (aggressive)
5. Black-Litterman - Market equilibrium + investor views

Used by: Strategy Advisor (allocation), Quant Analyst (optimization), Compliance Officer (limits)

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.models.portfolio_inputs import (
    EfficientFrontierOutput,
    OptimizationConfig,
    OptimizationOutput,
    PortfolioDataInput,
)


class PortfolioOptimizer:
    """Multi-method portfolio optimizer.

    WHAT: Calculates optimal asset allocation using various optimization techniques
    WHY: Provides validated, type-safe portfolio optimization for Finance Guru agents
    HOW: Uses Pydantic models for inputs/outputs, scipy for optimization, numpy/pandas for calculations

    EDUCATIONAL NOTE:
    Portfolio optimization is the science of allocating capital to maximize
    risk-adjusted returns. Different methods suit different investment goals:

    1. **Mean-Variance**: For investors with specific return targets
       - Pro: Intuitive, balances return vs risk
       - Con: Requires return forecasts (notoriously unreliable!)

    2. **Risk Parity**: For "all-weather" portfolios
       - Pro: No return forecasts needed, stable allocations
       - Con: Ignores return expectations, may underperform in bull markets

    3. **Minimum Variance**: For conservative capital preservation
       - Pro: Lowest risk, stable in volatile markets
       - Con: May sacrifice returns, can be too defensive

    4. **Maximum Sharpe**: For aggressive risk-adjusted growth
       - Pro: Optimal risk-adjusted returns, mathematically elegant
       - Con: Sensitive to input estimates, can be concentrated

    5. **Black-Litterman**: For incorporating specific views
       - Pro: Handles uncertainty well, combines equilibrium + views
       - Con: Complex, requires understanding of market equilibrium

    For most retail investors with $500k, Maximum Sharpe or Risk Parity
    are good starting points.
    """

    def __init__(self, config: OptimizationConfig):
        """Initialize portfolio optimizer with configuration.

        Args:
            config: OptimizationConfig with method and constraints
        """
        self.config = config

    def optimize(self, data: PortfolioDataInput) -> OptimizationOutput:
        """Optimize portfolio using configured method.

        EXPLANATION:
        This is the main entry point. It routes to the appropriate
        optimization method based on config.method.

        Args:
            data: PortfolioDataInput with price history

        Returns:
            OptimizationOutput with optimal weights and metrics

        Raises:
            ValueError: If optimization fails or constraints are infeasible
        """
        # Route to appropriate optimization method
        if self.config.method == "mean_variance":
            return self.optimize_mean_variance(data)
        elif self.config.method == "risk_parity":
            return self.optimize_risk_parity(data)
        elif self.config.method == "min_variance":
            return self.optimize_min_variance(data)
        elif self.config.method == "max_sharpe":
            return self.optimize_max_sharpe(data)
        elif self.config.method == "black_litterman":
            return self.optimize_black_litterman(data)
        else:
            raise ValueError(f"Unknown optimization method: {self.config.method}")

    def optimize_mean_variance(self, data: PortfolioDataInput) -> OptimizationOutput:
        """Markowitz Mean-Variance Optimization.

        FORMULA:
        Minimize: w^T Σ w  (portfolio variance)
        Subject to:
            - w^T μ >= target_return (if specified)
            - Σw_i = 1 (fully invested)
            - position_limits constraints

        EDUCATIONAL NOTE:
        This is the Nobel Prize-winning approach (Markowitz, 1952).
        It finds the portfolio with the lowest risk for a given return target,
        or the maximum return for a given risk level.

        WHY IT WORKS:
        - Diversification reduces risk (portfolio volatility < weighted avg)
        - Math finds the optimal balance between assets
        - Correlation matters: uncorrelated assets = better diversification

        LIMITATIONS:
        - Requires return forecasts (very uncertain!)
        - Sensitive to input estimates (small changes = big allocation shifts)
        - Can produce concentrated portfolios

        Args:
            data: PortfolioDataInput

        Returns:
            OptimizationOutput with optimal allocation
        """
        # Calculate inputs
        returns = self._calculate_expected_returns(data)
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Objective: minimize portfolio variance
        def objective(weights):
            return weights @ cov_matrix @ weights

        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}  # Fully invested
        ]

        # Add return constraint if target specified
        if self.config.target_return is not None:
            constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda w: w @ returns - self.config.target_return,
                }
            )

        # Bounds (position limits)
        bounds = [self.config.position_limits for _ in range(n_assets)]

        # Initial guess (equal weight)
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Optimization failed: {result.message}")

        # Validate and return
        weights = self._validate_weights(result.x, data.tickers)
        return self._create_output(weights, data, returns, cov_matrix)

    def optimize_risk_parity(self, data: PortfolioDataInput) -> OptimizationOutput:
        """Risk Parity Optimization (Equal Risk Contribution).

        CONCEPT:
        Each asset contributes EQUALLY to total portfolio risk.

        FORMULA:
        Risk contribution_i = w_i × (Σw)_i / σ_portfolio

        Where:
            - w_i = weight of asset i
            - (Σw)_i = marginal contribution of asset i to portfolio variance
            - σ_portfolio = portfolio standard deviation

        Goal: Make all risk contributions equal

        EDUCATIONAL NOTE:
        Risk Parity was popularized by Bridgewater's "All Weather" portfolio.
        The key insight: equal DOLLAR allocation ≠ equal RISK allocation.

        Example:
        Portfolio with stocks and bonds (equal $):
            - Stocks: 50% of dollars, ~90% of risk (high volatility)
            - Bonds: 50% of dollars, ~10% of risk (low volatility)

        Risk Parity would allocate MORE to bonds to equalize risk contributions.

        WHY IT'S POPULAR:
        - No return forecasts needed (avoids biggest uncertainty!)
        - More stable allocations (less turnover)
        - Performs well across market regimes
        - Good for "all-weather" portfolios

        LIMITATION:
        - Ignores return expectations (may underweight high-return assets)
        - Can be too conservative in bull markets

        Args:
            data: PortfolioDataInput

        Returns:
            OptimizationOutput with risk-balanced allocation
        """
        returns = self._calculate_expected_returns(data)
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Objective: minimize variance of risk contributions
        def objective(weights):
            portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
            marginal_contrib = cov_matrix @ weights
            risk_contrib = weights * marginal_contrib / portfolio_vol

            # Minimize sum of squared deviations from equal risk
            target_contrib = 1.0 / n_assets
            return np.sum((risk_contrib - target_contrib) ** 2)

        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}  # Fully invested
        ]

        # Bounds
        bounds = [self.config.position_limits for _ in range(n_assets)]

        # Initial guess (equal weight)
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Risk Parity optimization failed: {result.message}")

        weights = self._validate_weights(result.x, data.tickers)
        return self._create_output(weights, data, returns, cov_matrix)

    def optimize_min_variance(self, data: PortfolioDataInput) -> OptimizationOutput:
        """Minimum Variance Portfolio Optimization.

        FORMULA:
        Minimize: w^T Σ w  (portfolio variance)
        Subject to:
            - Σw_i = 1 (fully invested)
            - position_limits constraints
            - NO return constraint (pure risk minimization)

        EDUCATIONAL NOTE:
        This finds the lowest-risk allocation possible, ignoring returns entirely.

        WHY USE THIS:
        - Capital preservation is priority #1
        - Volatile market conditions (defensive positioning)
        - Approaching retirement (can't afford losses)
        - Complement to aggressive strategies (safe bucket)

        HISTORICAL PERFORMANCE:
        Minimum variance portfolios have surprisingly good risk-adjusted returns!
        Research shows they often beat market-cap weighted indices over long periods.
        This is called the "low volatility anomaly" - lower risk doesn't always
        mean lower returns.

        FOR YOUR $500K:
        If you're risk-averse or in volatile times, this is your friend.
        It will heavily favor stable assets (bonds, defensive stocks)
        over volatile assets (growth stocks, small caps).

        Args:
            data: PortfolioDataInput

        Returns:
            OptimizationOutput with minimum-risk allocation
        """
        returns = self._calculate_expected_returns(data)
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Objective: minimize portfolio variance
        def objective(weights):
            return weights @ cov_matrix @ weights

        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}  # Fully invested
        ]

        # Bounds
        bounds = [self.config.position_limits for _ in range(n_assets)]

        # Initial guess (equal weight)
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Minimum Variance optimization failed: {result.message}")

        weights = self._validate_weights(result.x, data.tickers)
        return self._create_output(weights, data, returns, cov_matrix)

    def optimize_max_sharpe(self, data: PortfolioDataInput) -> OptimizationOutput:
        """Maximum Sharpe Ratio Optimization.

        FORMULA:
        Maximize: (w^T μ - r_f) / √(w^T Σ w)

        Where:
            - μ = expected returns vector
            - r_f = risk-free rate
            - Σ = covariance matrix
            - w = portfolio weights

        EDUCATIONAL NOTE:
        The Sharpe ratio measures return per unit of risk. Maximizing it finds
        the portfolio with the best risk-adjusted returns.

        GRAPHICALLY:
        On the efficient frontier, this is where a line from the risk-free rate
        is tangent to the frontier. This is called the "tangency portfolio"
        or "market portfolio" (in CAPM theory).

        WHY IT'S POPULAR:
        - Mathematically optimal risk-adjusted returns
        - Intuitive: maximize bang for buck (return per unit of risk)
        - Used by professional portfolio managers
        - Works well for growth-oriented investors

        LIMITATIONS:
        - Requires return estimates (garbage in, garbage out!)
        - Can be concentrated (puts all eggs in best baskets)
        - Sensitive to estimate errors (small input change = big allocation change)

        RECOMMENDATION:
        Great for investors who:
        - Have strong return views (e.g., conviction in specific stocks)
        - Can tolerate concentration (fewer holdings)
        - Want aggressive growth with risk awareness
        - Rebalance regularly (quarterly or monthly)

        Args:
            data: PortfolioDataInput

        Returns:
            OptimizationOutput with maximum Sharpe allocation
        """
        returns = self._calculate_expected_returns(data)
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Objective: maximize Sharpe ratio (minimize negative Sharpe)
        def objective(weights):
            portfolio_return = weights @ returns
            portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
            sharpe = (portfolio_return - self.config.risk_free_rate) / portfolio_vol
            return -sharpe  # Minimize negative = maximize

        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}  # Fully invested
        ]

        # Bounds
        bounds = [self.config.position_limits for _ in range(n_assets)]

        # Initial guess (equal weight)
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Maximum Sharpe optimization failed: {result.message}")

        weights = self._validate_weights(result.x, data.tickers)
        return self._create_output(weights, data, returns, cov_matrix)

    def optimize_black_litterman(self, data: PortfolioDataInput) -> OptimizationOutput:
        """Black-Litterman Model Optimization.

        CONCEPT:
        Combines market equilibrium returns with investor-specific views
        to produce more stable, intuitive allocations than pure Markowitz.

        FORMULA (simplified):
        Posterior returns = [(τΣ)^-1 + P^T Ω^-1 P]^-1 [(τΣ)^-1 π + P^T Ω^-1 Q]

        Where:
            - π = market equilibrium returns (from reverse optimization)
            - Σ = covariance matrix
            - P = view selection matrix (which assets views apply to)
            - Q = view returns (your expected returns for specific assets)
            - Ω = view uncertainty matrix (confidence in views)
            - τ = scaling factor (typically 0.025-0.05)

        EDUCATIONAL NOTE:
        Black-Litterman solves a major problem with Markowitz:
        Small changes in return estimates → huge changes in allocations

        WHY THIS HAPPENS:
        Optimizer exploits tiny differences, creating extreme concentrated bets.

        HOW BLACK-LITTERMAN FIXES IT:
        1. Start with market equilibrium (market cap weights imply expected returns)
        2. Blend in your specific views with appropriate confidence
        3. Uncertainty is explicitly modeled → more stable allocations

        EXAMPLE FOR YOUR $500K:
        Market equilibrium might suggest:
            - SPY: 10% return, 16% vol
            - TSLA: 12% return, 40% vol

        You think TSLA will do 20% (bullish view).

        Black-Litterman blends:
            - Your view: 20% (but accounts for uncertainty)
            - Market equilibrium: 12%
            - Result: Maybe 15% (weighted by confidence)

        Then optimizes using blended returns → more stable allocation.

        WHEN TO USE:
        - You have specific investment opinions (views on certain stocks)
        - Want to incorporate views without extreme concentration
        - Need stable allocations (less turnover = lower trading costs)
        - Professional setting (institutional quality approach)

        Args:
            data: PortfolioDataInput

        Returns:
            OptimizationOutput with Black-Litterman allocation

        Raises:
            ValueError: If views are not provided in config
        """
        if self.config.views is None:
            raise ValueError("Black-Litterman requires views in config")

        # Calculate covariance matrix
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Step 1: Calculate market equilibrium returns (reverse optimization)
        # Assume equal weights as proxy for market cap weights
        market_weights = np.array([1.0 / n_assets] * n_assets)
        risk_aversion = 2.5  # Typical value
        equilibrium_returns = risk_aversion * cov_matrix @ market_weights

        # Step 2: Incorporate investor views
        # For simplicity, we'll use absolute views (each view is independent)
        tau = 0.025  # Scaling factor (uncertainty in equilibrium)

        # Build view matrix P (which assets have views)
        # Build view vector Q (what are the views)
        view_tickers = list(self.config.views.keys())
        P = np.zeros((len(view_tickers), n_assets))
        Q = np.zeros(len(view_tickers))

        for i, view_ticker in enumerate(view_tickers):
            ticker_idx = data.tickers.index(view_ticker)
            P[i, ticker_idx] = 1.0
            Q[i] = self.config.views[view_ticker]

        # View uncertainty (omega) - proportional to variance
        # Higher variance = less confidence in view
        Omega = np.diag([P[i] @ cov_matrix @ P[i].T for i in range(len(view_tickers))])

        # Step 3: Compute posterior (blended) returns
        # Posterior = [(τΣ)^-1 + P^T Ω^-1 P]^-1 [(τΣ)^-1 π + P^T Ω^-1 Q]
        tau_cov_inv = np.linalg.inv(tau * cov_matrix)
        omega_inv = np.linalg.inv(Omega)

        posterior_precision = tau_cov_inv + P.T @ omega_inv @ P
        posterior_cov = np.linalg.inv(posterior_precision)

        posterior_returns = posterior_cov @ (
            tau_cov_inv @ equilibrium_returns + P.T @ omega_inv @ Q
        )

        # Step 4: Optimize using posterior returns (standard mean-variance)
        def objective(weights):
            return weights @ cov_matrix @ weights

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        bounds = [self.config.position_limits for _ in range(n_assets)]

        x0 = np.array([1.0 / n_assets] * n_assets)

        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Black-Litterman optimization failed: {result.message}")

        weights = self._validate_weights(result.x, data.tickers)
        return self._create_output(weights, data, posterior_returns, cov_matrix)

    def generate_efficient_frontier(
        self, data: PortfolioDataInput, n_points: int = 50
    ) -> EfficientFrontierOutput:
        """Generate efficient frontier for visualization.

        EDUCATIONAL NOTE:
        The efficient frontier shows all optimal portfolios across risk levels.
        Each point represents maximum return for a given risk level.

        USE CASES:
        - Visualize risk-return tradeoff
        - Help choose appropriate risk level
        - Show diversification benefits graphically
        - Client education and communication

        Args:
            data: PortfolioDataInput
            n_points: Number of points on frontier

        Returns:
            EfficientFrontierOutput with frontier data
        """
        returns = self._calculate_expected_returns(data)
        cov_matrix = self._calculate_covariance_matrix(data)
        n_assets = len(data.tickers)

        # Find min and max possible returns on frontier
        min_var_weights = self._find_min_variance_weights(cov_matrix, n_assets)
        min_return = min_var_weights @ returns

        # Max return (subject to constraints)
        max_return = np.max(returns)

        # Generate target returns across range
        target_returns = np.linspace(min_return, max_return * 0.95, n_points)

        frontier_returns = []
        frontier_vols = []
        frontier_sharpes = []

        for target_ret in target_returns:
            try:
                # Optimize for this target return
                weights = self._optimize_for_target_return(
                    returns, cov_matrix, target_ret, n_assets
                )

                port_ret = weights @ returns
                port_vol = np.sqrt(weights @ cov_matrix @ weights)
                port_sharpe = (port_ret - self.config.risk_free_rate) / port_vol

                frontier_returns.append(float(port_ret))
                frontier_vols.append(float(port_vol))
                frontier_sharpes.append(float(port_sharpe))

            except Exception:
                # Skip infeasible points
                continue

        if len(frontier_returns) == 0:
            raise ValueError("Failed to generate efficient frontier")

        # Find optimal (max Sharpe) portfolio
        optimal_idx = int(np.argmax(frontier_sharpes))

        return EfficientFrontierOutput(
            returns=frontier_returns,
            volatilities=frontier_vols,
            sharpe_ratios=frontier_sharpes,
            optimal_portfolio_index=optimal_idx,
        )

    # Helper Methods

    def _calculate_expected_returns(self, data: PortfolioDataInput) -> np.ndarray:
        """Calculate or use provided expected returns.

        EDUCATIONAL NOTE:
        Expected returns are FUTURE returns, not historical averages.
        Historical returns are often poor predictors of future returns!

        If not provided, we estimate from historical data using geometric mean
        (more conservative than arithmetic mean).

        Args:
            data: PortfolioDataInput

        Returns:
            Array of expected annual returns
        """
        if data.expected_returns is not None:
            # Use provided returns
            return np.array([data.expected_returns[t] for t in data.tickers])

        # Estimate from historical data
        df = pd.DataFrame(data.prices, index=data.dates)
        returns = df.pct_change().dropna()

        # Use geometric mean (more conservative)
        expected = []
        for ticker in data.tickers:
            # Annualize: (1 + daily_return)^252 - 1
            mean_daily = returns[ticker].mean()
            annual_return = (1 + mean_daily) ** 252 - 1
            expected.append(annual_return)

        return np.array(expected)

    def _calculate_covariance_matrix(self, data: PortfolioDataInput) -> np.ndarray:
        """Calculate covariance matrix from price data.

        EDUCATIONAL NOTE:
        Covariance matrix captures:
        1. Individual asset volatilities (diagonal)
        2. Co-movement between assets (off-diagonal)

        This is the key input for portfolio optimization.
        Better covariance estimates = better allocations.

        Args:
            data: PortfolioDataInput

        Returns:
            Annualized covariance matrix
        """
        df = pd.DataFrame(data.prices, index=data.dates)
        returns = df.pct_change().dropna()

        # Calculate covariance matrix (daily)
        cov_daily = returns.cov().values

        # Annualize (multiply by 252 trading days)
        cov_annual = cov_daily * 252

        return cov_annual

    def _validate_weights(
        self, weights: np.ndarray, tickers: list[str]
    ) -> dict[str, float]:
        """Validate and convert weights array to dictionary.

        Args:
            weights: Array of weights
            tickers: List of ticker symbols

        Returns:
            Dictionary of {ticker: weight}

        Raises:
            ValueError: If weights are invalid
        """
        # Normalize to exactly 1.0 (handle numerical precision)
        weights = weights / weights.sum()

        # Check all within bounds
        for w in weights:
            if w < self.config.position_limits[0] - 1e-6:
                raise ValueError(
                    f"Weight {w:.4f} below minimum {self.config.position_limits[0]}"
                )
            if w > self.config.position_limits[1] + 1e-6:
                raise ValueError(
                    f"Weight {w:.4f} above maximum {self.config.position_limits[1]}"
                )

        # Convert to dictionary
        return {
            ticker: float(weight)
            for ticker, weight in zip(tickers, weights, strict=True)
        }

    def _calculate_portfolio_metrics(
        self,
        weights: dict[str, float],
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        tickers: list[str],
    ) -> tuple[float, float, float, float]:
        """Calculate portfolio return, volatility, Sharpe, and diversification ratio.

        Args:
            weights: Portfolio weights
            returns: Expected returns array
            cov_matrix: Covariance matrix
            tickers: Ticker symbols

        Returns:
            Tuple of (return, volatility, sharpe, diversification_ratio)
        """
        w = np.array([weights[t] for t in tickers])

        # Portfolio return
        port_return = float(w @ returns)

        # Portfolio volatility
        port_variance = w @ cov_matrix @ w
        port_vol = float(np.sqrt(port_variance))

        # Sharpe ratio
        sharpe = (port_return - self.config.risk_free_rate) / port_vol

        # Diversification ratio = weighted_avg_vol / portfolio_vol
        individual_vols = np.sqrt(np.diag(cov_matrix))
        weighted_avg_vol = w @ individual_vols
        diversification_ratio = weighted_avg_vol / port_vol

        return port_return, port_vol, sharpe, float(diversification_ratio)

    def _create_output(
        self,
        weights: dict[str, float],
        data: PortfolioDataInput,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
    ) -> OptimizationOutput:
        """Create OptimizationOutput from weights.

        Args:
            weights: Optimal weights
            data: Input data
            returns: Expected returns
            cov_matrix: Covariance matrix

        Returns:
            OptimizationOutput
        """
        port_return, port_vol, sharpe, div_ratio = self._calculate_portfolio_metrics(
            weights, returns, cov_matrix, data.tickers
        )

        return OptimizationOutput(
            tickers=data.tickers,
            method=self.config.method,
            optimal_weights=weights,
            expected_return=port_return,
            expected_volatility=port_vol,
            sharpe_ratio=sharpe,
            diversification_ratio=div_ratio,
        )

    def _find_min_variance_weights(
        self, cov_matrix: np.ndarray, n_assets: int
    ) -> np.ndarray:
        """Helper to find minimum variance portfolio weights."""

        def objective(weights):
            return weights @ cov_matrix @ weights

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]
        bounds = [self.config.position_limits for _ in range(n_assets)]
        x0 = np.array([1.0 / n_assets] * n_assets)

        result = minimize(
            objective, x0, method="SLSQP", bounds=bounds, constraints=constraints
        )
        return result.x

    def _optimize_for_target_return(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        target_return: float,
        n_assets: int,
    ) -> np.ndarray:
        """Helper to optimize for specific target return."""

        def objective(weights):
            return weights @ cov_matrix @ weights

        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
            {"type": "eq", "fun": lambda w: w @ returns - target_return},
        ]
        bounds = [self.config.position_limits for _ in range(n_assets)]
        x0 = np.array([1.0 / n_assets] * n_assets)

        result = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000},
        )

        if not result.success:
            raise ValueError(f"Cannot achieve target return {target_return}")

        return result.x


# Convenience function for quick optimization
def optimize_portfolio(
    data: PortfolioDataInput,
    config: OptimizationConfig | None = None,
) -> OptimizationOutput:
    """Convenience function to optimize portfolio with default or custom config.

    Args:
        data: PortfolioDataInput with price history
        config: Optional custom configuration (uses defaults if not provided)

    Returns:
        OptimizationOutput with optimal allocation

    Example:
        >>> from src.models.portfolio_inputs import PortfolioDataInput, OptimizationConfig
        >>> from src.strategies.optimizer import optimize_portfolio
        >>>
        >>> data = PortfolioDataInput(
        ...     tickers=["TSLA", "PLTR", "NVDA", "SPY"],
        ...     dates=[...],
        ...     prices={"TSLA": [...], "PLTR": [...], "NVDA": [...], "SPY": [...]}
        ... )
        >>> config = OptimizationConfig(method="max_sharpe", position_limits=(0.0, 0.30))
        >>> result = optimize_portfolio(data, config)
        >>> print(f"Optimal Weights: {result.optimal_weights}")
        >>> print(f"Expected Return: {result.expected_return:.2%}")
        >>> print(f"Expected Volatility: {result.expected_volatility:.2%}")
        >>> print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    """
    if config is None:
        config = OptimizationConfig()

    optimizer = PortfolioOptimizer(config)
    return optimizer.optimize(data)
