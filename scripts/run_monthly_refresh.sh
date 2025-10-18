#!/usr/bin/env bash
set -euo pipefail

# Monthly Finance Guru refresh
# - Updates yields, risk metrics, distribution trends, and alerts
# - Runs DRIP + price-path + margin risk simulation for 100k and 120k targets

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "[1/3] Monthly refresh snapshot..."
uv run python scripts/monthly_refresh.py

echo "[2/3] DRIP+price+margin sim (100k target)..."
uv run python scripts/sim_drip_price_margin.py --target 100000 --runs 1000 --months 60 --out docs/fin-guru/reports/drip-price-margin-sim-100k.json

echo "[3/3] DRIP+price+margin sim (120k target)..."
uv run python scripts/sim_drip_price_margin.py --target 120000 --runs 1000 --months 60 --out docs/fin-guru/reports/drip-price-margin-sim-120k.json

echo "Monthly refresh complete. Reports in docs/fin-guru/reports/"

