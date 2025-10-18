#!/usr/bin/env python3
"""
Simulate time to reach target annual dividend run-rate under DRIP + margin-for-expenses.

Assumptions:
- Monthly contributions are deployed by target weights.
- Dividends are reinvested (DRIP): cash buys more shares monthly.
- Expenses are funded by margin; margin accrues interest monthly.
- Dividend per-share follows Normal(mu, sd) using last 36 months history.

Outputs median/p25/p75 month when annualized monthly dividend >= target,
and probabilities of hitting target by 24/28/36 months.

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
    'YYY':0.05,'XYLD':0.05,
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


def simulate(weights: Dict[str, float], monthly_contrib: float, expenses: float, months: int, runs: int, target_income: float, margin_rate_annual: float, seed: int = 123):
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
    ann_income = np.zeros((runs, months))
    margin = np.zeros(runs)
    r_m = margin_rate_annual / 12.0

    for m in range(months):
        shares += (buys / prices)
        div_draw = rng.normal(mu, sd, size=(runs, len(mu)))
        div_draw = np.clip(div_draw, 0.0, None)
        cash = (shares * div_draw)
        # DRIP: reinvest into same tickers
        shares += (cash / prices)
        month_income = cash.sum(axis=1)
        ann_income[:, m] = month_income * 12.0
        # margin grows (expenses + interest)
        margin = margin * (1.0 + r_m) + expenses

    hit = (ann_income >= target_income)
    first = np.argmax(hit, axis=1)
    reached = hit.any(axis=1)
    first = np.where(reached, first + 1, np.nan)

    out = {
        'median_month': float(np.nanmedian(first)),
        'p25_month': float(np.nanpercentile(first, 25)),
        'p75_month': float(np.nanpercentile(first, 75)),
        'prob_by_24': float(np.nanmean(first <= 24)),
        'prob_by_28': float(np.nanmean(first <= 28)),
        'prob_by_36': float(np.nanmean(first <= 36)),
        'margin_after_months': float(np.mean(margin)),  # deterministic here
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--portfolio', choices=['A', 'B'], default='A')
    ap.add_argument('--target', type=float, default=100000.0)
    ap.add_argument('--expenses', type=float, default=4500.0)
    ap.add_argument('--months', type=int, default=48)
    ap.add_argument('--runs', type=int, default=5000)
    ap.add_argument('--contrib', type=float, default=13317.0)
    ap.add_argument('--margin-rate', type=float, default=0.10875)
    ap.add_argument('--seed', type=int, default=123)
    args = ap.parse_args()

    weights = OPT_A if args.portfolio == 'A' else OPT_B
    res = simulate(weights, args.contrib, args.expenses, args.months, args.runs, args.target, args.margin_rate, args.seed)
    print(json.dumps({'inputs': vars(args), 'results': res}, indent=2))


if __name__ == '__main__':
    main()

