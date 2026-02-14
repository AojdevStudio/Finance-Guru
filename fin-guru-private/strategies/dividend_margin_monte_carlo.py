"""Monte Carlo Simulation: Dividend Income + Margin Living Strategy
Finance Guru™ - Integrated Stress Testing

Simulates 28-month journey from $0 → $100k/year passive income
while managing margin debt across 10,000 market scenarios.

Author: Dr. Priya Desai (Quant Analyst)
Date: 2025-10-13
Updated: 2026-01-02 (v3.0 - Full 4-layer portfolio: Growth + Income + Hedge + GOOGL)
"""

import json
from datetime import datetime

import numpy as np
import pandas as pd


class DividendMarginMonteCarlo:
    """Monte Carlo engine for dividend income + margin living strategy"""

    def __init__(self):
        # ========================================
        # PORTFOLIO COMPOSITION (v3.0 - Jan 2026)
        # Full 4-layer structure: Growth + Income + Hedge + GOOGL
        # ========================================

        # Layer 1: Growth Portfolio (NO NEW DEPLOYMENT - just market growth)
        self.layer1_beta = 1.2  # Higher beta (tech-heavy)
        self.layer1_volatility = 0.22  # ~22% annual volatility
        self.layer1_expected_return = 0.18  # 18% annual expected return

        # Layer 2: Income Generation (5 buckets)
        # Total: 94% of deployment ($12,517/month)
        self.bucket_allocations = {
            "jpmorgan_income": 0.27,  # JEPI, JEPQ - stable
            "cef_stable": 0.20,  # CLM, CRF, ECAT - high yield CEFs
            "covered_call_etfs": 0.35,  # QQQI, SPYI, QQQY - moderate
            "yieldmax": 0.10,  # YMAX, AMZY (MSTY PAUSED)
            "drip_v2_cefs": 0.08,  # BDJ, ETY, ETV, BST, UTG
        }

        # Bucket target yields (annual)
        self.bucket_yields = {
            "jpmorgan_income": 0.09,  # 9% (JEPI/JEPQ average)
            "cef_stable": 0.21,  # 21% (CLM/CRF/ECAT average)
            "covered_call_etfs": 0.16,  # 16% (QQQI/SPYI/QQQY average)
            "yieldmax": 0.70,  # 70% (YMAX/AMZY - MSTY excluded)
            "drip_v2_cefs": 0.09,  # 9% (BlackRock/Eaton Vance CEFs)
        }

        # Bucket volatilities (annual, from historical data)
        self.bucket_volatility = {
            "jpmorgan_income": 0.069,  # Low vol - covered calls on SPY
            "cef_stable": 0.150,  # Moderate vol - leveraged CEFs
            "covered_call_etfs": 0.135,  # Moderate vol - tech covered calls
            "yieldmax": 0.450,  # HIGH vol (lower than MSTY alone)
            "drip_v2_cefs": 0.120,  # Low-moderate vol - institutional CEFs
        }

        # Calculate blended target yield
        self.target_yield = sum(
            self.bucket_allocations[b] * self.bucket_yields[b]
            for b in self.bucket_allocations
        )  # Should be ~19.9% blended (updated from docs)

        # Layer 3: Hedge (6% of deployment = $800/month)
        self.hedge_allocation = 0.06
        self.hedge_ticker = "SQQQ"
        self.hedge_leverage = 3.0  # 3x inverse Nasdaq

        # GOOGL Scale-In (diverts from Layer 2)
        self.googl_monthly_diversion = 1000  # $1,000/month to GOOGL
        self.googl_expected_return = 0.15  # 15% annual expected return
        self.googl_volatility = 0.30  # ~30% annual volatility (single stock)

        # Capital deployment (adjusted for diversions)
        self.total_monthly_income = 13317  # Total W2 income
        self.layer2_deployment = 11517  # $11,517 to income (after GOOGL diversion)
        self.layer3_deployment = 800  # $800 to hedge
        self.simulation_months = 28

        # Margin parameters (confidence-based scaling)
        self.margin_schedule = {
            range(1, 7): 4500,  # Months 1-6: Fixed expenses only
            range(7, 13): 6213,  # Months 7-12: Add mortgage (if data supports)
            range(13, 29): 8000,  # Months 13-28: Partial variables (conservative)
        }
        self.margin_rate = 0.11825  # 11.825% annual (updated Fidelity rate)
        self.margin_monthly_rate = self.margin_rate / 12

        # Safety constraints
        self.min_portfolio_margin_ratio = 3.0  # 3:1 minimum
        self.max_margin_balance = 100000
        self.stop_loss_threshold = -0.25  # -25% portfolio drop
        self.business_income_backstop = 22000  # $22k/month safety net

        # Yield degradation assumption (realistic)
        self.yield_degradation_rate = (
            0.15  # 15% decline over 28 months (improved with active mgmt)
        )

        # Active management parameters
        self.active_management = True
        self.yield_recovery_on_rotation = 0.12  # 12% recovery from rotating losers

    def get_margin_draw(self, month: int) -> float:
        """Get margin draw amount for given month"""
        for month_range, amount in self.margin_schedule.items():
            if month in month_range:
                return amount
        return 0

    def calculate_monthly_yield(self, month: int) -> float:
        """Calculate yield for given month with degradation"""
        # Linear degradation from 29.8% to 23.8% over 28 months
        start_yield = self.target_yield
        end_yield = start_yield * (1 - self.yield_degradation_rate)
        degradation_per_month = (start_yield - end_yield) / self.simulation_months
        current_yield = start_yield - (degradation_per_month * (month - 1))

        # Active management: If yield drops > 15%, rotate out losers (recovers 10% of degradation)
        if self.active_management and month > 6:
            yield_decline = (self.target_yield - current_yield) / self.target_yield
            if yield_decline > 0.15:  # More than 15% yield decline
                # Rotate out of underperformers (e.g., MSTY cut distribution)
                recovery = self.target_yield * self.yield_recovery_on_rotation
                current_yield = min(self.target_yield, current_yield + recovery)

        return current_yield

    def simulate_market_returns(self, n_scenarios: int) -> dict:
        """Simulate monthly returns for ALL portfolio layers across N scenarios.

        Returns: Dictionary with arrays for each component
        - layer1_returns: (n_scenarios, simulation_months) - Layer 1 growth portfolio
        - bucket_returns: (n_scenarios, simulation_months, 5) - Layer 2 income buckets
        - googl_returns: (n_scenarios, simulation_months) - GOOGL growth position
        - hedge_returns: (n_scenarios, simulation_months) - Layer 3 hedge position
        - market_returns: (n_scenarios, simulation_months) - Underlying market for reference
        """
        bucket_names = list(self.bucket_allocations.keys())
        n_buckets = len(bucket_names)

        layer1_returns = np.zeros((n_scenarios, self.simulation_months))
        bucket_returns = np.zeros((n_scenarios, self.simulation_months, n_buckets))
        googl_returns = np.zeros((n_scenarios, self.simulation_months))
        hedge_returns = np.zeros((n_scenarios, self.simulation_months))
        market_returns = np.zeros((n_scenarios, self.simulation_months))

        # Market regime probabilities (updated for 2026)
        regime_probs = {
            "bull": 0.35,  # +15% annual, low vol
            "normal": 0.40,  # +8% annual, moderate vol
            "bear": 0.20,  # -15% annual, high vol
            "crisis": 0.05,  # -40% drawdown, extreme vol
        }

        for scenario in range(n_scenarios):
            # Assign market regime for this scenario
            regime = np.random.choice(
                list(regime_probs.keys()), p=list(regime_probs.values())
            )

            # Set regime parameters
            if regime == "bull":
                market_drift = 0.15 / 12  # Monthly drift
                vol_multiplier = 0.8
            elif regime == "normal":
                market_drift = 0.08 / 12
                vol_multiplier = 1.0
            elif regime == "bear":
                market_drift = -0.15 / 12
                vol_multiplier = 1.5
            else:  # crisis
                market_drift = -0.40 / 12
                vol_multiplier = 3.0

            # Generate returns for each month
            for month in range(self.simulation_months):
                # Market return (SPY-like)
                market_vol = 0.16 / np.sqrt(12)  # ~16% annual vol
                market_ret = np.random.normal(market_drift, market_vol * vol_multiplier)
                market_returns[scenario, month] = market_ret

                # Layer 1 returns (growth portfolio with higher beta and vol)
                layer1_vol = self.layer1_volatility * vol_multiplier / np.sqrt(12)
                layer1_drift = self.layer1_expected_return / 12
                # Correlation with market (beta = 1.2)
                correlation = 0.85  # High correlation with market
                idiosyncratic_layer1 = np.random.normal(
                    0, layer1_vol * (1 - correlation)
                )
                layer1_returns[scenario, month] = (
                    (self.layer1_beta * market_ret)
                    + idiosyncratic_layer1
                    + (layer1_drift - market_drift)
                )

                # Layer 2 income bucket returns (correlated with market)
                for i, bucket_name in enumerate(bucket_names):
                    bucket_vol = (
                        self.bucket_volatility[bucket_name]
                        * vol_multiplier
                        / np.sqrt(12)
                    )

                    # YieldMax bucket has fat tails (5% chance of extreme move)
                    if bucket_name == "yieldmax" and np.random.random() < 0.05:
                        bucket_returns[scenario, month, i] = np.random.normal(
                            market_drift * 0.8, bucket_vol * 2.5
                        )
                    else:
                        # Correlation with market (income funds have ~0.7 correlation)
                        correlation = 0.7
                        idiosyncratic = np.random.normal(
                            0, bucket_vol * (1 - correlation)
                        )
                        bucket_returns[scenario, month, i] = (
                            market_ret * correlation + idiosyncratic
                        )

                # GOOGL returns (higher vol, higher expected return)
                googl_vol = self.googl_volatility * vol_multiplier / np.sqrt(12)
                googl_drift = self.googl_expected_return / 12
                googl_returns[scenario, month] = np.random.normal(
                    googl_drift, googl_vol
                )

                # Layer 3: SQQQ returns (3x inverse of market with decay)
                # SQQQ loses value over time due to daily reset (volatility drag)
                vol_drag = 0.02 / 12  # ~2% monthly decay in normal vol
                hedge_returns[scenario, month] = (-self.hedge_leverage * market_ret) - (
                    vol_drag * vol_multiplier
                )

        return {
            "layer1_returns": layer1_returns,
            "bucket_returns": bucket_returns,
            "googl_returns": googl_returns,
            "hedge_returns": hedge_returns,
            "market_returns": market_returns,
        }

    def run_single_scenario(self, scenario_returns: dict, scenario_idx: int) -> dict:
        """Run single 28-month scenario with FULL 4-layer portfolio structure.

        Args:
            scenario_returns: Dictionary with layer1_returns, bucket_returns, googl_returns, hedge_returns, market_returns
            scenario_idx: Index of this scenario in the arrays

        Returns:
            Dictionary with scenario results
        """
        # Extract returns for this scenario
        layer1_returns = scenario_returns["layer1_returns"][scenario_idx]
        bucket_returns = scenario_returns["bucket_returns"][scenario_idx]
        googl_returns = scenario_returns["googl_returns"][scenario_idx]
        hedge_returns = scenario_returns["hedge_returns"][scenario_idx]
        market_returns = scenario_returns["market_returns"][scenario_idx]

        bucket_names = list(self.bucket_allocations.keys())

        # Initialize portfolio components with ACTUAL Jan 2, 2026 values
        layer1_portfolio = 170073  # Layer 1: Growth portfolio (NO new deployment)
        income_portfolio = 61725  # Layer 2: Current dividend portfolio value
        googl_position = 1876  # Starting GOOGL value (6.004 shares @ $312)
        hedge_position = 13199  # Layer 3: Current SQQQ hedge value
        margin_balance = 3222  # Starting margin debt ($3,222 from Jan 2, 2026)

        # Tracking
        total_dividends_collected = 0
        max_drawdown = 0
        peak_total_value = 0
        margin_call_triggered = False
        backstop_used = False
        backstop_amount_used = 0

        # Monthly tracking
        monthly_portfolio = []
        monthly_layer1 = []
        monthly_layer2 = []
        monthly_margin = []
        monthly_dividends = []
        monthly_googl = []
        monthly_hedge = []

        for month in range(1, self.simulation_months + 1):
            # ========================================
            # 1. DEPLOY NEW CAPITAL
            # ========================================
            # Layer 1: NO NEW DEPLOYMENT - just market growth
            # (Layer 1 grows purely from market returns)

            # Layer 2: Income deployment (after GOOGL diversion)
            income_portfolio += self.layer2_deployment  # $11,517/month

            # GOOGL: Monthly addition
            googl_position += self.googl_monthly_diversion  # $1,000/month

            # Layer 3: Hedge deployment
            hedge_position += self.layer3_deployment  # $800/month

            # ========================================
            # 2. APPLY MARKET RETURNS
            # ========================================
            # Apply returns to Layer 1 (growth portfolio)
            if layer1_portfolio > 0:
                layer1_portfolio *= 1 + layer1_returns[month - 1]
                # Floor at $0 (stocks can't go negative)
                layer1_portfolio = max(0, layer1_portfolio)

            # Apply returns to Layer 2 income portfolio (weighted by bucket allocation)
            if income_portfolio > 0:
                weighted_return = sum(
                    self.bucket_allocations[bucket_names[i]]
                    * bucket_returns[month - 1, i]
                    for i in range(len(bucket_names))
                )
                income_portfolio *= 1 + weighted_return
                # Floor at $0 (funds can't go negative)
                income_portfolio = max(0, income_portfolio)

            # Apply returns to GOOGL
            if googl_position > 0:
                googl_position *= 1 + googl_returns[month - 1]
                # Floor at $0 (stocks can't go negative)
                googl_position = max(0, googl_position)

            # Apply returns to Layer 3 hedge (SQQQ)
            if hedge_position > 0:
                hedge_position *= 1 + hedge_returns[month - 1]
                # Floor at $0 (can't go negative)
                hedge_position = max(0, hedge_position)

            # ========================================
            # 3. CALCULATE TOTAL PORTFOLIO VALUE
            # ========================================
            # CRITICAL: Margin ratio is calculated based on TOTAL portfolio value (all layers)
            total_portfolio_value = (
                layer1_portfolio + income_portfolio + googl_position + hedge_position
            )

            # ========================================
            # 4. CALCULATE DIVIDEND INCOME
            # ========================================
            # Only income portfolio generates dividends
            current_yield = self.calculate_monthly_yield(month)
            monthly_dividend = income_portfolio * (current_yield / 12)
            total_dividends_collected += monthly_dividend

            # ========================================
            # 5. MARGIN DRAW AND DEBT MANAGEMENT
            # ========================================
            margin_draw = self.get_margin_draw(month)

            if monthly_dividend < margin_draw:
                # Draw from margin to cover shortfall
                shortfall = margin_draw - monthly_dividend
                margin_balance += shortfall
            else:
                # Dividends exceed expenses - pay down margin
                excess_dividend = monthly_dividend - margin_draw
                margin_balance = max(0, margin_balance - excess_dividend)

            # ========================================
            # 6. APPLY MARGIN INTEREST
            # ========================================
            if margin_balance > 0:
                margin_interest = margin_balance * self.margin_monthly_rate
                margin_balance += margin_interest

            # ========================================
            # 7. CHECK SAFETY THRESHOLDS
            # ========================================
            # Calculate portfolio-to-margin ratio
            if margin_balance > 0:
                portfolio_margin_ratio = total_portfolio_value / margin_balance

                # Margin call check (ratio < 3:1)
                if portfolio_margin_ratio < self.min_portfolio_margin_ratio:
                    margin_call_triggered = True
                    backstop_used = True
                    # Use business income to inject capital
                    injection = min(self.business_income_backstop, margin_balance)
                    margin_balance -= injection
                    backstop_amount_used += injection

            # ========================================
            # 8. DRAWDOWN TRACKING
            # ========================================
            if peak_total_value > 0:
                current_drawdown = (
                    total_portfolio_value - peak_total_value
                ) / peak_total_value
                if current_drawdown < max_drawdown:
                    max_drawdown = current_drawdown

                # Hedge benefit: In severe drawdowns, SQQQ gains offset losses
                if current_drawdown < -0.15:  # More than 15% drawdown
                    # This is where SQQQ provides value (already captured in returns)
                    pass

            peak_total_value = max(peak_total_value, total_portfolio_value)

            # ========================================
            # 9. TRACK MONTHLY VALUES
            # ========================================
            monthly_portfolio.append(total_portfolio_value)
            monthly_layer1.append(layer1_portfolio)
            monthly_layer2.append(income_portfolio)
            monthly_margin.append(margin_balance)
            monthly_dividends.append(monthly_dividend)
            monthly_googl.append(googl_position)
            monthly_hedge.append(hedge_position)

        # ========================================
        # CALCULATE FINAL METRICS
        # ========================================
        final_layer1_value = layer1_portfolio
        final_income_portfolio = income_portfolio
        final_googl_value = googl_position
        final_hedge_value = hedge_position
        final_portfolio_value = (
            layer1_portfolio + income_portfolio + googl_position + hedge_position
        )
        final_margin_balance = margin_balance
        final_annual_dividend = monthly_dividends[-1] * 12

        # Calculate final margin ratio (based on TOTAL portfolio)
        final_margin_ratio = (
            final_portfolio_value / final_margin_balance
            if final_margin_balance > 0
            else float("inf")
        )

        # Break-even month (dividends cover margin draw)
        break_even_month = None
        for i, div in enumerate(monthly_dividends):
            margin_draw_for_month = self.get_margin_draw(i + 1)
            if div >= margin_draw_for_month:
                break_even_month = i + 1
                break

        # Margin payoff month
        margin_payoff_month = None
        for i, margin in enumerate(monthly_margin):
            if margin == 0 and i > 0:
                margin_payoff_month = i + 1
                break

        return {
            "final_portfolio_value": final_portfolio_value,
            "final_layer1_value": final_layer1_value,
            "final_income_portfolio": final_income_portfolio,
            "final_googl_value": final_googl_value,
            "final_hedge_value": final_hedge_value,
            "final_margin_balance": final_margin_balance,
            "final_margin_ratio": final_margin_ratio,
            "final_annual_dividend": final_annual_dividend,
            "max_drawdown": max_drawdown,
            "margin_call_triggered": margin_call_triggered,
            "backstop_used": backstop_used,
            "backstop_amount_used": backstop_amount_used,
            "break_even_month": break_even_month,
            "margin_payoff_month": margin_payoff_month,
            "total_dividends_collected": total_dividends_collected,
            "monthly_portfolio": monthly_portfolio,
            "monthly_layer1": monthly_layer1,
            "monthly_layer2": monthly_layer2,
            "monthly_margin": monthly_margin,
            "monthly_dividends": monthly_dividends,
            "monthly_googl": monthly_googl,
            "monthly_hedge": monthly_hedge,
        }

    def run_simulation(self, n_scenarios: int = 10000) -> pd.DataFrame:
        """Run full Monte Carlo simulation with FULL 4-layer portfolio structure.

        Args:
            n_scenarios: Number of scenarios to simulate (default 10,000)

        Returns:
            DataFrame with results for all scenarios
        """
        print(f"\n{'=' * 60}")
        print("MONTE CARLO SIMULATION v3.0")
        print("Full 4-Layer Portfolio: Growth + Income + Hedge + GOOGL")
        print(f"{'=' * 60}")

        print("\nStarting Portfolio (Jan 2, 2026):")
        print("  Layer 1 (Growth): $170,073 - NO new deployment")
        print(
            f"  Layer 2 (Income): $61,725 - ${self.layer2_deployment:,.0f}/month deployment"
        )
        print(
            f"  Layer 3 (Hedge): $13,199 - ${self.layer3_deployment:,.0f}/month deployment"
        )
        print(
            f"  GOOGL Position: $1,876 - ${self.googl_monthly_diversion:,.0f}/month deployment"
        )
        print("  Starting Margin: $3,222")

        print("\nConfiguration:")
        print(f"  Layer 2 Blended Yield: {self.target_yield:.1%}")
        print(f"  Margin Rate: {self.margin_rate:.3%}")
        print(f"  Total Monthly W2: ${self.total_monthly_income:,.0f}")

        print(f"\nGenerating {n_scenarios:,} market scenarios...")
        scenario_returns = self.simulate_market_returns(n_scenarios)

        print(f"Running {n_scenarios:,} 28-month simulations...")
        results = []

        for i in range(n_scenarios):
            if (i + 1) % 2000 == 0:
                print(f"  Completed {i + 1:,} scenarios...")

            scenario_result = self.run_single_scenario(scenario_returns, i)
            results.append(scenario_result)

        print("\nSimulations complete. Analyzing results...")
        return pd.DataFrame(results)


def analyze_results(df: pd.DataFrame) -> dict:
    """Analyze simulation results and generate summary statistics for v3.0 model"""
    # Success metrics
    success_100k = (df["final_annual_dividend"] >= 100000).sum() / len(df)
    success_75k = (df["final_annual_dividend"] >= 75000).sum() / len(df)
    success_50k = (df["final_annual_dividend"] >= 50000).sum() / len(df)
    success_margin_free = (df["final_margin_balance"] == 0).sum() / len(df)
    margin_call_rate = df["margin_call_triggered"].sum() / len(df)
    backstop_usage_rate = df["backstop_used"].sum() / len(df)

    # Average backstop amount when used
    backstop_amounts = df[df["backstop_used"]]["backstop_amount_used"]
    avg_backstop = backstop_amounts.mean() if len(backstop_amounts) > 0 else 0

    # Portfolio value statistics (TOTAL - all layers)
    portfolio_stats = {
        "median": df["final_portfolio_value"].median(),
        "mean": df["final_portfolio_value"].mean(),
        "p5": df["final_portfolio_value"].quantile(0.05),
        "p25": df["final_portfolio_value"].quantile(0.25),
        "p75": df["final_portfolio_value"].quantile(0.75),
        "p95": df["final_portfolio_value"].quantile(0.95),
        "min": df["final_portfolio_value"].min(),
        "max": df["final_portfolio_value"].max(),
    }

    # Layer 1 statistics (Growth portfolio)
    layer1_stats = {
        "median": df["final_layer1_value"].median(),
        "mean": df["final_layer1_value"].mean(),
        "p5": df["final_layer1_value"].quantile(0.05),
        "p95": df["final_layer1_value"].quantile(0.95),
    }

    # Layer 2 statistics (Income portfolio)
    income_stats = {
        "median": df["final_income_portfolio"].median(),
        "mean": df["final_income_portfolio"].mean(),
        "p5": df["final_income_portfolio"].quantile(0.05),
        "p95": df["final_income_portfolio"].quantile(0.95),
    }

    # GOOGL position statistics
    googl_stats = {
        "median": df["final_googl_value"].median(),
        "mean": df["final_googl_value"].mean(),
        "p5": df["final_googl_value"].quantile(0.05),
        "p95": df["final_googl_value"].quantile(0.95),
    }

    # Layer 3 statistics (Hedge position)
    hedge_stats = {
        "median": df["final_hedge_value"].median(),
        "mean": df["final_hedge_value"].mean(),
        "p5": df["final_hedge_value"].quantile(0.05),
        "p95": df["final_hedge_value"].quantile(0.95),
    }

    # Dividend income statistics
    dividend_stats = {
        "median": df["final_annual_dividend"].median(),
        "mean": df["final_annual_dividend"].mean(),
        "p5": df["final_annual_dividend"].quantile(0.05),
        "p25": df["final_annual_dividend"].quantile(0.25),
        "p75": df["final_annual_dividend"].quantile(0.75),
        "p95": df["final_annual_dividend"].quantile(0.95),
        "min": df["final_annual_dividend"].min(),
        "max": df["final_annual_dividend"].max(),
    }

    # Margin balance statistics
    margin_stats = {
        "median": df["final_margin_balance"].median(),
        "mean": df["final_margin_balance"].mean(),
        "p5": df["final_margin_balance"].quantile(0.05),
        "p95": df["final_margin_balance"].quantile(0.95),
        "max": df["final_margin_balance"].max(),
    }

    # Margin ratio statistics (NEW - based on total portfolio)
    margin_ratio_stats = {
        "median": df["final_margin_ratio"].median(),
        "mean": df["final_margin_ratio"].mean(),
        "p5": df["final_margin_ratio"].quantile(0.05),
        "p95": df["final_margin_ratio"].quantile(0.95),
        "min": df["final_margin_ratio"].min(),
    }

    # Drawdown statistics
    drawdown_stats = {
        "median": df["max_drawdown"].median(),
        "mean": df["max_drawdown"].mean(),
        "p5": df["max_drawdown"].quantile(0.05),
        "p95": df["max_drawdown"].quantile(0.95),
        "worst": df["max_drawdown"].min(),
    }

    # Break-even timing statistics
    break_even_data = df[df["break_even_month"].notna()]["break_even_month"]
    break_even_stats = {
        "probability": len(break_even_data) / len(df),
        "median": break_even_data.median() if len(break_even_data) > 0 else None,
        "mean": break_even_data.mean() if len(break_even_data) > 0 else None,
        "p5": break_even_data.quantile(0.05) if len(break_even_data) > 0 else None,
        "p95": break_even_data.quantile(0.95) if len(break_even_data) > 0 else None,
    }

    # Margin payoff timing statistics
    payoff_data = df[df["margin_payoff_month"].notna()]["margin_payoff_month"]
    payoff_stats = {
        "probability": len(payoff_data) / len(df),
        "median": payoff_data.median() if len(payoff_data) > 0 else None,
        "mean": payoff_data.mean() if len(payoff_data) > 0 else None,
        "p5": payoff_data.quantile(0.05) if len(payoff_data) > 0 else None,
        "p95": payoff_data.quantile(0.95) if len(payoff_data) > 0 else None,
    }

    return {
        "simulation_date": datetime.now().strftime("%Y-%m-%d"),
        "model_version": "3.0",
        "n_scenarios": len(df),
        "success_metrics": {
            "probability_100k_income": success_100k,
            "probability_75k_income": success_75k,
            "probability_50k_income": success_50k,
            "probability_margin_free": success_margin_free,
            "margin_call_rate": margin_call_rate,
            "backstop_usage_rate": backstop_usage_rate,
            "avg_backstop_amount": avg_backstop,
        },
        "portfolio_value": portfolio_stats,
        "layer1_growth": layer1_stats,
        "income_portfolio": income_stats,
        "googl_position": googl_stats,
        "hedge_position": hedge_stats,
        "dividend_income": dividend_stats,
        "margin_balance": margin_stats,
        "margin_ratio": margin_ratio_stats,
        "drawdown": drawdown_stats,
        "break_even_timing": break_even_stats,
        "margin_payoff_timing": payoff_stats,
    }


if __name__ == "__main__":
    # Initialize Monte Carlo engine
    mc = DividendMarginMonteCarlo()

    # Run simulation
    results_df = mc.run_simulation(n_scenarios=10000)

    # Analyze results
    summary = analyze_results(results_df)

    # Print summary
    print("\n" + "=" * 80)
    print("MONTE CARLO SIMULATION RESULTS v3.0")
    print("Full 4-Layer Portfolio Strategy")
    print("=" * 80)
    print(f"\nSimulation Date: {summary['simulation_date']}")
    print(f"Model Version: {summary['model_version']}")
    print(f"Scenarios Analyzed: {summary['n_scenarios']:,}")

    print("\n" + "-" * 40)
    print("SUCCESS METRICS")
    print("-" * 40)
    print(
        f"Probability of $100k+ Annual Income: {summary['success_metrics']['probability_100k_income']:.1%}"
    )
    print(
        f"Probability of $75k+ Annual Income:  {summary['success_metrics']['probability_75k_income']:.1%}"
    )
    print(
        f"Probability of $50k+ Annual Income:  {summary['success_metrics']['probability_50k_income']:.1%}"
    )
    print(
        f"Probability of Margin-Free by Month 28: {summary['success_metrics']['probability_margin_free']:.1%}"
    )
    print(f"Margin Call Rate: {summary['success_metrics']['margin_call_rate']:.1%}")
    print(
        f"Business Income Backstop Used: {summary['success_metrics']['backstop_usage_rate']:.1%}"
    )
    if summary["success_metrics"]["avg_backstop_amount"] > 0:
        print(
            f"Average Backstop Amount: ${summary['success_metrics']['avg_backstop_amount']:,.0f}"
        )

    print("\n" + "-" * 40)
    print("TOTAL PORTFOLIO VALUE AT MONTH 28")
    print("-" * 40)
    print(f"Median: ${summary['portfolio_value']['median']:,.0f}")
    print(f"Mean: ${summary['portfolio_value']['mean']:,.0f}")
    print(f"5th Percentile (Bear): ${summary['portfolio_value']['p5']:,.0f}")
    print(f"95th Percentile (Bull): ${summary['portfolio_value']['p95']:,.0f}")

    print("\n" + "-" * 40)
    print("PORTFOLIO COMPOSITION AT MONTH 28 (Median Values)")
    print("-" * 40)
    print(f"Layer 1 (Growth):      ${summary['layer1_growth']['median']:,.0f}")
    print(f"Layer 2 (Income):      ${summary['income_portfolio']['median']:,.0f}")
    print(f"GOOGL Position:        ${summary['googl_position']['median']:,.0f}")
    print(f"Layer 3 (Hedge/SQQQ):  ${summary['hedge_position']['median']:,.0f}")

    print("\n" + "-" * 40)
    print("ANNUAL DIVIDEND INCOME AT MONTH 28")
    print("-" * 40)
    print(f"Median: ${summary['dividend_income']['median']:,.0f}")
    print(f"Mean: ${summary['dividend_income']['mean']:,.0f}")
    print(f"5th Percentile: ${summary['dividend_income']['p5']:,.0f}")
    print(f"25th Percentile: ${summary['dividend_income']['p25']:,.0f}")
    print(f"75th Percentile: ${summary['dividend_income']['p75']:,.0f}")
    print(f"95th Percentile: ${summary['dividend_income']['p95']:,.0f}")

    print("\n" + "-" * 40)
    print("MARGIN BALANCE AT MONTH 28")
    print("-" * 40)
    print(f"Median: ${summary['margin_balance']['median']:,.0f}")
    print(f"Mean: ${summary['margin_balance']['mean']:,.0f}")
    print(f"Maximum: ${summary['margin_balance']['max']:,.0f}")

    print("\n" + "-" * 40)
    print("MARGIN RATIO AT MONTH 28 (Total Portfolio / Margin)")
    print("-" * 40)
    print(f"Median: {summary['margin_ratio']['median']:.2f}:1")
    print(f"Mean: {summary['margin_ratio']['mean']:.2f}:1")
    print(f"5th Percentile (Worst): {summary['margin_ratio']['p5']:.2f}:1")
    print(f"95th Percentile (Best): {summary['margin_ratio']['p95']:.2f}:1")
    print(f"Minimum Ratio: {summary['margin_ratio']['min']:.2f}:1")
    print("NOTE: Fidelity requires 3:1 minimum for margin maintenance")

    print("\n" + "-" * 40)
    print("MAXIMUM DRAWDOWN")
    print("-" * 40)
    print(f"Median: {summary['drawdown']['median']:.1%}")
    print(f"95th Percentile: {summary['drawdown']['p95']:.1%}")
    print(f"Worst Case: {summary['drawdown']['worst']:.1%}")

    if summary["break_even_timing"]["probability"] > 0:
        print("\n" + "-" * 40)
        print("BREAK-EVEN TIMING")
        print("-" * 40)
        print(
            f"Probability of reaching break-even: {summary['break_even_timing']['probability']:.1%}"
        )
        if summary["break_even_timing"]["median"]:
            print(f"Median: Month {summary['break_even_timing']['median']:.0f}")
            print(
                f"5th-95th Percentile: Month {summary['break_even_timing']['p5']:.0f} - {summary['break_even_timing']['p95']:.0f}"
            )

    if summary["margin_payoff_timing"]["probability"] > 0:
        print("\n" + "-" * 40)
        print("MARGIN PAYOFF TIMING")
        print("-" * 40)
        print(
            f"Probability of paying off margin: {summary['margin_payoff_timing']['probability']:.1%}"
        )
        if summary["margin_payoff_timing"]["median"]:
            print(f"Median: Month {summary['margin_payoff_timing']['median']:.0f}")
            print(
                f"5th-95th Percentile: Month {summary['margin_payoff_timing']['p5']:.0f} - {summary['margin_payoff_timing']['p95']:.0f}"
            )

    print("\n" + "=" * 80)
    print("DISCLAIMER: This simulation is for educational purposes only.")
    print("Past performance does not guarantee future results.")
    print("Consult a licensed financial advisor before investing.")
    print("=" * 80)

    # Save results
    output_path = "fin-guru-private/fin-guru/analysis/monte-carlo-v3-2026-01-02.json"
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nDetailed results saved to: {output_path}")

    # Save full dataset (exclude monthly arrays for CSV)
    csv_columns = [
        "final_portfolio_value",
        "final_layer1_value",
        "final_income_portfolio",
        "final_googl_value",
        "final_hedge_value",
        "final_margin_balance",
        "final_margin_ratio",
        "final_annual_dividend",
        "max_drawdown",
        "margin_call_triggered",
        "backstop_used",
        "backstop_amount_used",
        "break_even_month",
        "margin_payoff_month",
        "total_dividends_collected",
    ]
    csv_path = (
        "fin-guru-private/fin-guru/analysis/monte-carlo-v3-full-results-2026-01-02.csv"
    )
    results_df[csv_columns].to_csv(csv_path, index=False)
    print(f"Full scenario data saved to: {csv_path}")
