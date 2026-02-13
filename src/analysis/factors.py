"""Factor Analysis Engine for Finance Guru™.

This module implements Fama-French factor models for return decomposition.
All calculations follow academic finance methodologies.

ARCHITECTURE NOTE:
This is Layer 2 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (factors_inputs.py)
    Layer 2: Calculator Classes (THIS FILE) - Business logic
    Layer 3: CLI Interface - Agent integration

EDUCATIONAL CONTEXT:
Factor models explain asset returns through systematic risk factors:

CAPM (1-Factor):
    Return = alpha + beta_market * market_return + error

Fama-French 3-Factor:
    Return = alpha + beta_market * market + beta_size * SMB + beta_value * HML + error

Carhart 4-Factor:
    Return = alpha + beta_market * market + beta_size * SMB + beta_value * HML + beta_mom * MOM + error

WHERE:
- alpha = Return not explained by factors (skill or luck)
- beta_* = Sensitivity to each factor
- SMB (Small Minus Big) = Size factor (small-cap minus large-cap)
- HML (High Minus Low) = Value factor (high book/market minus low)
- MOM (Momentum) = Past winners minus past losers

WHY FACTOR MODELS MATTER:
1. Attribution: "My 20% return = 15% from market + 3% from size + 2% alpha"
2. Risk Management: Understand factor concentrations
3. Performance Evaluation: Is alpha statistically significant?
4. Portfolio Construction: Target specific factor exposures

Author: Finance Guru™ Development Team
Created: 2025-10-13
"""

from datetime import date

import numpy as np
from sklearn.linear_model import LinearRegression

from src.models.factors_inputs import (
    AttributionOutput,
    FactorAnalysisOutput,
    FactorDataInput,
    FactorExposureOutput,
)


class FactorAnalyzer:
    """Factor analysis engine for Fama-French models.

    WHAT: Decomposes returns into systematic factor exposures
    WHY: Understand what drives performance (skill vs exposure)
    HOW: Linear regression of asset returns on factor returns

    USAGE EXAMPLE:
        # Create input data
        factor_data = FactorDataInput(
            ticker="TSLA",
            asset_returns=asset_rets,
            market_returns=mkt_rets,
            smb_returns=smb_rets,
            hml_returns=hml_rets,
            mom_returns=mom_rets
        )

        # Run analysis
        analyzer = FactorAnalyzer()
        results = analyzer.analyze(factor_data)

        # Check alpha significance
        if results.exposure.alpha_tstat > 2.0:
            print(f"Significant alpha: {results.exposure.alpha:.2%}")
    """

    def analyze(self, data: FactorDataInput) -> FactorAnalysisOutput:
        """Perform complete factor analysis.

        Args:
            data: Validated factor data (Pydantic model)

        Returns:
            FactorAnalysisOutput: Exposure and attribution results

        EDUCATIONAL NOTE:
        This method:
        1. Converts returns to excess returns (subtract risk-free rate)
        2. Runs regression to get factor betas
        3. Calculates return attribution
        4. Generates summary and recommendations
        """
        # Calculate excess returns
        daily_rf = data.risk_free_rate / 252
        excess_asset = np.array(data.asset_returns) - daily_rf
        excess_market = np.array(data.market_returns) - daily_rf

        # Determine model type and run regression
        exposure = self._estimate_exposures(
            excess_asset=excess_asset,
            excess_market=excess_market,
            smb=np.array(data.smb_returns) if data.smb_returns else None,
            hml=np.array(data.hml_returns) if data.hml_returns else None,
            mom=np.array(data.mom_returns) if data.mom_returns else None,
            ticker=data.ticker,
        )

        # Calculate attribution
        attribution = self._calculate_attribution(
            exposure=exposure,
            market_returns=np.array(data.market_returns),
            smb_returns=np.array(data.smb_returns) if data.smb_returns else None,
            hml_returns=np.array(data.hml_returns) if data.hml_returns else None,
            mom_returns=np.array(data.mom_returns) if data.mom_returns else None,
            asset_returns=np.array(data.asset_returns),
            ticker=data.ticker,
        )

        # Generate summary and recommendations
        summary = self._generate_summary(exposure, attribution)
        recommendations = self._generate_recommendations(exposure, attribution)

        return FactorAnalysisOutput(
            exposure=exposure,
            attribution=attribution,
            summary=summary,
            recommendations=recommendations,
        )

    def _estimate_exposures(
        self,
        excess_asset: np.ndarray,
        excess_market: np.ndarray,
        smb: np.ndarray | None,
        hml: np.ndarray | None,
        mom: np.ndarray | None,
        ticker: str,
    ) -> FactorExposureOutput:
        """Estimate factor exposures using OLS regression.

        WHAT: Run regression of asset returns on factor returns
        WHY: Betas tell us factor sensitivities
        HOW: Ordinary Least Squares (OLS) regression

        FORMULA:
            Y = alpha + beta_1 * X_1 + beta_2 * X_2 + ... + error

        EDUCATIONAL NOTE:
        OLS finds the "best fit line" that minimizes squared errors.
        The slope coefficients are our factor betas.
        The intercept is alpha (excess return not explained by factors).
        """
        # Build factor matrix X
        factors = [excess_market]
        factor_names = ["market"]

        if smb is not None:
            factors.append(smb)
            factor_names.append("smb")

        if hml is not None:
            factors.append(hml)
            factor_names.append("hml")

        if mom is not None:
            factors.append(mom)
            factor_names.append("mom")

        X = np.column_stack(factors)
        y = excess_asset

        # Run OLS regression
        model = LinearRegression()
        model.fit(X, y)

        # Extract coefficients
        alpha_daily = model.intercept_
        betas = model.coef_

        # Annualize alpha
        alpha_annual = alpha_daily * 252

        # Calculate R-squared
        y_pred = model.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        # Calculate standard errors and t-statistics
        n = len(y)
        k = X.shape[1]
        residuals = y - y_pred
        mse = np.sum(residuals**2) / (n - k - 1)

        # Standard error of alpha
        X_with_intercept = np.column_stack([np.ones(n), X])
        var_coef = mse * np.linalg.inv(X_with_intercept.T @ X_with_intercept).diagonal()
        se_alpha = np.sqrt(var_coef[0]) * np.sqrt(252)  # Annualize
        se_betas = np.sqrt(var_coef[1:])

        # T-statistics
        alpha_tstat = alpha_annual / se_alpha if se_alpha > 0 else 0
        beta_tstats = betas / se_betas

        # Extract individual betas
        market_beta = float(betas[0])
        market_beta_tstat = float(beta_tstats[0])

        size_beta = (
            float(betas[1]) if len(betas) > 1 and "smb" in factor_names else None
        )
        value_beta = (
            float(betas[2]) if len(betas) > 2 and "hml" in factor_names else None
        )
        momentum_beta = (
            float(betas[3]) if len(betas) > 3 and "mom" in factor_names else None
        )

        return FactorExposureOutput(
            ticker=ticker,
            analysis_date=date.today(),
            market_beta=market_beta,
            size_beta=size_beta,
            value_beta=value_beta,
            momentum_beta=momentum_beta,
            alpha=float(alpha_annual),
            r_squared=float(r_squared),
            alpha_tstat=float(alpha_tstat),
            market_beta_tstat=market_beta_tstat,
        )

    def _calculate_attribution(
        self,
        exposure: FactorExposureOutput,
        market_returns: np.ndarray,
        smb_returns: np.ndarray | None,
        hml_returns: np.ndarray | None,
        mom_returns: np.ndarray | None,
        asset_returns: np.ndarray,
        ticker: str,
    ) -> AttributionOutput:
        """Calculate return attribution by factor.

        WHAT: Decompose total return into factor contributions
        WHY: Shows where returns came from
        HOW: Multiply factor beta by factor return

        FORMULA:
            Factor_Contribution = beta_factor * mean(factor_returns) * 252

        EDUCATIONAL NOTE:
        Attribution answers: "My 20% return came from..."
        - 15% market exposure (high beta)
        - 2% size tilt (positive SMB beta)
        - 1% value tilt (positive HML beta)
        - 2% alpha (skill or luck)
        """
        # Annualize returns
        total_return = float(asset_returns.mean() * 252)
        market_return_annual = float(market_returns.mean() * 252)

        # Market attribution
        market_attribution = exposure.market_beta * market_return_annual

        # Size attribution
        size_attribution = None
        if exposure.size_beta is not None and smb_returns is not None:
            smb_return_annual = float(smb_returns.mean() * 252)
            size_attribution = exposure.size_beta * smb_return_annual

        # Value attribution
        value_attribution = None
        if exposure.value_beta is not None and hml_returns is not None:
            hml_return_annual = float(hml_returns.mean() * 252)
            value_attribution = exposure.value_beta * hml_return_annual

        # Momentum attribution
        momentum_attribution = None
        if exposure.momentum_beta is not None and mom_returns is not None:
            mom_return_annual = float(mom_returns.mean() * 252)
            momentum_attribution = exposure.momentum_beta * mom_return_annual

        # Alpha attribution
        alpha_attribution = exposure.alpha

        # Residual (unexplained)
        explained = market_attribution
        if size_attribution:
            explained += size_attribution
        if value_attribution:
            explained += value_attribution
        if momentum_attribution:
            explained += momentum_attribution
        explained += alpha_attribution

        residual = total_return - explained

        # Calculate importance percentages
        # NOTE: We cap at 1.0 (100%) because offsetting factors can produce
        # values > 100%. For example: market +150%, other factors -50% = 100% total.
        # In this case, market "importance" would be 1.5 mathematically, but we
        # cap it at 1.0 for display purposes (market dominated the return).
        if total_return != 0:
            market_importance = min(abs(market_attribution / total_return), 1.0)
            alpha_importance = min(abs(alpha_attribution / total_return), 1.0)
        else:
            market_importance = 0.0
            alpha_importance = 0.0

        return AttributionOutput(
            ticker=ticker,
            analysis_date=date.today(),
            total_return=total_return,
            market_attribution=float(market_attribution),
            size_attribution=float(size_attribution)
            if size_attribution is not None
            else None,
            value_attribution=float(value_attribution)
            if value_attribution is not None
            else None,
            momentum_attribution=float(momentum_attribution)
            if momentum_attribution is not None
            else None,
            alpha_attribution=float(alpha_attribution),
            residual=float(residual),
            market_importance=float(market_importance),
            alpha_importance=float(alpha_importance),
        )

    def _generate_summary(
        self, exposure: FactorExposureOutput, attribution: AttributionOutput
    ) -> str:
        """Generate human-readable summary."""
        lines = []
        lines.append(f"Factor Analysis for {exposure.ticker}:")
        lines.append(f"- Model explains {exposure.r_squared:.1%} of variance")
        lines.append(
            f"- Market beta: {exposure.market_beta:.2f} (t-stat: {exposure.market_beta_tstat:.2f})"
        )

        if exposure.alpha_tstat > 2.0:
            lines.append(f"- Alpha: {exposure.alpha:.1%} (statistically significant!)")
        else:
            lines.append(
                f"- Alpha: {exposure.alpha:.1%} (not statistically significant)"
            )

        lines.append(f"- Total return: {attribution.total_return:.1%} annualized")
        lines.append(f"  ∟ {attribution.market_importance:.0%} from market exposure")
        lines.append(f"  ∟ {attribution.alpha_importance:.0%} from alpha")

        return "\n".join(lines)

    def _generate_recommendations(
        self, exposure: FactorExposureOutput, attribution: AttributionOutput
    ) -> list[str]:
        """Generate actionable recommendations."""
        recs = []

        # Beta interpretation
        if exposure.market_beta > 1.5:
            recs.append(
                "High market beta (>1.5) suggests aggressive positioning - consider hedging in downturns"
            )
        elif exposure.market_beta < 0.5:
            recs.append(
                "Low market beta (<0.5) suggests defensive positioning - suitable for risk-averse investors"
            )

        # Alpha significance
        if exposure.alpha_tstat > 2.0:
            recs.append(
                f"Significant positive alpha ({exposure.alpha:.1%}) - strategy shows skill beyond factor exposure"
            )
        elif exposure.alpha_tstat < -2.0:
            recs.append(
                f"Significant negative alpha ({exposure.alpha:.1%}) - underperforming risk-adjusted expectations"
            )

        # R-squared interpretation
        if exposure.r_squared < 0.30:
            recs.append(
                "Low R² (<30%) suggests returns are driven by idiosyncratic factors, not systematic ones"
            )
        elif exposure.r_squared > 0.80:
            recs.append(
                "High R² (>80%) suggests returns closely track factor exposures - limited diversification"
            )

        # Factor tilts
        if exposure.size_beta and exposure.size_beta > 0.5:
            recs.append(
                "Strong small-cap tilt detected - adds size premium but increases volatility"
            )
        if exposure.value_beta and exposure.value_beta < -0.5:
            recs.append("Strong growth tilt detected - reduces value premium exposure")

        return recs


# Convenience function
def analyze_factors(
    ticker: str,
    asset_returns: list[float],
    market_returns: list[float],
    smb_returns: list[float] | None = None,
    hml_returns: list[float] | None = None,
    mom_returns: list[float] | None = None,
    risk_free_rate: float = 0.045,
) -> FactorAnalysisOutput:
    """Convenience function for factor analysis.

    Args:
        ticker: Asset ticker symbol
        asset_returns: List of asset daily returns
        market_returns: List of market daily returns
        smb_returns: Optional size factor returns
        hml_returns: Optional value factor returns
        mom_returns: Optional momentum factor returns
        risk_free_rate: Annual risk-free rate

    Returns:
        FactorAnalysisOutput with exposure and attribution

    Example:
        results = analyze_factors(
            ticker="TSLA",
            asset_returns=[0.02, -0.01, 0.03, ...],
            market_returns=[0.01, -0.005, 0.015, ...],
            risk_free_rate=0.045
        )
    """
    # Create input model
    factor_data = FactorDataInput(
        ticker=ticker,
        asset_returns=asset_returns,
        market_returns=market_returns,
        smb_returns=smb_returns,
        hml_returns=hml_returns,
        mom_returns=mom_returns,
        risk_free_rate=risk_free_rate,
    )

    # Analyze
    analyzer = FactorAnalyzer()
    return analyzer.analyze(factor_data)


# Type exports
__all__ = [
    "FactorAnalyzer",
    "analyze_factors",
]
