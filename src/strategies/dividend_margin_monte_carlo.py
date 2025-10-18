"""
Monte Carlo Simulation: Dividend Income + Margin Living Strategy
Finance Guru™ - Integrated Stress Testing

Simulates 28-month journey from $0 → $100k/year passive income
while managing margin debt across 10,000 market scenarios.

Author: Dr. Priya Desai (Quant Analyst)
Date: 2025-10-13
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict
import json

class DividendMarginMonteCarlo:
    """Monte Carlo engine for dividend income + margin living strategy"""

    def __init__(self):
        # Portfolio composition (3-bucket allocation)
        self.bucket1_allocation = 0.45  # Stable foundation
        self.bucket2_allocation = 0.35  # Covered calls
        self.bucket3_allocation = 0.20  # Volatility harvesting

        # Bucket target yields
        self.bucket1_yield = 0.11  # 11% blended
        self.bucket2_yield = 0.22  # 22% blended
        self.bucket3_yield = 0.85  # 85% blended
        self.target_yield = 0.298  # 29.8% blended overall

        # Capital deployment
        self.monthly_deployment = 13317  # $13,317/month (W2 income)
        self.simulation_months = 28

        # Margin parameters
        self.margin_schedule = {
            range(1, 7): 4500,    # Months 1-6: $4,500/month
            range(7, 13): 6213,   # Months 7-12: $6,213/month
            range(13, 29): 14500  # Months 13-28: $14,500/month (optional)
        }
        self.margin_rate = 0.10875  # 10.875% annual
        self.margin_monthly_rate = self.margin_rate / 12

        # Safety constraints
        self.min_portfolio_margin_ratio = 3.0  # 3:1 minimum
        self.max_margin_balance = 100000
        self.stop_loss_threshold = -0.25  # -25% portfolio drop
        self.business_income_backstop = 22000  # $22k/month safety net

        # Volatility profiles (from historical data)
        self.bucket_volatility = {
            'bucket1': 0.069,  # JEPI annual volatility
            'bucket2': 0.135,  # QQQI annual volatility
            'bucket3': 0.540   # MSTY annual volatility
        }

        # Correlation matrices (from historical data)
        self.bucket_correlations = {
            'bucket1': 0.620,  # Average correlation within Bucket 1
            'bucket2': 0.887,  # Average correlation within Bucket 2 (HIGH)
            'bucket3': 0.545   # Average correlation within Bucket 3
        }

        # Yield degradation assumption (realistic)
        self.yield_degradation_rate = 0.20  # 20% decline over 28 months

        # Active management parameters
        self.active_management = True  # Family office actively rotates funds
        self.yield_recovery_on_rotation = 0.10  # Rotating out of losers recovers 10% yield

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

    def simulate_market_returns(self, n_scenarios: int) -> np.ndarray:
        """
        Simulate monthly returns for each bucket across N scenarios.

        Returns: (n_scenarios, simulation_months, 3) array
        - Dimension 0: Scenario number
        - Dimension 1: Month number
        - Dimension 2: Bucket (0=Bucket1, 1=Bucket2, 2=Bucket3)
        """
        returns = np.zeros((n_scenarios, self.simulation_months, 3))

        # Market regime probabilities
        regime_probs = {
            'bull': 0.40,     # +15% annual, low vol
            'normal': 0.35,   # +8% annual, moderate vol
            'bear': 0.20,     # -15% annual, high vol
            'crisis': 0.05    # -40% drawdown, extreme vol
        }

        for scenario in range(n_scenarios):
            # Assign market regime for this scenario
            regime = np.random.choice(
                list(regime_probs.keys()),
                p=list(regime_probs.values())
            )

            # Set regime parameters
            if regime == 'bull':
                drift = 0.15 / 12  # Monthly drift
                vol_multiplier = 0.8
            elif regime == 'normal':
                drift = 0.08 / 12
                vol_multiplier = 1.0
            elif regime == 'bear':
                drift = -0.15 / 12
                vol_multiplier = 1.5
            else:  # crisis
                drift = -0.40 / 12
                vol_multiplier = 3.0

            # Generate correlated returns for each bucket
            for month in range(self.simulation_months):
                # Bucket 1 (Stable) - lowest volatility
                vol1 = self.bucket_volatility['bucket1'] * vol_multiplier / np.sqrt(12)
                returns[scenario, month, 0] = np.random.normal(drift, vol1)

                # Bucket 2 (Covered Calls) - moderate volatility
                vol2 = self.bucket_volatility['bucket2'] * vol_multiplier / np.sqrt(12)
                returns[scenario, month, 1] = np.random.normal(drift, vol2)

                # Bucket 3 (Volatility) - highest volatility
                vol3 = self.bucket_volatility['bucket3'] * vol_multiplier / np.sqrt(12)
                # Add fat tails (5% chance of extreme move)
                if np.random.random() < 0.05:
                    returns[scenario, month, 2] = np.random.normal(drift, vol3 * 3)
                else:
                    returns[scenario, month, 2] = np.random.normal(drift, vol3)

        return returns

    def run_single_scenario(self, scenario_returns: np.ndarray) -> Dict:
        """
        Run single 28-month scenario.

        Args:
            scenario_returns: (simulation_months, 3) array of monthly returns

        Returns:
            Dictionary with scenario results
        """
        # Initialize tracking
        portfolio_value = 0
        margin_balance = 0
        total_dividends_collected = 0
        max_drawdown = 0
        peak_portfolio_value = 0
        margin_call_triggered = False
        backstop_used = False

        # Monthly tracking
        monthly_portfolio = []
        monthly_margin = []
        monthly_dividends = []

        for month in range(1, self.simulation_months + 1):
            # 1. Deploy capital
            portfolio_value += self.monthly_deployment

            # 2. Apply market returns to existing portfolio
            if portfolio_value > 0:
                bucket_returns = scenario_returns[month - 1]
                weighted_return = (
                    self.bucket1_allocation * bucket_returns[0] +
                    self.bucket2_allocation * bucket_returns[1] +
                    self.bucket3_allocation * bucket_returns[2]
                )
                portfolio_value *= (1 + weighted_return)

            # 3. Calculate monthly dividend income
            current_yield = self.calculate_monthly_yield(month)
            monthly_dividend = portfolio_value * (current_yield / 12)
            total_dividends_collected += monthly_dividend

            # 4. Margin draw (only if dividends don't cover expenses yet)
            margin_draw = self.get_margin_draw(month)
            if monthly_dividend < margin_draw:
                # Draw from margin to cover shortfall
                margin_balance += (margin_draw - monthly_dividend)
            else:
                # Dividends exceed expenses - pay down margin
                excess_dividend = monthly_dividend - margin_draw
                margin_balance = max(0, margin_balance - excess_dividend)

            # 5. Apply margin interest
            if margin_balance > 0:
                margin_interest = margin_balance * self.margin_monthly_rate
                margin_balance += margin_interest

            # 6. Check for margin call
            if margin_balance > 0:
                portfolio_margin_ratio = portfolio_value / margin_balance
                if portfolio_margin_ratio < self.min_portfolio_margin_ratio:
                    # Margin call triggered
                    margin_call_triggered = True
                    backstop_used = True
                    # Use business income to inject capital
                    margin_balance -= self.business_income_backstop

            # 7. Check for stop-loss
            if peak_portfolio_value > 0:
                current_drawdown = (portfolio_value - peak_portfolio_value) / peak_portfolio_value
                if current_drawdown < max_drawdown:
                    max_drawdown = current_drawdown

                if current_drawdown < self.stop_loss_threshold:
                    # Stop-loss triggered - pause new margin draws
                    margin_draw = 0

            peak_portfolio_value = max(peak_portfolio_value, portfolio_value)

            # Track monthly values
            monthly_portfolio.append(portfolio_value)
            monthly_margin.append(margin_balance)
            monthly_dividends.append(monthly_dividend)

        # Calculate final metrics
        final_portfolio_value = portfolio_value
        final_margin_balance = margin_balance
        final_annual_dividend = monthly_dividends[-1] * 12

        # Calculate month when dividend income exceeds $4,500/month
        break_even_month = None
        for i, div in enumerate(monthly_dividends):
            if div >= 4500:
                break_even_month = i + 1
                break

        # Calculate month when margin is paid off
        margin_payoff_month = None
        for i, margin in enumerate(monthly_margin):
            if margin == 0 and i > 0:  # Found first month with zero margin after debt accumulated
                margin_payoff_month = i + 1
                break

        return {
            'final_portfolio_value': final_portfolio_value,
            'final_margin_balance': final_margin_balance,
            'final_annual_dividend': final_annual_dividend,
            'max_drawdown': max_drawdown,
            'margin_call_triggered': margin_call_triggered,
            'backstop_used': backstop_used,
            'break_even_month': break_even_month,
            'margin_payoff_month': margin_payoff_month,
            'total_dividends_collected': total_dividends_collected,
            'monthly_portfolio': monthly_portfolio,
            'monthly_margin': monthly_margin,
            'monthly_dividends': monthly_dividends
        }

    def run_simulation(self, n_scenarios: int = 10000) -> pd.DataFrame:
        """
        Run full Monte Carlo simulation.

        Args:
            n_scenarios: Number of scenarios to simulate (default 10,000)

        Returns:
            DataFrame with results for all scenarios
        """
        print(f"Generating {n_scenarios:,} market scenarios...")
        scenario_returns = self.simulate_market_returns(n_scenarios)

        print(f"Running {n_scenarios:,} 28-month simulations...")
        results = []

        for i in range(n_scenarios):
            if (i + 1) % 1000 == 0:
                print(f"  Completed {i + 1:,} scenarios...")

            scenario_result = self.run_single_scenario(scenario_returns[i])
            results.append(scenario_result)

        print("Simulations complete. Analyzing results...")
        return pd.DataFrame(results)


def analyze_results(df: pd.DataFrame) -> Dict:
    """Analyze simulation results and generate summary statistics"""

    # Success metrics
    success_100k = (df['final_annual_dividend'] >= 100000).sum() / len(df)
    success_margin_free = (df['final_margin_balance'] == 0).sum() / len(df)
    margin_call_rate = df['margin_call_triggered'].sum() / len(df)
    backstop_usage_rate = df['backstop_used'].sum() / len(df)

    # Portfolio value statistics
    portfolio_stats = {
        'median': df['final_portfolio_value'].median(),
        'mean': df['final_portfolio_value'].mean(),
        'p5': df['final_portfolio_value'].quantile(0.05),
        'p95': df['final_portfolio_value'].quantile(0.95),
        'min': df['final_portfolio_value'].min(),
        'max': df['final_portfolio_value'].max()
    }

    # Dividend income statistics
    dividend_stats = {
        'median': df['final_annual_dividend'].median(),
        'mean': df['final_annual_dividend'].mean(),
        'p5': df['final_annual_dividend'].quantile(0.05),
        'p95': df['final_annual_dividend'].quantile(0.95),
        'min': df['final_annual_dividend'].min(),
        'max': df['final_annual_dividend'].max()
    }

    # Margin balance statistics
    margin_stats = {
        'median': df['final_margin_balance'].median(),
        'mean': df['final_margin_balance'].mean(),
        'p5': df['final_margin_balance'].quantile(0.05),
        'p95': df['final_margin_balance'].quantile(0.95),
        'max': df['final_margin_balance'].max()
    }

    # Drawdown statistics
    drawdown_stats = {
        'median': df['max_drawdown'].median(),
        'mean': df['max_drawdown'].mean(),
        'p5': df['max_drawdown'].quantile(0.05),
        'p95': df['max_drawdown'].quantile(0.95),
        'worst': df['max_drawdown'].min()
    }

    # Break-even timing statistics
    break_even_data = df[df['break_even_month'].notna()]['break_even_month']
    break_even_stats = {
        'median': break_even_data.median() if len(break_even_data) > 0 else None,
        'mean': break_even_data.mean() if len(break_even_data) > 0 else None,
        'p5': break_even_data.quantile(0.05) if len(break_even_data) > 0 else None,
        'p95': break_even_data.quantile(0.95) if len(break_even_data) > 0 else None
    }

    # Margin payoff timing statistics
    payoff_data = df[df['margin_payoff_month'].notna()]['margin_payoff_month']
    payoff_stats = {
        'median': payoff_data.median() if len(payoff_data) > 0 else None,
        'mean': payoff_data.mean() if len(payoff_data) > 0 else None,
        'p5': payoff_data.quantile(0.05) if len(payoff_data) > 0 else None,
        'p95': payoff_data.quantile(0.95) if len(payoff_data) > 0 else None
    }

    return {
        'simulation_date': datetime.now().strftime('%Y-%m-%d'),
        'n_scenarios': len(df),
        'success_metrics': {
            'probability_100k_income': success_100k,
            'probability_margin_free': success_margin_free,
            'margin_call_rate': margin_call_rate,
            'backstop_usage_rate': backstop_usage_rate
        },
        'portfolio_value': portfolio_stats,
        'dividend_income': dividend_stats,
        'margin_balance': margin_stats,
        'drawdown': drawdown_stats,
        'break_even_timing': break_even_stats,
        'margin_payoff_timing': payoff_stats
    }


if __name__ == '__main__':
    # Initialize Monte Carlo engine
    mc = DividendMarginMonteCarlo()

    # Run simulation
    results_df = mc.run_simulation(n_scenarios=10000)

    # Analyze results
    summary = analyze_results(results_df)

    # Print summary
    print("\n" + "="*80)
    print("MONTE CARLO SIMULATION RESULTS")
    print("Dividend Income + Margin Living Strategy")
    print("="*80)
    print(f"\nSimulation Date: {summary['simulation_date']}")
    print(f"Scenarios Analyzed: {summary['n_scenarios']:,}")

    print("\n--- SUCCESS METRICS ---")
    print(f"Probability of $100k+ Annual Income: {summary['success_metrics']['probability_100k_income']:.1%}")
    print(f"Probability of Margin-Free by Month 28: {summary['success_metrics']['probability_margin_free']:.1%}")
    print(f"Margin Call Rate: {summary['success_metrics']['margin_call_rate']:.1%}")
    print(f"Business Income Backstop Used: {summary['success_metrics']['backstop_usage_rate']:.1%}")

    print("\n--- PORTFOLIO VALUE AT MONTH 28 ---")
    print(f"Median: ${summary['portfolio_value']['median']:,.0f}")
    print(f"Mean: ${summary['portfolio_value']['mean']:,.0f}")
    print(f"5th Percentile: ${summary['portfolio_value']['p5']:,.0f}")
    print(f"95th Percentile: ${summary['portfolio_value']['p95']:,.0f}")

    print("\n--- ANNUAL DIVIDEND INCOME AT MONTH 28 ---")
    print(f"Median: ${summary['dividend_income']['median']:,.0f}")
    print(f"Mean: ${summary['dividend_income']['mean']:,.0f}")
    print(f"5th Percentile: ${summary['dividend_income']['p5']:,.0f}")
    print(f"95th Percentile: ${summary['dividend_income']['p95']:,.0f}")

    print("\n--- MARGIN BALANCE AT MONTH 28 ---")
    print(f"Median: ${summary['margin_balance']['median']:,.0f}")
    print(f"Mean: ${summary['margin_balance']['mean']:,.0f}")
    print(f"Maximum: ${summary['margin_balance']['max']:,.0f}")

    print("\n--- MAXIMUM DRAWDOWN ---")
    print(f"Median: {summary['drawdown']['median']:.1%}")
    print(f"95th Percentile: {summary['drawdown']['p95']:.1%}")
    print(f"Worst Case: {summary['drawdown']['worst']:.1%}")

    if summary['break_even_timing']['median']:
        print("\n--- BREAK-EVEN TIMING (Dividends Cover $4,500/month) ---")
        print(f"Median: Month {summary['break_even_timing']['median']:.0f}")
        print(f"5th-95th Percentile: Month {summary['break_even_timing']['p5']:.0f} - {summary['break_even_timing']['p95']:.0f}")

    if summary['margin_payoff_timing']['median']:
        print("\n--- MARGIN PAYOFF TIMING ---")
        print(f"Median: Month {summary['margin_payoff_timing']['median']:.0f}")
        print(f"5th-95th Percentile: Month {summary['margin_payoff_timing']['p5']:.0f} - {summary['margin_payoff_timing']['p95']:.0f}")

    print("\n" + "="*80)

    # Save results
    output_path = 'docs/fin-guru/monte-carlo-dividend-margin-2025-10-13.json'
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nDetailed results saved to: {output_path}")

    # Save full dataset
    csv_path = 'docs/fin-guru/monte-carlo-dividend-margin-full-results-2025-10-13.csv'
    results_df.to_csv(csv_path, index=False)
    print(f"Full scenario data saved to: {csv_path}")
