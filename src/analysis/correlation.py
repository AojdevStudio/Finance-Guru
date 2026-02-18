"""Correlation and Covariance Engine for Finance Guru.

WHAT: Calculates portfolio correlation and covariance for diversification analysis
WHY: Essential for portfolio construction, risk management, and hedge identification
ARCHITECTURE: Layer 2 of 3-layer type-safe architecture

ANALYTICS:
- Pearson correlation matrices
- Covariance matrices
- Rolling (time-varying) correlations
- Portfolio diversification scoring
- Concentration risk detection

Used by: Strategy Advisor (diversification), Quant Analyst (optimization), Risk Assessment
"""

import numpy as np
import pandas as pd

from src.models.correlation_inputs import (
    CorrelationConfig,
    CorrelationMatrixOutput,
    CovarianceMatrixOutput,
    PortfolioCorrelationOutput,
    PortfolioPriceData,
    RollingCorrelationOutput,
)


class CorrelationEngine:
    """WHAT: Calculates correlation and covariance for portfolio diversification analysis
    WHY: Provides validated, type-safe correlation analysis for Finance Guru agents
    HOW: Uses Pydantic models for inputs/outputs, pandas/numpy for calculations.

    EDUCATIONAL NOTE:
    This engine helps answer critical portfolio questions:

    1. **Are my holdings diversified?**
       - Low average correlation (<0.5) = Well diversified
       - High average correlation (>0.7) = Concentration risk

    2. **Do I have effective hedges?**
       - Negative correlations = Natural hedges (when one drops, other rises)
       - Look for pairs with correlation < -0.3

    3. **Is correlation stable or changing?**
       - Rolling correlation shows regime shifts
       - Correlation often spikes during crises (diversification fails!)

    4. **How much risk am I taking?**
       - Covariance matrix feeds into portfolio variance calculation
       - Higher covariances = more portfolio risk
    """

    def __init__(self, config: CorrelationConfig):
        """Initialize correlation engine with configuration.

        Args:
            config: CorrelationConfig with analysis settings
        """
        self.config = config

    def calculate_portfolio_correlation(
        self,
        data: PortfolioPriceData,
    ) -> PortfolioCorrelationOutput:
        """Calculate comprehensive correlation analysis for portfolio.

        EXPLANATION:
        This is the main entry point. It orchestrates all correlation calculations
        and returns a complete diversification assessment. Because we use Pydantic
        models, we KNOW the inputs are valid and synchronized before calculating.

        Args:
            data: PortfolioPriceData with synchronized price series

        Returns:
            PortfolioCorrelationOutput with full correlation analysis
        """
        # Convert to DataFrame for calculations
        df = pd.DataFrame(data.prices, index=data.dates)

        # Calculate returns (correlation uses returns, not prices)
        returns = df.pct_change().dropna()

        # Calculate correlation matrix
        corr_matrix = self._calculate_correlation_matrix(returns, data.tickers)

        # Calculate covariance matrix
        cov_matrix = self._calculate_covariance_matrix(returns, data.tickers)

        # Calculate portfolio-level metrics
        div_score = self._calculate_diversification_score(
            corr_matrix.correlation_matrix
        )
        concentration_warning = corr_matrix.average_correlation > 0.7

        # Calculate rolling correlations if requested
        rolling_corrs = None
        if self.config.rolling_window is not None:
            rolling_corrs = self._calculate_rolling_correlations(returns, data.tickers)

        return PortfolioCorrelationOutput(
            calculation_date=data.dates[-1],
            tickers=data.tickers,
            correlation_matrix=corr_matrix,
            covariance_matrix=cov_matrix,
            diversification_score=div_score,
            concentration_warning=concentration_warning,
            rolling_correlations=rolling_corrs,
        )

    def _calculate_correlation_matrix(
        self,
        returns: pd.DataFrame,
        tickers: list[str],
    ) -> CorrelationMatrixOutput:
        """Calculate correlation matrix between all assets.

        FORMULA:
        Pearson correlation between X and Y:
            ρ(X,Y) = Cov(X,Y) / (σ_X × σ_Y)

        Where:
            - Cov(X,Y) = covariance between X and Y
            - σ_X = standard deviation of X
            - σ_Y = standard deviation of Y

        EDUCATIONAL NOTE:
        Correlation is "standardized covariance" - it removes the scale
        and gives you a number between -1 and +1 that's easy to interpret:

        - 1.0: Perfect positive correlation (always move together)
        - 0.5-0.7: Strong positive correlation (usually move together)
        - 0.3-0.5: Moderate correlation (sometimes move together)
        - 0.0-0.3: Weak correlation (mostly independent)
        - <0.0: Negative correlation (move opposite - HEDGE!)

        Args:
            returns: DataFrame of asset returns
            tickers: List of ticker symbols

        Returns:
            CorrelationMatrixOutput with full correlation matrix
        """
        # Calculate correlation matrix using pandas
        if self.config.method == "pearson":
            corr_df = returns.corr(method="pearson")
        else:  # spearman
            corr_df = returns.corr(method="spearman")

        # Convert to nested dict format
        corr_dict = {}
        for ticker1 in tickers:
            corr_dict[ticker1] = {}
            for ticker2 in tickers:
                corr_dict[ticker1][ticker2] = float(corr_df.loc[ticker1, ticker2])

        # Calculate average correlation (excluding diagonal)
        # This tells us overall portfolio concentration
        off_diagonal_values = []
        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i < j:  # Only upper triangle (avoid counting twice and diagonal)
                    off_diagonal_values.append(corr_dict[ticker1][ticker2])

        avg_corr = float(np.mean(off_diagonal_values)) if off_diagonal_values else 0.0

        # Get calculation date (handle both datetime and date objects)
        calc_date = returns.index[-1]
        if hasattr(calc_date, "date"):
            calc_date = calc_date.date()

        return CorrelationMatrixOutput(
            tickers=tickers,
            calculation_date=calc_date,
            correlation_matrix=corr_dict,
            average_correlation=avg_corr,
        )

    def _calculate_covariance_matrix(
        self,
        returns: pd.DataFrame,
        tickers: list[str],
    ) -> CovarianceMatrixOutput:
        """Calculate covariance matrix between all assets.

        FORMULA:
        Covariance between X and Y:
            Cov(X,Y) = E[(X - μ_X)(Y - μ_Y)]

        Where:
            - E[...] = expected value (average)
            - μ_X = mean of X
            - μ_Y = mean of Y

        EDUCATIONAL NOTE:
        Covariance measures how two assets vary together in their actual units.

        INTERPRETATION:
        - Positive covariance: Assets tend to move in same direction
        - Negative covariance: Assets tend to move in opposite directions
        - Magnitude matters: Higher absolute value = stronger relationship

        WHY WE NEED THIS:
        Portfolio variance formula uses covariance matrix:
            σ²_portfolio = w^T × Σ × w

        Where:
            - w = portfolio weights
            - Σ = covariance matrix
            - w^T = transposed weights vector

        This is used by portfolio optimizers to minimize risk.

        Args:
            returns: DataFrame of asset returns
            tickers: List of ticker symbols

        Returns:
            CovarianceMatrixOutput with full covariance matrix
        """
        # Calculate covariance matrix using pandas
        cov_df = returns.cov()

        # Convert to nested dict format
        cov_dict = {}
        for ticker1 in tickers:
            cov_dict[ticker1] = {}
            for ticker2 in tickers:
                cov_dict[ticker1][ticker2] = float(cov_df.loc[ticker1, ticker2])

        # Get calculation date (handle both datetime and date objects)
        calc_date = returns.index[-1]
        if hasattr(calc_date, "date"):
            calc_date = calc_date.date()

        return CovarianceMatrixOutput(
            tickers=tickers,
            calculation_date=calc_date,
            covariance_matrix=cov_dict,
        )

    def _calculate_diversification_score(
        self,
        correlation_matrix: dict[str, dict[str, float]],
    ) -> float:
        """Calculate portfolio diversification score.

        FORMULA:
        Diversification Score = 1 - average_correlation

        EDUCATIONAL NOTE:
        This is a simple but effective measure of diversification.

        INTERPRETATION:
        - 1.0 = Perfect diversification (all correlations = 0)
        - 0.5 = Moderate diversification (average correlation = 0.5)
        - 0.0 = No diversification (all correlations = 1.0, perfectly correlated)

        GUIDELINE FOR YOUR $500K PORTFOLIO:
        - Score > 0.6: Excellent diversification
        - Score 0.4-0.6: Good diversification
        - Score 0.2-0.4: Moderate diversification
        - Score < 0.2: Poor diversification (concentration risk!)

        Args:
            correlation_matrix: Full correlation matrix

        Returns:
            Diversification score between 0 and 1
        """
        # Extract off-diagonal correlations
        tickers = list(correlation_matrix.keys())
        off_diagonal = []

        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i < j:
                    off_diagonal.append(correlation_matrix[ticker1][ticker2])

        if not off_diagonal:
            return 1.0  # Single asset = "perfectly diversified" by definition

        avg_corr = np.mean(off_diagonal)

        # Diversification score = 1 - average correlation
        # Higher score = better diversification
        return float(1.0 - avg_corr)

    def _calculate_rolling_correlations(
        self,
        returns: pd.DataFrame,
        tickers: list[str],
    ) -> list[RollingCorrelationOutput]:
        """Calculate rolling (time-varying) correlations for all pairs.

        EDUCATIONAL NOTE:
        Correlations change over time! This is called "correlation regime shifts."

        COMMON PATTERNS:
        1. **Crisis convergence**: During market crashes, all correlations spike
           toward 1.0 as "everything sells off together"

        2. **Calm divergence**: During stable markets, correlations drift lower
           as individual stock stories dominate

        3. **Sector rotation**: Correlations within sectors rise/fall as
           investors rotate between growth/value, tech/energy, etc.

        WHY THIS MATTERS FOR YOUR $500K:
        - If rolling correlations are rising across your portfolio → RED FLAG
        - Means diversification is disappearing
        - Consider adding uncorrelated assets or hedges

        Args:
            returns: DataFrame of asset returns
            tickers: List of ticker symbols

        Returns:
            List of RollingCorrelationOutput for all pairs
        """
        rolling_outputs = []

        # Calculate for all pairs
        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i < j:  # Only upper triangle (avoid duplicates)
                    # Calculate rolling correlation
                    rolling_corr = (
                        returns[ticker1]
                        .rolling(
                            window=self.config.rolling_window,
                            min_periods=self.config.min_periods,
                        )
                        .corr(returns[ticker2])
                    )

                    # Drop NaN values from beginning
                    rolling_corr = rolling_corr.dropna()

                    if len(rolling_corr) == 0:
                        continue

                    # Extract values (handle both datetime and date index types)
                    dates = [
                        d.date() if hasattr(d, "date") and callable(d.date) else d
                        for d in rolling_corr.index
                    ]
                    correlations = rolling_corr.tolist()
                    current_corr = float(correlations[-1])
                    avg_corr = float(np.mean(correlations))
                    corr_min = float(np.min(correlations))
                    corr_max = float(np.max(correlations))

                    rolling_outputs.append(
                        RollingCorrelationOutput(
                            ticker_1=ticker1,
                            ticker_2=ticker2,
                            dates=dates,
                            correlations=correlations,
                            current_correlation=current_corr,
                            average_correlation=avg_corr,
                            correlation_range=(corr_min, corr_max),
                        )
                    )

        return rolling_outputs


# Convenience function for quick calculations
def calculate_correlation(
    data: PortfolioPriceData,
    config: CorrelationConfig | None = None,
) -> PortfolioCorrelationOutput:
    """Convenience function to calculate correlation with default or custom config.

    EDUCATIONAL NOTE:
    This function provides a simple interface for agents to calculate
    portfolio correlation without needing to instantiate the engine class.

    Args:
        data: PortfolioPriceData with synchronized price series
        config: Optional custom configuration (uses defaults if not provided)

    Returns:
        PortfolioCorrelationOutput with full analysis

    Example:
        >>> from src.models.correlation_inputs import PortfolioPriceData
        >>> from src.analysis.correlation import calculate_correlation
        >>>
        >>> data = PortfolioPriceData(
        ...     tickers=["TSLA", "PLTR", "NVDA"],
        ...     dates=[...],
        ...     prices={"TSLA": [...], "PLTR": [...], "NVDA": [...]}
        ... )
        >>> result = calculate_correlation(data)
        >>> print(f"Diversification Score: {result.diversification_score:.2f}")
        >>> print(f"Average Correlation: {result.correlation_matrix.average_correlation:.2f}")
    """
    if config is None:
        config = CorrelationConfig()

    engine = CorrelationEngine(config)
    return engine.calculate_portfolio_correlation(data)
