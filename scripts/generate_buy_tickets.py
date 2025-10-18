#!/usr/bin/env python3
import argparse
from datetime import date
from pathlib import Path

import yfinance as yf


V2_WEIGHTS = {
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


def fetch_prices(tickers):
    prices = {}
    for t in tickers:
        hist = yf.Ticker(t).history(period="1d")
        prices[t] = float(hist["Close"][-1]) if not hist.empty else None
    return prices


def format_ticket(contrib, prices, weights):
    lines = []
    lines.append(f"# Buy Ticket – DRIP v2 Mix | ${contrib:,.0f}/mo")
    lines.append(f"Date: {date.today().isoformat()}")
    lines.append("")
    lines.append("| Ticker | Weight | $ Amount | Price | Shares |")
    lines.append("|---|---:|---:|---:|---:|")
    for t, w in weights.items():
        amt = contrib * w
        px = prices.get(t)
        sh = (amt / px) if px else 0.0
        lines.append(f"| {t} | {w:.2%} | ${amt:,.2f} | ${px:,.2f} | {sh:.4f} |")
    total = sum(contrib * w for w in weights.values())
    lines.append("|")
    lines.append(f"| TOTAL | 100% | ${total:,.2f} |  |  |")
    lines.append("")
    lines.append("Notes: Fractional shares assumed; DRIP enabled on all positions.")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--outdir", default="docs/fin-guru/tickets", help="Output folder for tickets")
    p.add_argument("--base", type=float, default=13317.0)
    p.add_argument("--plus2k", type=float, default=15317.0)
    p.add_argument("--plus5k", type=float, default=18317.0)
    args = p.parse_args()

    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    prices = fetch_prices(V2_WEIGHTS.keys())

    today = date.today().isoformat()
    tickets = [
        (args.base, f"buy-ticket-{today}-v2-base.md"),
        (args.plus2k, f"buy-ticket-{today}-v2-plus2k.md"),
        (args.plus5k, f"buy-ticket-{today}-v2-plus5k.md"),
    ]

    for contrib, filename in tickets:
        content = format_ticket(contrib, prices, V2_WEIGHTS)
        (Path(args.outdir) / filename).write_text(content)

    print(f"Wrote tickets to {args.outdir}")


if __name__ == "__main__":
    main()

