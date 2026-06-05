"""Tests for the deterministic Layer 3 pipeline bundle."""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path

from buy_ticket_agent import pipeline
from buy_ticket_agent.pipeline import (
    PIPELINE_TOOL_KEYS,
    Layer3Bundle,
    Layer3ProcessResult,
    Layer3ToolSpec,
    run,
)


def _freeze_run_time(monkeypatch) -> None:
    fixed_now = datetime(2026, 6, 5, 12, 0, 0, tzinfo=UTC)
    monkeypatch.setattr(pipeline, "_utc_now", lambda: fixed_now)


async def _successful_cli(
    spec: Layer3ToolSpec,
    *,
    project_root: Path,
    timeout_seconds: int,
) -> Layer3ProcessResult:
    del project_root, timeout_seconds
    return Layer3ProcessResult(
        returncode=0,
        stdout=json.dumps({"tool": spec.key}),
        stderr="SECRET_TOKEN=secret-value",
        duration_ms=8,
    )


def test_run_pipeline_exercises_all_five_cli_specs_for_two_tickers(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Pipeline bundle invokes all five Layer 3 CLIs for TSLA and SPY."""
    _freeze_run_time(monkeypatch)
    calls: list[Layer3ToolSpec] = []

    async def fake_cli(
        spec: Layer3ToolSpec,
        *,
        project_root: Path,
        timeout_seconds: int,
    ) -> Layer3ProcessResult:
        calls.append(spec)
        return await _successful_cli(
            spec,
            project_root=project_root,
            timeout_seconds=timeout_seconds,
        )

    monkeypatch.setattr(pipeline, "_run_cli_subprocess", fake_cli)

    bundle = run(["TSLA", "SPY"], project_root=tmp_path)

    Layer3Bundle.model_validate(bundle)
    assert [spec.key for spec in calls] == list(PIPELINE_TOOL_KEYS)
    assert bundle["status"] == "succeeded"
    assert bundle["primary_ticker"] == "TSLA"
    assert bundle["tickers"] == ["TSLA", "SPY"]
    assert set(PIPELINE_TOOL_KEYS).issubset(bundle)
    assert bundle["itc"]["data"] == {"tool": "itc"}
    assert bundle["risk"]["data"] == {"tool": "risk"}
    assert bundle["mom"]["data"] == {"tool": "mom"}
    assert bundle["vol"]["data"] == {"tool": "vol"}
    assert bundle["opt"]["data"] == {"tool": "opt"}

    commands = {spec.key: spec.logged_command for spec in calls}
    assert commands["itc"] == [
        "python",
        "src/analysis/itc_risk_cli.py",
        "TSLA",
        "--universe",
        "tradfi",
        "--output",
        "json",
        "--no-price",
    ]
    assert commands["risk"] == [
        "python",
        "src/analysis/risk_metrics_cli.py",
        "TSLA",
        "--days",
        "90",
        "--output",
        "json",
        "--benchmark",
        "SPY",
    ]
    assert commands["opt"][:5] == [
        "python",
        "src/strategies/optimizer_cli.py",
        "TSLA",
        "SPY",
        "--days",
    ]

    bundle_path = tmp_path / bundle["bundle_path"]
    state_db = tmp_path / bundle["state_db"]
    bundle_text = bundle_path.read_text()
    assert "SECRET_TOKEN" not in bundle_text
    assert "secret-value" not in bundle_text

    with sqlite3.connect(state_db) as conn:
        row = conn.execute(
            """
            SELECT status, primary_ticker, tickers_json, payload_json
            FROM layer3_bundles
            WHERE id = ?
            """,
            (bundle["run_id"],),
        ).fetchone()

    assert row[0] == "succeeded"
    assert row[1] == "TSLA"
    assert json.loads(row[2]) == ["TSLA", "SPY"]
    assert json.loads(row[3])["run_id"] == bundle["run_id"]


def test_run_pipeline_captures_cli_failure_without_aborting(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A failed CLI is captured with status while other tools continue."""
    _freeze_run_time(monkeypatch)

    async def fake_cli(
        spec: Layer3ToolSpec,
        *,
        project_root: Path,
        timeout_seconds: int,
    ) -> Layer3ProcessResult:
        del project_root, timeout_seconds
        if spec.key == "risk":
            return Layer3ProcessResult(
                returncode=7,
                stdout="SECRET_TOKEN=secret-value",
                stderr="private stderr output",
                duration_ms=11,
            )
        return Layer3ProcessResult(
            returncode=0,
            stdout=json.dumps({"tool": spec.key}),
            stderr="",
            duration_ms=7,
        )

    monkeypatch.setattr(pipeline, "_run_cli_subprocess", fake_cli)

    bundle = run(["TSLA", "SPY"], project_root=tmp_path)

    assert bundle["status"] == "partial"
    assert bundle["risk"]["status"] == "failed"
    assert bundle["risk"]["returncode"] == 7
    assert bundle["risk"]["error"] == "ProcessFailed"
    assert bundle["risk"]["data"] is None
    assert bundle["mom"]["status"] == "succeeded"
    assert bundle["vol"]["status"] == "succeeded"
    assert bundle["opt"]["status"] == "succeeded"

    bundle_text = (tmp_path / bundle["bundle_path"]).read_text()
    assert "SECRET_TOKEN" not in bundle_text
    assert "secret-value" not in bundle_text
    assert "private stderr output" not in bundle_text


def test_run_pipeline_five_ticker_universe_completes_under_sixty_seconds(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A five-ticker bundle path stays under the AOJ-460 local runtime budget."""
    _freeze_run_time(monkeypatch)
    monkeypatch.setattr(pipeline, "_run_cli_subprocess", _successful_cli)

    started = time.perf_counter()
    bundle = run(["TSLA", "SPY", "AAPL", "MSFT", "NVDA"], project_root=tmp_path)
    elapsed = time.perf_counter() - started

    assert elapsed < 60
    assert bundle["status"] == "succeeded"
    assert bundle["tickers"] == ["TSLA", "SPY", "AAPL", "MSFT", "NVDA"]
