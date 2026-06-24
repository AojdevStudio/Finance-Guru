#!/usr/bin/env python3
"""SnapTrade CLI for Finance Guru live-sync.

USAGE:
    # Proof of life: list connected accounts as JSON
    uv run python -m src.integrations.snaptrade.cli accounts --output json

    # Include read-only diagnostics needed before deleting CSV paths
    uv run python -m src.integrations.snaptrade.cli accounts --probe --output json

    # Create local account-routing config for later Sheet sync phases
    uv run python -m src.integrations.snaptrade.cli accounts \
        --write-config config/snaptrade-accounts.yaml

    # Phase 1 — sync positions / balances for config-enabled accounts ONLY.
    # Accounts with role=unassigned or enabled=false are refused, not fetched,
    # so the live path stays inert until an account is verified and routed.
    uv run python -m src.integrations.snaptrade.cli positions --output json
    uv run python -m src.integrations.snaptrade.cli balances --output json
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
    derive_margin_debt,
)
from src.integrations.snaptrade.models import (
    SnapTradeAccountConfig,
    SnapTradeAccountsConfig,
)

DEFAULT_CONFIG_PATH = Path("config/snaptrade-accounts.yaml")


def main(argv: list[str] | None = None) -> int:
    """Run the SnapTrade CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "accounts":
        return _accounts_command(args)
    if args.command in ("positions", "balances"):
        return _routing_command(args)
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

    for kind in ("positions", "balances"):
        sub = subparsers.add_parser(
            kind,
            help=f"Sync {kind} for config-enabled accounts only (read-only).",
        )
        sub.add_argument(
            "--output",
            choices=("text", "json", "yaml"),
            default="json",
            help="Output format. Defaults to json.",
        )
        sub.add_argument(
            "--config",
            default=str(DEFAULT_CONFIG_PATH),
            help=(
                "Account routing config. Defaults to config/snaptrade-accounts.yaml."
            ),
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


def _routing_command(args: argparse.Namespace) -> int:
    kind = args.command  # "positions" or "balances"
    try:
        config = SnapTradeAccountsConfig.from_path(Path(args.config))
    except (FileNotFoundError, ValueError) as exc:
        print(f"SnapTrade config error: {exc}", file=sys.stderr)
        return 1
    refused = [
        {
            "account_id": account.snaptrade_account_id,
            "name": account.name,
            "reason": account.refusal_reason,
        }
        for account in config.accounts
        if not account.is_syncable
    ]
    try:
        records = _fetch_routing_records(config.syncable, kind)
    except (SnapTradeAPIError, ValueError, RuntimeError) as exc:
        print(f"SnapTrade error: {exc}", file=sys.stderr)
        return 1
    payload: dict[str, Any] = {
        "kind": kind,
        "synced_account_count": len(records),
        "refused_account_count": len(refused),
        "accounts": records,
        "refused": refused,
    }
    _print_routing(payload, args.output)
    return 0


def _fetch_routing_records(
    syncable: list[SnapTradeAccountConfig], kind: str
) -> list[dict[str, Any]]:
    # The config gate is the only cutover switch: with no syncable account we
    # never touch the network, so the live path stays inert until verified.
    if not syncable:
        return []
    client = SnapTradeClientWrapper.from_env()
    records: list[dict[str, Any]] = []
    for account in syncable:
        record: dict[str, Any] = {
            "account_id": account.snaptrade_account_id,
            "name": account.name,
            "role": str(account.role),
        }
        if kind == "positions":
            record["positions"] = _account_positions(
                client, account.snaptrade_account_id
            )
        else:
            record["balances"] = _account_balances(client, account.snaptrade_account_id)
        records.append(record)
    return records


def _account_positions(
    client: SnapTradeClientWrapper, account_id: str
) -> list[dict[str, Any]]:
    # Equities come from the positions endpoint; options from a separate one.
    return client.get_positions(account_id) + client.get_options(account_id)


def _account_balances(
    client: SnapTradeClientWrapper, account_id: str
) -> dict[str, Any]:
    raw = client.get_balances(account_id)
    first = raw[0] if raw else {}
    equity = client.get_account_equity(account_id)
    margin_debt, gross_mv = derive_margin_debt(
        client.get_positions(account_id),
        client.get_options(account_id),
        equity,
    )
    return {
        "currency": first.get("currency"),
        "settled_cash": first.get("cash"),  # -> SPAXX row
        "buying_power": first.get("buying_power"),
        "account_equity": equity,
        "gross_market_value": gross_mv,
        "margin_debt": margin_debt,  # derived; SnapTrade omits it directly
    }


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


def _print_structured(payload: dict[str, Any], output_format: str) -> bool:
    """Emit json/yaml; return True when handled, False for text formats."""
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=False))
        return True
    if output_format == "yaml":
        print(yaml.safe_dump(payload, sort_keys=False))
        return True
    return False


def _print_routing(payload: dict[str, Any], output_format: str) -> None:
    if _print_structured(payload, output_format):
        return
    print(
        f"SnapTrade {payload['kind']}: "
        f"{payload['synced_account_count']} synced, "
        f"{payload['refused_account_count']} refused"
    )
    for account in payload["accounts"]:
        data = account[payload["kind"]]
        if payload["kind"] == "positions":
            print(f"- {account['name']} ({account['role']}): {len(data)} positions")
        else:
            print(
                f"- {account['name']} ({account['role']}): "
                f"cash={data.get('settled_cash')} margin_debt={data.get('margin_debt')}"
            )
    for refusal in payload["refused"]:
        print(f"- refused {refusal['name']}: {refusal['reason']}")


def _print_payload(payload: dict[str, Any], output_format: str) -> None:
    if _print_structured(payload, output_format):
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
