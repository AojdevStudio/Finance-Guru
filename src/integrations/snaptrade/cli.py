#!/usr/bin/env python3
"""SnapTrade CLI for Finance Guru live-sync Phase 0.

USAGE:
    # Proof of life: list connected accounts as JSON
    uv run python -m src.integrations.snaptrade.cli accounts --output json

    # Include read-only diagnostics needed before deleting CSV paths
    uv run python -m src.integrations.snaptrade.cli accounts --probe --output json

    # Create local account-routing config for later Sheet sync phases
    uv run python -m src.integrations.snaptrade.cli accounts \
        --write-config config/snaptrade-accounts.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from src.integrations.snaptrade.client import (
    SnapTradeAPIError,
    SnapTradeClientWrapper,
)
from src.integrations.snaptrade.models import SnapTradeAccountsConfig

DEFAULT_CONFIG_PATH = Path("config/snaptrade-accounts.yaml")


def main(argv: list[str] | None = None) -> int:
    """Run the SnapTrade CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "accounts":
        return _accounts_command(args)
    parser.print_help(sys.stderr)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Finance Guru™ SnapTrade read-only CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    accounts = subparsers.add_parser(
        "accounts",
        help="List linked SnapTrade accounts and optionally write routing config.",
    )
    accounts.add_argument(
        "--output",
        choices=("text", "json", "yaml"),
        default="text",
        help="Output format. Defaults to text.",
    )
    accounts.add_argument(
        "--probe",
        action="store_true",
        help="Also fetch per-account balance/position diagnostics. Read-only.",
    )
    accounts.add_argument(
        "--write-config",
        nargs="?",
        const=str(DEFAULT_CONFIG_PATH),
        help=(
            "Write local account routing config. Defaults to "
            "config/snaptrade-accounts.yaml when no path is supplied."
        ),
    )
    accounts.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing config when used with --write-config.",
    )
    return parser


def _accounts_command(args: argparse.Namespace) -> int:
    try:
        client = SnapTradeClientWrapper.from_env()
        accounts = client.list_accounts()
        account_payloads: list[dict[str, Any]] = [
            account.model_dump(exclude={"raw"}) for account in accounts
        ]
        probes: list[dict[str, Any]] = []
        if args.probe:
            for account in accounts:
                probes.append(client.probe_account(account.id))
        payload: dict[str, Any] = {
            "account_count": len(accounts),
            "accounts": account_payloads,
        }
        if probes:
            payload["probes"] = probes
            payload["phase_0_findings"] = _phase_0_findings(account_payloads, probes)
        if args.write_config:
            config_path = Path(args.write_config)
            _write_config(config_path, accounts, force=args.force)
            payload["config_written"] = str(config_path)
        _print_payload(payload, args.output)
        return 0
    except (SnapTradeAPIError, ValueError, RuntimeError) as exc:
        print(f"SnapTrade error: {exc}", file=sys.stderr)
        return 1


def _write_config(path: Path, accounts: list[Any], force: bool) -> None:
    if path.exists() and not force:
        raise ValueError(f"Config already exists: {path}. Use --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    config = SnapTradeAccountsConfig.from_accounts(accounts)
    path.write_text(
        yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )


def _phase_0_findings(
    accounts: list[dict[str, Any]], probes: list[dict[str, Any]]
) -> dict[str, Any]:
    account_types = sorted(
        {str(account.get("type") or "unknown") for account in accounts}
    )
    spaxx_accounts = [
        probe["account_id"] for probe in probes if probe["spaxx_as_position"]
    ]
    avg_present = sum(probe["average_purchase_price_present_count"] for probe in probes)
    avg_missing = sum(probe["average_purchase_price_missing_count"] for probe in probes)
    balance_rows = sum(probe["balance_count"] for probe in probes)
    return {
        "account_types_seen": account_types,
        "balance_rows_seen": balance_rows,
        "spaxx_appears_as_position": len(spaxx_accounts) > 0,
        "spaxx_account_ids": spaxx_accounts,
        "average_purchase_price_present_count": avg_present,
        "average_purchase_price_missing_count": avg_missing,
    }


def _print_payload(payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=False))
        return
    if output_format == "yaml":
        print(yaml.safe_dump(payload, sort_keys=False))
        return
    print(f"SnapTrade accounts: {payload['account_count']}")
    for account in payload["accounts"]:
        print(
            "- "
            f"{account['name'] or '(unnamed)'} | "
            f"{account['institution_name'] or '(institution unknown)'} | "
            f"type={account['type'] or 'unknown'} | "
            f"id={account['id']}"
        )
    if "phase_0_findings" in payload:
        findings = payload["phase_0_findings"]
        print("\nPhase 0 findings:")
        print(f"- Account types seen: {', '.join(findings['account_types_seen'])}")
        print(f"- Balance rows seen: {findings['balance_rows_seen']}")
        print(f"- SPAXX as position: {findings['spaxx_appears_as_position']}")
        print(
            "- Average purchase price present/missing: "
            f"{findings['average_purchase_price_present_count']}/"
            f"{findings['average_purchase_price_missing_count']}"
        )
    if "config_written" in payload:
        print(f"\nConfig written: {payload['config_written']}")


if __name__ == "__main__":
    raise SystemExit(main())
