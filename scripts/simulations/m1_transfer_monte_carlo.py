#!/usr/bin/env python3
"""
M1 Finance Transfer Analysis - Monte Carlo Simulation
Comparing Scenario A (Keep in Layer 1) vs Scenario B (Liquidate for Layer 2)
Analysis Date: 2025-10-28
"""

import numpy as np
import pandas as pd
from datetime import datetime

# Analysis Parameters
CURRENT_DATE = "2025-10-28"
TIME_HORIZON_YEARS = 4  # 3-5 years, using midpoint
SIMULATIONS = 10000
TAX_RATE = 0.15  # 15% long-term capital gains

# M1 Holdings (from transfer data)
M1_HOLDINGS = {
    "VOO": 4264.86,
    "VTI": 3600.63,
    "VXUS": 1950.43,
    "QQQ": 1124.39
}
M1_TOTAL_VALUE = sum(M1_HOLDINGS.values())  # $10,940.31
M1_UNREALIZED_GAIN = 1478.22  # From M1 screenshots
M1_TAX_HIT = M1_UNREALIZED_GAIN * TAX_RATE  # $221.73

# Risk Metrics from Phase 1 Analysis
RISK_METRICS = {
    "VOO": {"return": 0.1926, "sharpe": 0.798, "volatility": 0.1849, "max_dd": -0.187},
    "VTI": {"return": 0.1912, "sharpe": 0.753, "volatility": 0.1940, "max_dd": -0.193},
    "VXUS": {"return": 0.2186, "sharpe": 1.107, "volatility": 0.1569, "max_dd": -0.136},
    "QQQ": {"return": 0.2817, "sharpe": 0.973, "volatility": 0.2347, "max_dd": -0.228},
}

# Weighted average for M1 portfolio
M1_WEIGHTS = {k: v/M1_TOTAL_VALUE for k, v in M1_HOLDINGS.items()}
M1_EXPECTED_RETURN = sum(RISK_METRICS[k]["return"] * M1_WEIGHTS[k] for k in M1_HOLDINGS.keys())
M1_VOLATILITY = sum(RISK_METRICS[k]["volatility"] * M1_WEIGHTS[k] for k in M1_HOLDINGS.keys())

# Layer 2 Dividend Portfolio Assumptions (from user profile)
LAYER2_BLENDED_YIELD = 0.24  # 24% annual yield
LAYER2_VOLATILITY = 0.15  # Conservative estimate for dividend CEFs
LAYER2_EXPECTED_RETURN = 0.10  # 10% total return (24% yield - 14% NAV decay typical for CEFs)

print("=" * 80)
print("M1 FINANCE TRANSFER ANALYSIS - MONTE CARLO SIMULATION")
print("=" * 80)
print(f"Analysis Date: {CURRENT_DATE}")
print(f"Time Horizon: {TIME_HORIZON_YEARS} years")
print(f"Simulations: {SIMULATIONS:,}")
print(f"Tax Rate: {TAX_RATE:.1%}")
print()

print("M1 TRANSFER DETAILS:")
print(f"  Total Value: ${M1_TOTAL_VALUE:,.2f}")
print(f"  Unrealized Gain: ${M1_UNREALIZED_GAIN:,.2f}")
print(f"  Tax Hit (if liquidated): ${M1_TAX_HIT:,.2f}")
print()

print("M1 PORTFOLIO CHARACTERISTICS:")
print(f"  Expected Annual Return: {M1_EXPECTED_RETURN:.2%}")
print(f"  Annual Volatility: {M1_VOLATILITY:.2%}")
print()

print("LAYER 2 DIVIDEND PORTFOLIO CHARACTERISTICS:")
print(f"  Expected Annual Return: {LAYER2_EXPECTED_RETURN:.2%}")
print(f"  Blended Yield: {LAYER2_BLENDED_YIELD:.2%}")
print(f"  Annual Volatility: {LAYER2_VOLATILITY:.2%}")
print()

# SCENARIO A: Keep M1 holdings in Layer 1 (Growth)
print("=" * 80)
print("SCENARIO A: KEEP M1 HOLDINGS IN LAYER 1 (GROWTH)")
print("=" * 80)

np.random.seed(42)
scenario_a_results = []

for i in range(SIMULATIONS):
    value = M1_TOTAL_VALUE
    annual_returns = []

    for year in range(TIME_HORIZON_YEARS):
        # Generate random return using geometric Brownian motion
        z = np.random.normal(0, 1)
        annual_return = M1_EXPECTED_RETURN + M1_VOLATILITY * z
        value *= (1 + annual_return)
        annual_returns.append(annual_return)

    scenario_a_results.append({
        "final_value": value,
        "total_return": (value - M1_TOTAL_VALUE) / M1_TOTAL_VALUE,
        "cagr": ((value / M1_TOTAL_VALUE) ** (1/TIME_HORIZON_YEARS)) - 1,
        "worst_year": min(annual_returns),
        "best_year": max(annual_returns)
    })

scenario_a_df = pd.DataFrame(scenario_a_results)

print(f"\nFinal Value Statistics (after {TIME_HORIZON_YEARS} years):")
print(f"  Mean: ${scenario_a_df['final_value'].mean():,.2f}")
print(f"  Median: ${scenario_a_df['final_value'].median():,.2f}")
print(f"  5th Percentile: ${scenario_a_df['final_value'].quantile(0.05):,.2f}")
print(f"  95th Percentile: ${scenario_a_df['final_value'].quantile(0.95):,.2f}")
print("\nCAGR Statistics:")
print(f"  Mean: {scenario_a_df['cagr'].mean():.2%}")
print(f"  Median: {scenario_a_df['cagr'].median():.2%}")
print(f"  5th Percentile: {scenario_a_df['cagr'].quantile(0.05):.2%}")
print(f"  95th Percentile: {scenario_a_df['cagr'].quantile(0.95):.2%}")
print("\nTotal Return Statistics:")
print(f"  Mean: {scenario_a_df['total_return'].mean():.2%}")
print(f"  Probability of Positive Return: {(scenario_a_df['total_return'] > 0).mean():.1%}")
print(f"  Probability of >50% Gain: {(scenario_a_df['total_return'] > 0.5).mean():.1%}")

# SCENARIO B: Liquidate and deploy to Layer 2 (Dividend)
print("\n" + "=" * 80)
print("SCENARIO B: LIQUIDATE M1 → DEPLOY TO LAYER 2 (DIVIDEND)")
print("=" * 80)

np.random.seed(42)
scenario_b_results = []

# After-tax capital available
initial_capital_b = M1_TOTAL_VALUE - M1_TAX_HIT
print(f"Starting Capital (after 15% tax): ${initial_capital_b:,.2f}")
print()

for i in range(SIMULATIONS):
    value = initial_capital_b
    cumulative_dividends = 0
    annual_returns = []

    for year in range(TIME_HORIZON_YEARS):
        # NAV growth/decay (dividend funds typically have NAV decay)
        z = np.random.normal(0, 1)
        nav_return = (LAYER2_EXPECTED_RETURN - LAYER2_BLENDED_YIELD) + LAYER2_VOLATILITY * z

        # Dividends received (assumed to be reinvested)
        dividends = value * LAYER2_BLENDED_YIELD
        cumulative_dividends += dividends

        # Total return = NAV change + dividends
        total_return = nav_return + LAYER2_BLENDED_YIELD
        value *= (1 + nav_return)  # NAV change only
        value += dividends  # Reinvest dividends

        annual_returns.append(total_return)

    scenario_b_results.append({
        "final_value": value,
        "cumulative_dividends": cumulative_dividends,
        "total_return": (value - initial_capital_b) / initial_capital_b,
        "cagr": ((value / initial_capital_b) ** (1/TIME_HORIZON_YEARS)) - 1,
        "worst_year": min(annual_returns),
        "best_year": max(annual_returns)
    })

scenario_b_df = pd.DataFrame(scenario_b_results)

print(f"Final Value Statistics (after {TIME_HORIZON_YEARS} years):")
print(f"  Mean: ${scenario_b_df['final_value'].mean():,.2f}")
print(f"  Median: ${scenario_b_df['final_value'].median():,.2f}")
print(f"  5th Percentile: ${scenario_b_df['final_value'].quantile(0.05):,.2f}")
print(f"  95th Percentile: ${scenario_b_df['final_value'].quantile(0.95):,.2f}")
print("\nCumulative Dividends Received:")
print(f"  Mean: ${scenario_b_df['cumulative_dividends'].mean():,.2f}")
print(f"  Median: ${scenario_b_df['cumulative_dividends'].median():,.2f}")
print("\nCAGR Statistics:")
print(f"  Mean: {scenario_b_df['cagr'].mean():.2%}")
print(f"  Median: {scenario_b_df['cagr'].median():.2%}")
print(f"  5th Percentile: {scenario_b_df['cagr'].quantile(0.05):.2%}")
print(f"  95th Percentile: {scenario_b_df['cagr'].quantile(0.95):.2%}")
print("\nTotal Return Statistics:")
print(f"  Mean: {scenario_b_df['total_return'].mean():.2%}")
print(f"  Probability of Positive Return: {(scenario_b_df['total_return'] > 0).mean():.1%}")
print(f"  Probability of >50% Gain: {(scenario_b_df['total_return'] > 0.5).mean():.1%}")

# COMPARATIVE ANALYSIS
print("\n" + "=" * 80)
print("COMPARATIVE ANALYSIS")
print("=" * 80)

mean_diff = scenario_a_df['final_value'].mean() - scenario_b_df['final_value'].mean()
median_diff = scenario_a_df['final_value'].median() - scenario_b_df['final_value'].median()

print("\nExpected Final Value Difference (Scenario A - Scenario B):")
print(f"  Mean: ${mean_diff:,.2f}")
print(f"  Median: ${median_diff:,.2f}")
print()

if mean_diff > 0:
    print(f"✅ Scenario A (Keep in Layer 1) outperforms by ${mean_diff:,.2f} on average")
    pct_diff = (mean_diff / scenario_b_df['final_value'].mean()) * 100
    print(f"   That's {pct_diff:.1f}% higher than Scenario B")
else:
    print(f"✅ Scenario B (Deploy to Layer 2) outperforms by ${abs(mean_diff):,.2f} on average")
    pct_diff = (abs(mean_diff) / scenario_a_df['final_value'].mean()) * 100
    print(f"   That's {pct_diff:.1f}% higher than Scenario A")

print(f"\nProbability Scenario A > Scenario B: {(scenario_a_df['final_value'] > scenario_b_df['final_value']).mean():.1%}")
print(f"Probability Scenario B > Scenario A: {(scenario_b_df['final_value'] > scenario_a_df['final_value']).mean():.1%}")

# Tax Break-Even Analysis
print("\n" + "=" * 80)
print("TAX BREAK-EVEN ANALYSIS")
print("=" * 80)
print(f"Tax cost to liquidate: ${M1_TAX_HIT:,.2f}")
print("\nTo break even on the tax hit, Scenario B must generate:")
print(f"  ${M1_TAX_HIT:,.2f} in additional value over {TIME_HORIZON_YEARS} years")
print()

# Calculate years to break even on dividends alone
annual_dividend_income_b = initial_capital_b * LAYER2_BLENDED_YIELD
years_to_recover_tax = M1_TAX_HIT / annual_dividend_income_b
print(f"Annual dividend income from Layer 2: ${annual_dividend_income_b:,.2f}")
print(f"Years to recover tax via dividends alone: {years_to_recover_tax:.2f} years")

if years_to_recover_tax < TIME_HORIZON_YEARS:
    print(f"✅ Tax cost recovered in {years_to_recover_tax:.2f} years (within {TIME_HORIZON_YEARS}-year horizon)")
else:
    print(f"⚠️  Tax cost NOT fully recovered in {TIME_HORIZON_YEARS}-year horizon")

# Risk-Adjusted Return Comparison
print("\n" + "=" * 80)
print("RISK-ADJUSTED PERFORMANCE")
print("=" * 80)

# Calculate Sharpe ratios for both scenarios
risk_free_rate = 0.04  # Assume 4% risk-free rate

scenario_a_sharpe = (scenario_a_df['cagr'].mean() - risk_free_rate) / scenario_a_df['cagr'].std()
scenario_b_sharpe = (scenario_b_df['cagr'].mean() - risk_free_rate) / scenario_b_df['cagr'].std()

print("\nScenario A (Keep in Layer 1):")
print(f"  Mean CAGR: {scenario_a_df['cagr'].mean():.2%}")
print(f"  CAGR Std Dev: {scenario_a_df['cagr'].std():.2%}")
print(f"  Sharpe Ratio: {scenario_a_sharpe:.3f}")

print("\nScenario B (Deploy to Layer 2):")
print(f"  Mean CAGR: {scenario_b_df['cagr'].mean():.2%}")
print(f"  CAGR Std Dev: {scenario_b_df['cagr'].std():.2%}")
print(f"  Sharpe Ratio: {scenario_b_sharpe:.3f}")

print()
if scenario_a_sharpe > scenario_b_sharpe:
    print(f"✅ Scenario A has superior risk-adjusted returns (Sharpe: {scenario_a_sharpe:.3f} vs {scenario_b_sharpe:.3f})")
else:
    print(f"✅ Scenario B has superior risk-adjusted returns (Sharpe: {scenario_b_sharpe:.3f} vs {scenario_a_sharpe:.3f})")

# FINAL RECOMMENDATION
print("\n" + "=" * 80)
print("QUANTITATIVE RECOMMENDATION")
print("=" * 80)

print("\nBased on 10,000 Monte Carlo simulations over 4 years:\n")

if mean_diff > 1000:  # If difference > $1,000
    confidence = (scenario_a_df['final_value'] > scenario_b_df['final_value']).mean()
    print("✅ RECOMMENDATION: KEEP M1 HOLDINGS IN LAYER 1 (GROWTH)")
    print("\n   Statistical Support:")
    print(f"   • Expected outperformance: ${mean_diff:,.2f} ({pct_diff:.1f}% higher)")
    print(f"   • Probability of outperformance: {confidence:.1%}")
    print(f"   • Superior risk-adjusted returns (Sharpe: {scenario_a_sharpe:.3f} vs {scenario_b_sharpe:.3f})")
    print(f"   • No tax drag (${M1_TAX_HIT:,.2f} tax cost avoided)")
    print("   • Diversification benefit (adds VXUS international exposure)")
elif mean_diff < -1000:
    confidence = (scenario_b_df['final_value'] > scenario_a_df['final_value']).mean()
    print("✅ RECOMMENDATION: LIQUIDATE M1 → DEPLOY TO LAYER 2 (DIVIDEND)")
    print("\n   Statistical Support:")
    print(f"   • Expected outperformance: ${abs(mean_diff):,.2f} ({pct_diff:.1f}% higher)")
    print(f"   • Probability of outperformance: {confidence:.1%}")
    print(f"   • Tax break-even achieved in {years_to_recover_tax:.2f} years")
    print("   • Accelerates dividend income strategy")
else:
    print("⚖️  RECOMMENDATION: STATISTICALLY EQUIVALENT (difference < $1,000)")
    print("\n   Both scenarios produce similar outcomes. Default to KEEP IN LAYER 1 to avoid tax friction.")

print("\n" + "=" * 80)
print(f"Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
