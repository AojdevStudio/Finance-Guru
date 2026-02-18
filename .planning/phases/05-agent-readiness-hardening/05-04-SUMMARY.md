---
phase: 05-agent-readiness-hardening
plan: 04
subsystem: testing
tags: [pytest, coverage, risk-metrics, momentum, volatility, correlation, moving-averages, market-data]

# Dependency graph
requires:
  - phase: 05-01
    provides: Ruff linter configuration ensuring test files are lint-clean
provides:
  - Comprehensive test coverage for 6 core analysis/utility modules
  - 117 new tests bringing total from 438 to 550+
  - Coverage increase from 26% to 35% (core modules 86-99%)
affects: [05-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [synthetic data generation with numpy/pandas for financial test fixtures, mock-based API testing]

key-files:
  created: [tests/python/test_momentum.py, tests/python/test_volatility.py, tests/python/test_correlation.py, tests/python/test_moving_averages.py, tests/python/test_market_data.py]
  modified: [tests/python/test_risk_metrics.py, src/analysis/correlation.py]

key-decisions:
  - "All tests use synthetic data (numpy random walks) -- zero real API calls"
  - "pytest.approx() for all floating-point comparisons"
  - "Known-answer tests where formulas are verifiable (SMA, WMA, beta of self=1.0)"
  - "Market data tests use unittest.mock to mock yfinance and requests modules"

metrics:
  duration: "14 min"
  completed: "2026-02-13"
  tests-added: 117
  coverage-before: "26%"
  coverage-after: "35%"
---

# Phase 05 Plan 04: Core Test Coverage Summary

Comprehensive test coverage for the 6 largest untested analysis and utility modules, raising total tests from 438 to 550+ and coverage from 26% to 35%.

## Tasks Completed

### Task 1: Analysis Calculator Tests (risk_metrics, momentum, volatility, correlation)

Created/rewrote 4 test files with 85 tests covering:

- _risk_metrics.py_ (97% coverage): VaR (historical/parametric), CVaR, Sharpe ratio, Sortino ratio, max drawdown, Calmar ratio, annual volatility, beta/alpha calculations, convenience wrapper
- _momentum.py_ (95% coverage): RSI with signal thresholds, MACD with histogram verification, Stochastic oscillator with high/low validation, Williams %R range checks, ROC with trend detection, calculate_all combined output
- _volatility.py_ (99% coverage): Bollinger Bands (upper > middle > lower), ATR scaling with volatility, historical vol (annual > daily), Keltner Channels, regime classification (low/normal/high/extreme)
- _correlation.py_ (95% coverage): Pearson and Spearman matrices, diagonal=1.0, symmetric, covariance positive diagonal, diversification scoring, rolling correlations, concentration warnings

### Task 2: Utility Calculator Tests (moving_averages, market_data)

Created 2 test files with 32 tests covering:

- _moving_averages.py_ (86% coverage): SMA known-answer (period 3 of [1,2,3,4,5] = [2,3,4]), WMA weighted average verification, EMA vs SMA responsiveness, HMA calculation, price position detection (ABOVE/BELOW/AT), crossover signal detection, Golden Cross/Death Cross
- _market_data.py_ (66% coverage): yfinance mocking (single/multiple tickers, price change calculation, regularMarketPrice fallback, error handling, zero previousClose), Finnhub realtime mocking, API key fallback behavior, network error fallback, input normalization (string to list, uppercasing)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed correlation.py rolling dates type handling**

- _Found during:_ Task 1 (correlation tests)
- _Issue:_ `_calculate_rolling_correlations` called `.date()` on `datetime.date` objects (which don't have that method), causing `AttributeError` when index contains date objects rather than datetime objects
- _Fix:_ Added conditional check: `d.date() if hasattr(d, "date") and callable(d.date) else d`
- _Files modified:_ `src/analysis/correlation.py`
- _Commit:_ 43cd422

## Coverage Report

| Module | Before | After |
|--------|--------|-------|
| src/analysis/risk_metrics.py | 0% | 97% |
| src/analysis/correlation.py | 0% | 95% |
| src/utils/momentum.py | 0% | 95% |
| src/utils/volatility.py | 0% | 99% |
| src/utils/moving_averages.py | 0% | 86% |
| src/utils/market_data.py | 0% | 66% |
| **Overall src/** | **26%** | **35%** |

Note: CLI wrapper files (*_cli.py) remain at 0% -- they are excluded from coverage targets per plan as they are I/O-only thin wrappers. The remaining gap to 80% is primarily these CLI files plus strategies/ modules (backtester, optimizer).

## Next Phase Readiness

Plan 05-05 should raise `--cov-fail-under` from 0 toward the 80% target. The core calculator modules are now well-covered, but strategies/ (backtester, optimizer) and remaining utility modules still need tests.
