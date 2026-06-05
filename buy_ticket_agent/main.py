"""Command entry point for the buy-ticket agent scaffold."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from buy_ticket_agent.pipeline import run_smoke_for_cli
from buy_ticket_agent.secrets import SecretAccessError


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(
        description="Run buy-ticket agent scaffold commands.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run the scaffold smoke path and write draft/log/state artifacts.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute the buy-ticket agent CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.smoke:
        parser.print_help()
        return 2

    try:
        result = run_smoke_for_cli(project_root=Path.cwd())
    except SecretAccessError as exc:
        print(f"Secret access blocker: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
