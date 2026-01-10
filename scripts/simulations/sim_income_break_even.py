#!/usr/bin/env python3
"""
Simulate income break-even timing for income portfolios.

- Uses yfinance to fetch last close prices and monthly dividend histories
- Simulates monthly contributions and stochastic dividends for each holding
- Estimates first month when monthly cash income >= expenses

Usage examples:
  uv run python scripts/sim_income_break_even.py --portfolio A --expenses 4500 --months 48 --runs 5000
  uv run python scripts/sim_income_break_even.py --portfolio B --expenses 6213 --contrib-bump 2000

Outputs JSON with median/p25/p75 month and probability by 24/28/36 months.

Educational-only; not investment advice.
"""

import argparse
import json
from typing import Dict

import numpy as np
import yfinance as yf


OPT_A: Dict[str, float] = {
    'QQQI':0.20,'JEPQ':0.15,'SPYI':0.10,'BDJ':0.10,'ETY':0.10,
    'ETV':0.05,'BST':0.10,'UTG':0.05,'PDI':0.075,'PDO':0.075
}

OPT_B: Dict[str, float] = {
    **OPT_A,
    'YYY':0.05,
    'XYLD':0.05,
    'BDJ':OPT_A['BDJ']-0.025,
    'ETY':OPT_A['ETY']-0.025,
    'PDO':OPT_A['PDO']-0.025,
}


def get_price(t: str) -> float:
    hist = yf.Ticker(t).history(period='1d')
    return float(hist['Close'][-1]) if not hist.empty else float('nan')


def monthly_div_stats(t: str):
    div = yf.Ticker(t).dividends
    if div is None or div.empty:
        return 0.0, 0.0
    df = div.to_frame('div')
    df['m'] = df.index.to_period('M')
    m = df.groupby('m')['div'].sum().tail(36)
    mu = float(m.mean()) if len(m) > 0 else 0.0
    sd = float(m.std(ddof=1)) if len(m) > 1 else 0.0
    return mu, sd


def simulate(weights: Dict[str, float], monthly_contrib: float, expense: float, months: int, runs: int, seed: int = 42):
    tickers = [t for t, w in weights.items() if w > 0]
    prices = np.array([get_price(t) for t in tickers])
    mu_sd = [monthly_div_stats(t) for t in tickers]
    mu = np.array([x[0] for x in mu_sd])
    sd = np.array([x[1] for x in mu_sd])

    wts = np.array([weights[t] for t in tickers])
    buys = monthly_contrib * wts

    valid = (prices > 0) & (wts > 0)
    prices = prices[valid]
    mu = mu[valid]
    sd = sd[valid]
    buys = buys[valid]

    rng = np.random.default_rng(seed)
    shares = np.zeros((runs, len(buys)))
    monthly_income = np.zeros((runs, months))

    for m in range(months):
        shares += (buys / prices)
        div_draw = rng.normal(mu, sd, size=(runs, len(mu)))
        div_draw = np.clip(div_draw, 0.0, None)
        monthly_income[:, m] = (shares * div_draw).sum(axis=1)

    first_idx = np.argmax(monthly_income >= expense, axis=1)
    reached = (monthly_income >= expense).any(axis=1)
    first_month = np.where(reached, first_idx + 1, np.nan)

    out = {
        'median_month': float(np.nanmedian(first_month)),
        'p25_month': float(np.nanpercentile(first_month, 25)),
        'p75_month': float(np.nanpercentile(first_month, 75)),
        'prob_by_24': float(np.nanmean(first_month <= 24)),
        'prob_by_28': float(np.nanmean(first_month <= 28)),
        'prob_by_36': float(np.nanmean(first_month <= 36)),
    }
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--portfolio', choices=['A', 'B'], default='A')
    p.add_argument('--expenses', type=float, default=4500.0)
    p.add_argument('--months', type=int, default=48)
    p.add_argument('--runs', type=int, default=5000)
    p.add_argument('--contrib', type=float, default=13317.0)
    p.add_argument('--contrib-bump', type=float, default=0.0)
    p.add_argument('--seed', type=int, default=42)
    args = p.parse_args()

    weights = OPT_A if args.portfolio == 'A' else OPT_B
    res = simulate(weights, args.contrib + args.contrib_bump, args.expenses, args.months, args.runs, args.seed)
    print(json.dumps({
        'portfolio': args.portfolio,
        'expenses': args.expenses,
        'months': args.months,
        'runs': args.runs,
        'contrib_total': args.contrib + args.contrib_bump,
        'results': res,
    }, indent=2))


if __name__ == '__main__':
    main()

