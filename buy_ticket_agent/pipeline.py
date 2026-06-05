"""Smoke pipeline for the buy-ticket agent scaffold."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from buy_ticket_agent.config import SmokePaths
from buy_ticket_agent.notifier import NotificationResult, push_ticket_preview
from buy_ticket_agent.secrets import resolve_notification_config
from buy_ticket_agent.state import (
    initialize_state,
    record_smoke_failure,
    record_smoke_run,
)

SMOKE_TICKER = "SPY"
ITC_PROXY_TICKER = "SP500"
DISCLAIMER = (
    "For educational purposes only; not investment advice. Consult a licensed "
    "financial professional before acting. Loss of principal is possible."
)


@dataclass(frozen=True)
class CliEnvelope:
    """Captured result from the Layer 3 smoke CLI call."""

    command: list[str]
    status: str
    returncode: int
    stdout_chars: int
    stderr_chars: int
    error: str | None = None


@dataclass(frozen=True)
class SmokeResult:
    """Result envelope returned by a smoke run."""

    run_id: str
    ticket_id: str | None
    status: str
    draft_path: str | None
    log_path: str
    state_db: str
    notification: NotificationResult | None


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _output_length(output: str | bytes | None) -> int:
    if output is None:
        return 0
    return len(output)


def _trigger_context_from_env() -> dict[str, str] | None:
    source = os.getenv("BUY_TICKET_TRIGGER_SOURCE")
    if not source:
        return None

    context = {"source": source}
    optional_fields = {
        "BUY_TICKET_TRIGGER_AMOUNT": "amount",
        "BUY_TICKET_TRIGGER_ACCOUNT_KEY": "source_account_key",
        "BUY_TICKET_TRIGGER_TRANSACTION_KEY": "transaction_key",
    }
    for env_name, field_name in optional_fields.items():
        value = os.getenv(env_name)
        if value:
            context[field_name] = value
    return context


def run_layer3_smoke_cli(project_root: Path) -> CliEnvelope:
    """Invoke the existing ITC Risk CLI once for the smoke path."""
    command_args = (
        [
            ITC_PROXY_TICKER,
            "--universe",
            "tradfi",
            "--output",
            "json",
            "--no-price",
        ]
        if os.getenv("ITC_API_KEY")
        else ["--list-supported", "tradfi"]
    )
    run_command = [sys.executable, "src/analysis/itc_risk_cli.py", *command_args]
    logged_command = ["python", *run_command[1:]]
    try:
        result = subprocess.run(
            run_command,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired as exc:
        return CliEnvelope(
            command=logged_command,
            status="failed",
            returncode=-1,
            stdout_chars=_output_length(exc.stdout),
            stderr_chars=_output_length(exc.stderr),
            error="TimeoutExpired",
        )
    except FileNotFoundError:
        return CliEnvelope(
            command=logged_command,
            status="failed",
            returncode=-1,
            stdout_chars=0,
            stderr_chars=0,
            error="FileNotFoundError",
        )
    status = "succeeded" if result.returncode == 0 else "failed"
    return CliEnvelope(
        command=logged_command,
        status=status,
        returncode=result.returncode,
        stdout_chars=_output_length(result.stdout),
        stderr_chars=_output_length(result.stderr),
    )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _make_ticket_payload(
    *,
    run_id: str,
    ticket_id: str,
    created_at: str,
    cli_result: CliEnvelope,
    trigger_context: dict[str, str] | None,
) -> dict:
    payload = {
        "id": ticket_id,
        "run_id": run_id,
        "created_at": created_at,
        "mode": "shadow",
        "ticker": SMOKE_TICKER,
        "analysis_proxy": ITC_PROXY_TICKER,
        "status": "draft",
        "action": "review_only",
        "summary": "Smoke draft generated from a single Layer 3 CLI call.",
        "layer3": {
            "tool": "itc_risk_cli",
            "status": cli_result.status,
            "returncode": cli_result.returncode,
        },
        "disclaimer": DISCLAIMER,
    }
    if trigger_context is not None:
        payload["trigger"] = trigger_context
    return payload


def run_smoke(project_root: Path | None = None) -> SmokeResult:
    """Run the AOJ-458 end-to-end smoke path."""
    paths = SmokePaths.from_project_root(project_root)
    now = _utc_now()
    created_at = now.isoformat()
    run_id = f"smoke-{now:%Y%m%d}-{uuid4().hex[:8]}"
    ticket_id = f"ticket-{run_id}"

    notification_config = resolve_notification_config()
    trigger_context = _trigger_context_from_env()
    initialize_state(paths.state_db)
    cli_result = run_layer3_smoke_cli(paths.project_root)

    draft_path = paths.drafts_dir / f"{run_id}.json"
    log_path = paths.runs_dir / f"{run_id}.json"
    preview = f"{SMOKE_TICKER} shadow draft ready for review"

    if cli_result.status != "succeeded":
        status = "layer3_failed"
        log_payload = {
            "event": "buy_ticket_smoke_run",
            "run_id": run_id,
            "ticket_id": None,
            "created_at": created_at,
            "status": status,
            "draft_path": None,
            "state_db": _relative(paths.state_db, paths.project_root),
            "trigger": trigger_context,
            "layer3": asdict(cli_result),
            "notification": None,
        }
        _write_json(log_path, log_payload)
        record_smoke_failure(
            paths.state_db,
            run_id=run_id,
            created_at=created_at,
            status=status,
            log_path=log_path,
        )
        return SmokeResult(
            run_id=run_id,
            ticket_id=None,
            status=status,
            draft_path=None,
            log_path=_relative(log_path, paths.project_root),
            state_db=_relative(paths.state_db, paths.project_root),
            notification=None,
        )

    ticket_payload = _make_ticket_payload(
        run_id=run_id,
        ticket_id=ticket_id,
        created_at=created_at,
        cli_result=cli_result,
        trigger_context=trigger_context,
    )
    _write_json(draft_path, ticket_payload)

    notification = push_ticket_preview(
        notification_config,
        ticket_id=ticket_id,
        preview=preview,
    )
    status = (
        "completed"
        if notification.status in {"sent", "skipped"}
        else "notification_failed"
    )

    log_payload = {
        "event": "buy_ticket_smoke_run",
        "run_id": run_id,
        "ticket_id": ticket_id,
        "created_at": created_at,
        "status": status,
        "draft_path": _relative(draft_path, paths.project_root),
        "state_db": _relative(paths.state_db, paths.project_root),
        "trigger": trigger_context,
        "layer3": asdict(cli_result),
        "notification": asdict(notification),
    }
    _write_json(log_path, log_payload)
    record_smoke_run(
        paths.state_db,
        run_id=run_id,
        ticket_id=ticket_id,
        created_at=created_at,
        ticker=SMOKE_TICKER,
        status=status,
        draft_path=draft_path,
        log_path=log_path,
        preview=preview,
    )

    return SmokeResult(
        run_id=run_id,
        ticket_id=ticket_id,
        status=status,
        draft_path=_relative(draft_path, paths.project_root),
        log_path=_relative(log_path, paths.project_root),
        state_db=_relative(paths.state_db, paths.project_root),
        notification=notification,
    )


def run_smoke_for_cli(project_root: Path | None = None) -> SmokeResult:
    """CLI wrapper that surfaces BWS access failures to the caller."""
    return run_smoke(project_root=project_root)
