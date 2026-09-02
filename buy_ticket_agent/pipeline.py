"""Smoke pipeline for the buy-ticket agent scaffold."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from buy_ticket_agent.config import SmokePaths
from buy_ticket_agent.notifier import NotificationResult, push_ticket_preview
from buy_ticket_agent.secrets import resolve_notification_config
from buy_ticket_agent.state import (
    initialize_state,
    record_layer3_bundle,
    record_smoke_failure,
    record_smoke_run,
)
from src.config.instance_paths import InstancePaths

SMOKE_TICKER = "SPY"
ITC_PROXY_TICKER = "SP500"
DISCLAIMER = (
    "For educational purposes only; not investment advice. Consult a licensed "
    "financial professional before acting. Loss of principal is possible."
)
Layer3ToolKey = Literal["itc", "risk", "mom", "vol", "opt"]
Layer3ToolStatus = Literal["succeeded", "failed"]
Layer3BundleStatus = Literal["succeeded", "partial", "failed"]
PIPELINE_TOOL_KEYS: tuple[Layer3ToolKey, ...] = ("itc", "risk", "mom", "vol", "opt")


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
class DraftPersistenceResult:
    """Durability outcome for the smoke draft, independent of delivery."""

    status: Literal["created", "reused", "not-created"]


@dataclass(frozen=True)
class SmokeResult:
    """Result envelope returned by a smoke run."""

    run_id: str
    ticket_id: str | None
    status: Literal["completed", "layer3_failed"]
    draft_path: str | None
    log_path: str
    state_db: str
    notification: NotificationResult | None
    persistence: DraftPersistenceResult | None = None


@dataclass(frozen=True)
class Layer3ToolSpec:
    """Command metadata for one deterministic Layer 3 tool call."""

    key: Layer3ToolKey
    command: list[str]
    logged_command: list[str]


@dataclass(frozen=True)
class Layer3ProcessResult:
    """Raw subprocess outcome before JSON parsing."""

    returncode: int
    stdout: str
    stderr: str
    duration_ms: int
    error: str | None = None


class Layer3ToolResult(BaseModel):
    """Sanitized result envelope for one Layer 3 CLI."""

    model_config = ConfigDict(extra="forbid")

    key: Layer3ToolKey
    command: list[str]
    status: Layer3ToolStatus
    returncode: int
    duration_ms: int
    stdout_chars: int
    stderr_chars: int
    data: Any | None = None
    error: str | None = None


class Layer3Bundle(BaseModel):
    """Deterministic JSON bundle consumed by later ticket-generation layers."""

    model_config = ConfigDict(extra="forbid")

    event: Literal["layer3_pipeline_bundle"] = "layer3_pipeline_bundle"
    run_id: str
    created_at: str
    status: Layer3BundleStatus
    primary_ticker: str
    tickers: list[str]
    universe: Literal["crypto", "tradfi"]
    bundle_path: str
    state_db: str
    itc: Layer3ToolResult
    risk: Layer3ToolResult
    mom: Layer3ToolResult
    vol: Layer3ToolResult
    opt: Layer3ToolResult


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _resolve_smoke_paths(
    instance_paths: InstancePaths | None,
    project_root: Path | None,
) -> SmokePaths:
    """Resolve instance storage while retaining a source-root test override."""
    if instance_paths is None and project_root is not None:
        instance_paths = InstancePaths(root=project_root.resolve())
    paths = SmokePaths.from_instance(instance_paths)
    if project_root is None:
        return paths
    return paths.model_copy(update={"project_root": project_root.resolve()})


def _output_length(output: str | bytes | None) -> int:
    if output is None:
        return 0
    return len(output)


def _decode_output(output: bytes | str | None) -> str:
    """Decode subprocess output without raising on malformed bytes."""
    if output is None:
        return ""
    if isinstance(output, str):
        return output
    return output.decode("utf-8", errors="replace")


def _normalize_tickers(tickers: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Normalize ticker input while preserving first-seen order."""
    normalized: list[str] = []
    seen: set[str] = set()
    for ticker in tickers:
        value = ticker.strip().upper()
        if not value or value in seen:
            continue
        normalized.append(value)
        seen.add(value)
    if not normalized:
        raise ValueError("At least one ticker is required")
    return tuple(normalized)


def _validate_universe(universe: str) -> Literal["crypto", "tradfi"]:
    """Validate the ITC universe value used by the Layer 3 bundle."""
    if universe == "crypto":
        return "crypto"
    if universe == "tradfi":
        return "tradfi"
    raise ValueError("universe must be 'crypto' or 'tradfi'")


def _logged_command(command: list[str]) -> list[str]:
    """Return a stable command representation without local interpreter paths."""
    return ["python", *command[1:]]


def _build_layer3_specs(
    tickers: tuple[str, ...],
    *,
    universe: Literal["crypto", "tradfi"],
    days: int,
    optimizer_days: int,
) -> tuple[Layer3ToolSpec, ...]:
    """Build the fixed AOJ-460 Layer 3 CLI command matrix."""
    primary_ticker = tickers[0]
    benchmark = next(
        (ticker for ticker in tickers[1:] if ticker != primary_ticker), None
    )

    itc_command = [
        sys.executable,
        "src/analysis/itc_risk_cli.py",
        primary_ticker,
        "--universe",
        universe,
        "--output",
        "json",
        "--no-price",
    ]
    risk_command = [
        sys.executable,
        "src/analysis/risk_metrics_cli.py",
        primary_ticker,
        "--days",
        str(days),
        "--output",
        "json",
    ]
    if benchmark:
        risk_command.extend(["--benchmark", benchmark])

    commands: dict[Layer3ToolKey, list[str]] = {
        "itc": itc_command,
        "risk": risk_command,
        "mom": [
            sys.executable,
            "src/utils/momentum_cli.py",
            primary_ticker,
            "--days",
            str(days),
            "--output",
            "json",
        ],
        "vol": [
            sys.executable,
            "src/utils/volatility_cli.py",
            primary_ticker,
            "--days",
            str(days),
            "--output",
            "json",
        ],
        "opt": [
            sys.executable,
            "src/strategies/optimizer_cli.py",
            *tickers,
            "--days",
            str(optimizer_days),
            "--method",
            "max_sharpe",
            "--output",
            "json",
        ],
    }
    return tuple(
        Layer3ToolSpec(
            key=key,
            command=commands[key],
            logged_command=_logged_command(commands[key]),
        )
        for key in PIPELINE_TOOL_KEYS
    )


async def _run_cli_subprocess(
    spec: Layer3ToolSpec,
    *,
    project_root: Path,
    timeout_seconds: int,
) -> Layer3ProcessResult:
    """Run one Layer 3 CLI and capture only scrub-safe process metadata."""
    started = time.perf_counter()
    try:
        process = await asyncio.create_subprocess_exec(
            *spec.command,
            cwd=project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
        except TimeoutError:
            process.kill()
            stdout, stderr = await process.communicate()
            return Layer3ProcessResult(
                returncode=-1,
                stdout=_decode_output(stdout),
                stderr=_decode_output(stderr),
                duration_ms=int((time.perf_counter() - started) * 1000),
                error="TimeoutExpired",
            )
    except FileNotFoundError:
        return Layer3ProcessResult(
            returncode=-1,
            stdout="",
            stderr="",
            duration_ms=int((time.perf_counter() - started) * 1000),
            error="FileNotFoundError",
        )
    except Exception as exc:
        return Layer3ProcessResult(
            returncode=-1,
            stdout="",
            stderr="",
            duration_ms=int((time.perf_counter() - started) * 1000),
            error=type(exc).__name__,
        )

    return Layer3ProcessResult(
        returncode=process.returncode if process.returncode is not None else -1,
        stdout=_decode_output(stdout),
        stderr=_decode_output(stderr),
        duration_ms=int((time.perf_counter() - started) * 1000),
    )


def _make_failed_tool_result(
    spec: Layer3ToolSpec,
    process_result: Layer3ProcessResult,
    *,
    error: str,
) -> Layer3ToolResult:
    """Build a scrubbed failed tool envelope."""
    return Layer3ToolResult(
        key=spec.key,
        command=spec.logged_command,
        status="failed",
        returncode=process_result.returncode,
        duration_ms=process_result.duration_ms,
        stdout_chars=_output_length(process_result.stdout),
        stderr_chars=_output_length(process_result.stderr),
        error=error,
    )


async def _run_layer3_tool(
    spec: Layer3ToolSpec,
    *,
    project_root: Path,
    timeout_seconds: int,
) -> Layer3ToolResult:
    """Run one Layer 3 CLI and parse successful JSON output."""
    process_result = await _run_cli_subprocess(
        spec,
        project_root=project_root,
        timeout_seconds=timeout_seconds,
    )
    if process_result.error is not None:
        return _make_failed_tool_result(
            spec, process_result, error=process_result.error
        )
    if process_result.returncode != 0:
        return _make_failed_tool_result(spec, process_result, error="ProcessFailed")
    if not process_result.stdout.strip():
        return _make_failed_tool_result(spec, process_result, error="NoJsonOutput")

    try:
        data = json.loads(process_result.stdout)
    except json.JSONDecodeError:
        return _make_failed_tool_result(spec, process_result, error="JSONDecodeError")

    return Layer3ToolResult(
        key=spec.key,
        command=spec.logged_command,
        status="succeeded",
        returncode=process_result.returncode,
        duration_ms=process_result.duration_ms,
        stdout_chars=_output_length(process_result.stdout),
        stderr_chars=_output_length(process_result.stderr),
        data=data,
    )


async def _run_layer3_tools(
    specs: tuple[Layer3ToolSpec, ...],
    *,
    project_root: Path,
    timeout_seconds: int,
) -> dict[Layer3ToolKey, Layer3ToolResult]:
    """Run the Layer 3 CLI matrix concurrently and return ordered results."""
    results = await asyncio.gather(
        *(
            _run_layer3_tool(
                spec,
                project_root=project_root,
                timeout_seconds=timeout_seconds,
            )
            for spec in specs
        )
    )
    return {result.key: result for result in results}


def _bundle_status(
    results: dict[Layer3ToolKey, Layer3ToolResult],
) -> Layer3BundleStatus:
    """Summarize per-tool statuses into a bundle-level status."""
    succeeded = sum(1 for result in results.values() if result.status == "succeeded")
    if succeeded == len(results):
        return "succeeded"
    if succeeded == 0:
        return "failed"
    return "partial"


def run(
    tickers: list[str] | tuple[str, ...],
    *,
    universe: str = "tradfi",
    instance_paths: InstancePaths | None = None,
    project_root: Path | None = None,
    timeout_seconds: int = 55,
    days: int = 90,
    optimizer_days: int = 252,
) -> dict[str, Any]:
    """Run the deterministic AOJ-460 Layer 3 pipeline and persist its bundle."""
    normalized_tickers = _normalize_tickers(tickers)
    validated_universe = _validate_universe(universe)
    paths = _resolve_smoke_paths(instance_paths, project_root)
    now = _utc_now()
    created_at = now.isoformat()
    run_id = f"layer3-{now:%Y%m%d}-{uuid4().hex[:8]}"
    bundle_path = paths.bundles_dir / f"{run_id}.json"
    specs = _build_layer3_specs(
        normalized_tickers,
        universe=validated_universe,
        days=days,
        optimizer_days=optimizer_days,
    )

    initialize_state(paths.state_db)
    tool_results = asyncio.run(
        _run_layer3_tools(
            specs,
            project_root=paths.project_root,
            timeout_seconds=timeout_seconds,
        )
    )
    bundle = Layer3Bundle(
        run_id=run_id,
        created_at=created_at,
        status=_bundle_status(tool_results),
        primary_ticker=normalized_tickers[0],
        tickers=list(normalized_tickers),
        universe=validated_universe,
        bundle_path=_relative(bundle_path, paths.instance_root),
        state_db=_relative(paths.state_db, paths.instance_root),
        itc=tool_results["itc"],
        risk=tool_results["risk"],
        mom=tool_results["mom"],
        vol=tool_results["vol"],
        opt=tool_results["opt"],
    )
    payload = bundle.model_dump(mode="json")
    _write_json(bundle_path, payload)
    record_layer3_bundle(
        paths.state_db,
        run_id=run_id,
        created_at=created_at,
        primary_ticker=normalized_tickers[0],
        tickers=normalized_tickers,
        status=bundle.status,
        bundle_path=_relative(bundle_path, paths.instance_root),
        payload=payload,
    )
    return payload


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


def _smoke_run_id(
    now: datetime,
    trigger_context: dict[str, str] | None,
) -> str:
    """Derive one logical run identity for each upstream trigger."""
    if trigger_context is not None:
        source = trigger_context.get("source")
        transaction_key = trigger_context.get("transaction_key")
        if source and transaction_key:
            identity = json.dumps(
                [source, transaction_key],
                ensure_ascii=True,
                separators=(",", ":"),
            )
            digest = hashlib.sha256(identity.encode()).hexdigest()[:16]
            return f"smoke-trigger-{digest}"
    return f"smoke-{now:%Y%m%d}-{uuid4().hex[:8]}"


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


def _load_persisted_smoke(
    draft_path: Path,
    log_path: Path,
    *,
    run_id: str,
    ticket_id: str,
) -> tuple[str, CliEnvelope]:
    """Load and validate the durable inputs needed for a notification retry."""
    try:
        draft = json.loads(draft_path.read_text())
        log = json.loads(log_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Persisted smoke artifacts are unreadable") from exc
    if not isinstance(draft, dict) or not isinstance(log, dict):
        raise ValueError("Persisted smoke artifacts must be JSON objects")
    if draft.get("run_id") != run_id or draft.get("id") != ticket_id:
        raise ValueError("Persisted smoke draft identity does not match trigger")
    created_at = draft.get("created_at")
    layer3 = log.get("layer3")
    if not isinstance(created_at, str) or not isinstance(layer3, dict):
        raise ValueError("Persisted smoke artifacts are incomplete")
    try:
        cli_result = CliEnvelope(**layer3)
    except TypeError as exc:
        raise ValueError("Persisted Layer 3 result is malformed") from exc
    if cli_result.status != "succeeded":
        raise ValueError("Persisted smoke draft lacks successful Layer 3 evidence")
    return created_at, cli_result


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


def run_smoke(
    instance_paths: InstancePaths | None = None,
    project_root: Path | None = None,
) -> SmokeResult:
    """Run the AOJ-458 end-to-end smoke path."""
    paths = _resolve_smoke_paths(instance_paths, project_root)
    now = _utc_now()
    notification_config = resolve_notification_config()
    trigger_context = _trigger_context_from_env()
    created_at = now.isoformat()
    run_id = _smoke_run_id(now, trigger_context)
    ticket_id = f"ticket-{run_id}"
    initialize_state(paths.state_db)

    draft_path = paths.drafts_dir / f"{run_id}.json"
    log_path = paths.runs_dir / f"{run_id}.json"
    preview = f"{SMOKE_TICKER} shadow draft ready for review"
    if draft_path.exists():
        created_at, cli_result = _load_persisted_smoke(
            draft_path,
            log_path,
            run_id=run_id,
            ticket_id=ticket_id,
        )
        persistence = DraftPersistenceResult(status="reused")
    else:
        cli_result = run_layer3_smoke_cli(paths.project_root)
        persistence = DraftPersistenceResult(status="not-created")

    if cli_result.status != "succeeded":
        failure_status: Literal["layer3_failed"] = "layer3_failed"
        log_payload = {
            "event": "buy_ticket_smoke_run",
            "run_id": run_id,
            "ticket_id": None,
            "created_at": created_at,
            "status": failure_status,
            "draft_path": None,
            "state_db": _relative(paths.state_db, paths.instance_root),
            "trigger": trigger_context,
            "layer3": asdict(cli_result),
            "persistence": asdict(persistence),
            "notification": None,
        }
        _write_json(log_path, log_payload)
        record_smoke_failure(
            paths.state_db,
            run_id=run_id,
            created_at=created_at,
            status=failure_status,
            log_path=log_path,
        )
        return SmokeResult(
            run_id=run_id,
            ticket_id=None,
            status=failure_status,
            draft_path=None,
            log_path=_relative(log_path, paths.instance_root),
            state_db=_relative(paths.state_db, paths.instance_root),
            notification=None,
            persistence=persistence,
        )

    if persistence.status == "not-created":
        ticket_payload = _make_ticket_payload(
            run_id=run_id,
            ticket_id=ticket_id,
            created_at=created_at,
            cli_result=cli_result,
            trigger_context=trigger_context,
        )
        _write_json(draft_path, ticket_payload)
        persistence = DraftPersistenceResult(status="created")

    notification = push_ticket_preview(
        notification_config,
        ticket_id=ticket_id,
        preview=preview,
    )
    success_status: Literal["completed"] = "completed"

    log_payload = {
        "event": "buy_ticket_smoke_run",
        "run_id": run_id,
        "ticket_id": ticket_id,
        "created_at": created_at,
        "status": success_status,
        "draft_path": _relative(draft_path, paths.instance_root),
        "state_db": _relative(paths.state_db, paths.instance_root),
        "trigger": trigger_context,
        "layer3": asdict(cli_result),
        "persistence": asdict(persistence),
        "notification": asdict(notification),
    }
    _write_json(log_path, log_payload)
    record_smoke_run(
        paths.state_db,
        run_id=run_id,
        ticket_id=ticket_id,
        created_at=created_at,
        ticker=SMOKE_TICKER,
        status=success_status,
        draft_path=draft_path,
        log_path=log_path,
        preview=preview,
    )

    return SmokeResult(
        run_id=run_id,
        ticket_id=ticket_id,
        status=success_status,
        draft_path=_relative(draft_path, paths.instance_root),
        log_path=_relative(log_path, paths.instance_root),
        state_db=_relative(paths.state_db, paths.instance_root),
        notification=notification,
        persistence=persistence,
    )


def run_smoke_for_cli(
    instance_paths: InstancePaths | None = None,
    project_root: Path | None = None,
) -> SmokeResult:
    """CLI wrapper that surfaces BWS access failures to the caller."""
    return run_smoke(instance_paths=instance_paths, project_root=project_root)
