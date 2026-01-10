#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path
import subprocess

import numpy as np
import yfinance as yf


V2_TICKERS = [
    "CLM","CRF","QQQI","SPYI","JEPQ","BDJ","ETY","ETV","UTG","BST"
]


def ttm_yield(ticker):
    t = yf.Ticker(ticker)
    hist = t.history(period="1d")
    px = float(hist["Close"].iloc[-1]) if not hist.empty else np.nan
    div = t.dividends
    if div is None or div.empty or np.isnan(px):
        return np.nan
    # Sum distributions over last 365 calendar days
    import pandas as pd
    cutoff = pd.Timestamp.today(tz=div.index.tz) - pd.Timedelta(days=365)
    recent = div[div.index >= cutoff]
    div_sum = float(recent.sum()) if not recent.empty else 0.0
    return div_sum/px if px>0 else np.nan


def three_month_vs_twelve_month_avg(ticker):
    t = yf.Ticker(ticker)
    div = t.dividends
    if div is None or div.empty:
        return np.nan, np.nan
    df = div.to_frame('div')
    df['m'] = df.index.to_period('M')
    m = df.groupby('m')['div'].sum()
    if len(m) < 3:
        return np.nan, np.nan
    m3 = float(m.tail(3).mean())
    m12 = float(m.tail(12).mean()) if len(m)>=12 else float(m.mean())
    return m3, m12


def risk_metrics_cli(ticker):
    # Call internal CLI to compute 252-day metrics
    cmd = ["uv","run","python","src/analysis/risk_metrics_cli.py",ticker,"--days","252","--benchmark","SPY","--output","json"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    # Extract JSON blob from mixed output
    txt = out.stdout
    js = txt[txt.find('{'):txt.rfind('}')+1]
    try:
        return json.loads(js)
    except Exception:
        return {}


def drawdown_90d(ticker):
    # Approximate 90-day max drawdown from daily closes
    t = yf.Ticker(ticker)
    h = t.history(period="6mo")
    if h.empty:
        return np.nan
    px = h['Close'].values[-90:]
    if len(px) < 30:
        return np.nan
    peak = -np.inf
    maxdd = 0.0
    for p in px:
        peak = max(peak, p)
        dd = (p/peak) - 1.0
        maxdd = min(maxdd, dd)
    return float(maxdd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--outdir', default='docs/fin-guru/reports')
    ap.add_argument('--margin-apr', type=float, default=0.10875)
    args = ap.parse_args()

    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    report = {
        'date': today,
        'margin_apr': args.margin_apr,
        'tickers': {}
    }
    alerts = []

    for t in V2_TICKERS:
        yld = ttm_yield(t)
        m3, m12 = three_month_vs_twelve_month_avg(t)
        rm = risk_metrics_cli(t)
        dd90 = drawdown_90d(t)
        report['tickers'][t] = {
            'ttm_yield': yld,
            'm3_avg_div': m3,
            'm12_avg_div': m12,
            'risk_metrics': rm,
            'dd_90d': dd90,
        }
        # Alerts
        # Coverage buffer check: ttm_yield - apr >= 0.06
        if yld == yld and (yld - args.margin_apr) < 0.06:
            alerts.append(f"Coverage buffer low: {t} (TTM {yld:.2%} vs APR {args.margin_apr:.2%})")
        # Distribution cut check
        if m3 == m3 and m12 == m12 and m12>0 and (m3/m12) < 0.75:
            alerts.append(f"Distribution down >25%: {t} (3m/12m = {m3/m12:.2f})")
        # 90d drawdown check
        if dd90 == dd90 and dd90 < -0.25:
            alerts.append(f"90d MaxDD >25%: {t} ({dd90:.2%})")

    report['alerts'] = alerts

    # Write JSON and Markdown
    out_json = Path(args.outdir) / f"monthly-refresh-{today}.json"
    out_md = Path(args.outdir) / f"monthly-refresh-{today}.md"
    out_json.write_text(json.dumps(report, indent=2))

    lines = [f"# Monthly Refresh – {today}", "", f"Margin APR: {args.margin_apr:.2%}", "", "## Alerts"]
    if alerts:
        for a in alerts:
            lines.append(f"- {a}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("| Ticker | TTM Yield | 3m/12m Div Ratio | Sharpe | MaxDD | 90d MaxDD |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for t, d in report['tickers'].items():
        y = d['ttm_yield']
        ratio = (d['m3_avg_div']/d['m12_avg_div']) if (d['m3_avg_div'] and d['m12_avg_div']) else np.nan
        sharpe = d['risk_metrics'].get('sharpe_ratio') if d['risk_metrics'] else None
        mdd = d['risk_metrics'].get('max_drawdown') if d['risk_metrics'] else None
        dd90 = d['dd_90d']
        y_s = f"{y:.2%}" if y==y else ""
        r_s = f"{ratio:.2f}" if ratio==ratio else ""
        sh_s = f"{sharpe:.2f}" if sharpe is not None else ""
        mdd_s = f"{mdd:.2%}" if mdd is not None else ""
        dd90_s = f"{dd90:.2%}" if dd90==dd90 else ""
        lines.append(f"| {t} | {y_s} | {r_s} | {sh_s} | {mdd_s} | {dd90_s} |")

    out_md.write_text("\n".join(lines))
    print(f"Wrote {out_json} and {out_md}")


if __name__ == "__main__":
    main()
