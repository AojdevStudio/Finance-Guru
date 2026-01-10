#!/usr/bin/env python3
"""Get MSFT fundamental metrics for report generation."""

import yfinance as yf
from datetime import datetime

# Get MSFT data
msft = yf.Ticker("MSFT")
info = msft.info

# Calculate YTD performance
end_date = datetime.now()
start_of_year = datetime(end_date.year, 1, 1)
hist = msft.history(start=start_of_year, end=end_date)

if len(hist) > 0:
    ytd_return = ((hist["Close"][-1] - hist["Close"][0]) / hist["Close"][0]) * 100
else:
    ytd_return = 0

# Get key metrics
market_cap = info.get("marketCap", 0) / 1e12
pe_ratio = info.get("forwardPE", 0)
eps = info.get("trailingEps", 0)
div_yield = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
high_52w = info.get("fiftyTwoWeekHigh", 0)
low_52w = info.get("fiftyTwoWeekLow", 0)
avg_vol = info.get("averageVolume", 0)

print(f"Market Cap: ${market_cap:.2f}T")
print(f"P/E Ratio: {pe_ratio:.2f}")
print(f"EPS (TTM): ${eps:.2f}")
print(f"Dividend Yield: {div_yield:.2f}%")
print(f"YTD Return: {ytd_return:.2f}%")
print(f"52-Week High: ${high_52w:.2f}")
print(f"52-Week Low: ${low_52w:.2f}")
print(f"Avg Volume: {avg_vol:,}")
