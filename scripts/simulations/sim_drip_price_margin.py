#!/usr/bin/env python3
"""
DRIP + Price Path + Margin Risk Simulator

Simulates monthly price returns (bootstrapped from historical monthly returns),
monthly dividends with DRIP, and margin-funded expenses to estimate:
- Time to dividend run-rate targets
- Probability of breaching portfolio-to-margin ratio thresholds (e.g., 3.5x, 3.0x)

Educational-only; not investment advice.
"""

import argparse
import json
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
import warnings
from pathlib import Path

# Suppress noisy warnings from pandas/yfinance in batch sims
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


V2_WEIGHTS: Dict[str, float] = {
    "CLM": 0.18,
    "CRF": 0.12,
    "QQQI": 0.18,
    "SPYI": 0.12,
    "JEPQ": 0.10,
    "BDJ": 0.08,
    "ETY": 0.08,
    "ETV": 0.05,
    "UTG": 0.04,
    "BST": 0.05,
}


def last_price(t: str) -> float:
    h = yf.Ticker(t).history(period="1d")
    return float(h["Close"].iloc[-1]) if not h.empty else np.nan


def monthly_div_mu_sd(t: str) -> Tuple[float, float]:
    div = yf.Ticker(t).dividends
    if div is None or div.empty:
        return 0.0, 0.0
    df = div.to_frame("div")
    df["m"] = df.index.to_period("M")
    m = df.groupby("m")["div"].sum()
    m = m.tail(36)
    if len(m) == 0:
        return 0.0, 0.0
    mu = float(m.mean())
    sd = float(m.std(ddof=1)) if len(m) > 1 else 0.0
    return mu, sd


def monthly_returns(t: str) -> np.ndarray:
    h = yf.Ticker(t).history(period="5y")
    if h.empty:
        h = yf.Ticker(t).history(period="3y")
    if h.empty:
        return np.array([0.0])
    m = h["Close"].resample("ME").last().pct_change().dropna()
    if len(m) < 6:
        return np.array([0.0])
    return m.values


def simulate(weights: Dict[str, float], contrib: float, expense: float, target_income: float, months: int, runs: int, margin_apr: float, seed: int = 2025):
    tickers = [t for t, w in weights.items() if w > 0]
    px0 = np.array([last_price(t) for t in tickers])
    mu_sd = [monthly_div_mu_sd(t) for t in tickers]
    mu = np.array([x[0] for x in mu_sd])
    sd = np.array([x[1] for x in mu_sd])
    rets = {t: monthly_returns(t) for t in tickers}

    wts = np.array([weights[t] for t in tickers])
    buys = contrib * wts
    r_m = margin_apr / 12.0

    rng = np.random.default_rng(seed)
    shares = np.zeros((runs, len(tickers)))
    prices = np.tile(px0, (runs, 1))
    ann_income = np.zeros((runs, months))
    margin = np.zeros(runs)
    ratio = np.full((runs, months), np.inf)

    for m in range(months):
        # Buy at start-of-month with contributions
        prices = prices  # prices already at start of month
        shares += (buys / prices)

        # Dividends for the month per share
        div_draw = rng.normal(mu, sd, size=(runs, len(mu)))
        div_draw = np.clip(div_draw, 0.0, None)
        cash = (shares * div_draw)

        # DRIP: reinvest dividends at current price (approx.)
        shares += (cash / prices)

        # Update prices by sampling a monthly return per ticker (bootstrapped)
        for j, t in enumerate(tickers):
            rts = rets[t]
            if len(rts) > 1:
                draw = rng.choice(rts)
            else:
                draw = 0.0
            prices[:, j] *= (1.0 + draw)

        # Record income and margin
        month_income = cash.sum(axis=1)
        ann_income[:, m] = month_income * 12.0
        margin = margin * (1.0 + r_m) + expense

        port_val = (shares * prices).sum(axis=1)
        ratio[:, m] = np.where(margin > 0, port_val / margin, np.inf)

    hit = (ann_income >= target_income)
    first = np.argmax(hit, axis=1)
    reached = hit.any(axis=1)
    first = np.where(reached, first + 1, np.nan)

    # Breach probabilities
    breach_35 = np.nanmean((ratio <= 3.5).any(axis=1))
    breach_30 = np.nanmean((ratio <= 3.0).any(axis=1))

    return {
        'median_month': float(np.nanmedian(first)),
        'p25_month': float(np.nanpercentile(first, 25)),
        'p75_month': float(np.nanpercentile(first, 75)),
        'prob_by_28': float(np.nanmean(first <= 28)),
        'prob_by_36': float(np.nanmean(first <= 36)),
        'breach_prob_le_3_5x': float(breach_35),
        'breach_prob_le_3_0x': float(breach_30),
        'expected_ratio_month_60': float(np.nanmean(ratio[:, -1])),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', type=float, default=100000.0)
    ap.add_argument('--contrib', type=float, default=13317.0)
    ap.add_argument('--expense', type=float, default=4500.0)
    ap.add_argument('--months', type=int, default=60)
    ap.add_argument('--runs', type=int, default=3000)
    ap.add_argument('--apr', type=float, default=0.10875)
    ap.add_argument('--out', default='docs/fin-guru/reports/drip-price-margin-sim.json')
    args = ap.parse_args()

    res = {
        'inputs': vars(args),
        'results': {}
    }
    for lbl, bump in [('base', 0.0), ('plus2k', 2000.0), ('plus5k', 5000.0)]:
        out = simulate(V2_WEIGHTS, args.contrib + bump, args.expense, args.target, args.months, args.runs, args.apr)
        res['results'][lbl] = out

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2))
    print(f"Wrote {args.out}")


if __name__ == '__main__':
    main()
