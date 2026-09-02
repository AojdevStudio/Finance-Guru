"""CLI interface for validated margin-health metrics."""

from __future__ import annotations

import argparse
import json

from src.analysis.margin_metrics import (
    SUPPORTED_MARGIN_SOURCES,
    metrics_from_runtime,
    parse_money,
    parse_rate,
)


def main(argv: list[str] | None = None) -> int:
    """Calculate and print current margin-health metrics as JSON."""
    parser = argparse.ArgumentParser(description="Calculate live margin health metrics")
    parser.add_argument(
        "--source",
        choices=SUPPORTED_MARGIN_SOURCES,
        default="db",
        help=(
            "Balance source. Defaults to the local DB snapshot (sync-first store); "
            "'snaptrade' reads the API live; 'csv' reads a Fidelity export."
        ),
    )
    parser.add_argument("--csv", help="Specific Fidelity balances CSV to read")
    parser.add_argument(
        "--annual-rate",
        type=parse_rate,
        help="Annual margin rate as decimal or percent; defaults to .env",
    )
    parser.add_argument(
        "--monthly-dividend-income",
        type=parse_money,
        help=(
            "Current monthly dividend income; defaults to "
            "FG_DIVIDEND_MONTHLY_INCOME if set"
        ),
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    args = parser.parse_args(argv)

    metrics = metrics_from_runtime(
        source=args.source,
        csv_path=args.csv,
        annual_rate=args.annual_rate,
        monthly_dividend_income=args.monthly_dividend_income,
    )
    print(
        json.dumps(
            metrics.model_dump(mode="json"),
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
