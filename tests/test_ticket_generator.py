"""Tests for AOJ-461 Claude buy-ticket generation."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from buy_ticket_agent import config
from buy_ticket_agent.ticket_generator import generate
from buy_ticket_agent.ticket_models import BuyTicket, PortfolioState
from src.config.instance_paths import InstancePaths


def _ticket_payload() -> dict[str, Any]:
    return {
        "strategy_name": "AOJ-461 acceptance ticket",
        "generated_on": "2026-06-08",
        "generated_by": "strategy-advisor",
        "portfolio_context_date": "2026-06-08",
        "deployment_amount": 10000.0,
        "cash_available": 15000.0,
        "remaining_cash_buffer": 5000.0,
        "price_snapshot_as_of": "2026-06-08T15:00:00Z",
        "itc_applicability": "supported",
        "itc_risk_score": 0.42,
        "allocations": [
            {
                "ticker": "TSLA",
                "category": "Growth",
                "weight": 0.25,
                "amount": 2500.0,
                "price": 250.0,
                "shares": 10.0,
            },
            {
                "ticker": "PLTR",
                "category": "Growth",
                "weight": 0.25,
                "amount": 2500.0,
                "price": 50.0,
                "shares": 50.0,
            },
            {
                "ticker": "SPY",
                "category": "Index",
                "weight": 0.50,
                "amount": 5000.0,
                "price": 500.0,
                "shares": 10.0,
            },
        ],
        "strategy_rationale": ["Blend growth names with broad index exposure."],
        "risk_notes": ["All hard guardrails are below rejection thresholds."],
        "sources": ["Layer 3 deterministic bundle"],
        "assumptions": ["Fractional shares supported."],
        "progress_tracking": "Month 1",
        "educational_notice": (
            "For educational purposes only; not investment advice. Consult a "
            "licensed financial professional before acting. Loss of principal "
            "is possible."
        ),
    }


def _layer3_bundle() -> dict[str, Any]:
    tool_result = {
        "key": "risk",
        "command": ["python", "tool.py"],
        "status": "succeeded",
        "returncode": 0,
        "duration_ms": 5,
        "stdout_chars": 10,
        "stderr_chars": 0,
        "data": {},
        "error": None,
    }
    return {
        "event": "layer3_pipeline_bundle",
        "run_id": "layer3-20260608-test",
        "created_at": "2026-06-08T15:00:00+00:00",
        "status": "succeeded",
        "primary_ticker": "TSLA",
        "tickers": ["TSLA", "PLTR", "SPY"],
        "universe": "tradfi",
        "bundle_path": "notebooks/auto-tickets/bundles/test.json",
        "state_db": "notebooks/auto-tickets/state.db",
        "itc": {
            **tool_result,
            "key": "itc",
            "data": {
                "symbol": "TSLA",
                "universe": "tradfi",
                "current_risk_score": 0.42,
                "risk_bands": [],
                "timestamp": "2026-06-08T15:00:00Z",
            },
        },
        "risk": {**tool_result, "key": "risk"},
        "mom": {**tool_result, "key": "mom"},
        "vol": {**tool_result, "key": "vol"},
        "opt": {
            **tool_result,
            "key": "opt",
            "data": {"weights": {"TSLA": 0.25, "PLTR": 0.25, "SPY": 0.50}},
        },
    }


def _portfolio_state() -> PortfolioState:
    return PortfolioState(
        portfolio_value=100000.0,
        cash_available=15000.0,
        monthly_dividend_income=500.0,
        monthly_margin_interest=200.0,
        current_positions={"TSLA": 10000.0, "PLTR": 5000.0, "SPY": 25000.0},
        context_date="2026-06-08",
    )


class FakeMessages:
    """Capture Anthropic request payloads and return forced tool-use blocks."""

    def __init__(
        self,
        cache_reads: list[int],
        *,
        tool_input: dict[str, Any] | None = None,
    ) -> None:
        self.cache_reads = cache_reads
        self.tool_input = tool_input
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        cache_read = self.cache_reads.pop(0)
        return SimpleNamespace(
            content=[
                SimpleNamespace(
                    type="tool_use",
                    name="emit_buy_ticket",
                    input=self.tool_input
                    if self.tool_input is not None
                    else _ticket_payload(),
                )
            ],
            usage=SimpleNamespace(
                input_tokens=100,
                output_tokens=50,
                cache_creation_input_tokens=900,
                cache_read_input_tokens=cache_read,
            ),
        )


class FakeAnthropicClient:
    """Minimal fake client exposing the SDK messages namespace."""

    def __init__(
        self,
        cache_reads: list[int],
        *,
        tool_input: dict[str, Any] | None = None,
    ) -> None:
        self.messages = FakeMessages(cache_reads, tool_input=tool_input)


def test_generate_calls_claude_with_prompt_cache_and_returns_valid_ticket() -> None:
    """Generation forces JSON tool use and validates the buy-ticket schema."""
    client = FakeAnthropicClient(cache_reads=[0])

    result = generate(_layer3_bundle(), _portfolio_state(), client=client)

    BuyTicket.model_validate(result.ticket.model_dump())
    assert result.ticket.document_type == "buy-ticket"
    assert [allocation.ticker for allocation in result.ticket.allocations] == [
        "TSLA",
        "PLTR",
        "SPY",
    ]
    assert result.guardrails.status == "accepted"
    assert result.usage.cache_read_input_tokens == 0

    call = client.messages.calls[0]
    assert call["model"] == "claude-sonnet-4-6"
    assert call["tool_choice"] == {
        "type": "tool",
        "name": "emit_buy_ticket",
        "disable_parallel_tool_use": True,
    }
    assert call["tools"][0]["name"] == "emit_buy_ticket"
    input_schema = call["tools"][0]["input_schema"]
    assert "advisory_block" not in input_schema["properties"]
    assert "advisory_block" not in input_schema.get("required", [])
    assert "itc_applicability" not in input_schema["properties"]
    assert "itc_risk_score" not in input_schema["properties"]
    assert any(
        block.get("cache_control", {}).get("type") == "ephemeral"
        for block in call["system"]
    )


def test_ticket_schema_rejects_mismatched_deployment_total() -> None:
    """Allocation dollars must match deployment_amount before guardrails run."""
    payload = _ticket_payload()
    payload["deployment_amount"] = 99999.0

    with pytest.raises(ValueError, match="allocation amounts"):
        BuyTicket.model_validate(payload)


def test_second_identical_generation_reports_prompt_cache_hit() -> None:
    """The second identical input exposes Anthropic cache-read usage metadata."""
    client = FakeAnthropicClient(cache_reads=[0, 1200])
    bundle = _layer3_bundle()
    portfolio = _portfolio_state()

    first = generate(bundle, portfolio, client=client)
    second = generate(bundle, portfolio, client=client)

    assert first.usage.cache_read_input_tokens == 0
    assert second.usage.cache_read_input_tokens == 1200
    assert len(client.messages.calls) == 2


def test_generate_clears_llm_authored_advisory_block_on_accepted_ticket() -> None:
    """System-owned advisory blocks cannot persist on accepted LLM output."""
    payload = {**_ticket_payload(), "advisory_block": "llm-authored advisory"}
    client = FakeAnthropicClient(cache_reads=[0], tool_input=payload)

    result = generate(_layer3_bundle(), _portfolio_state(), client=client)

    assert result.guardrails.status == "accepted"
    assert result.guardrails.advisory_block is None
    assert result.ticket.advisory_block is None


def test_generate_uses_layer3_itc_score_over_understated_model_score() -> None:
    """A lower model-authored ITC score cannot bypass the Layer 3 hard cap."""
    bundle = _layer3_bundle()
    bundle["itc"]["data"]["current_risk_score"] = 0.72
    payload = {**_ticket_payload(), "itc_risk_score": 0.01}
    client = FakeAnthropicClient(cache_reads=[0], tool_input=payload)

    result = generate(bundle, _portfolio_state(), client=client)

    assert result.guardrails.status == "blocked"
    assert result.guardrails.advisory_block == "itc_risk>=0.7"
    assert result.ticket.itc_risk_score == 0.72


@pytest.mark.parametrize("itc_state", ["missing", "not-run", "failed"])
def test_generate_blocks_unavailable_layer3_itc_before_model_call(
    itc_state: str,
) -> None:
    """Only a successful authoritative Layer 3 ITC result permits generation."""
    bundle = _layer3_bundle()
    if itc_state == "missing":
        del bundle["itc"]
    else:
        bundle["itc"]["status"] = itc_state
    client = FakeAnthropicClient(cache_reads=[0])

    with pytest.raises(ValueError, match="Layer 3 ITC"):
        generate(bundle, _portfolio_state(), client=client)

    assert client.messages.calls == []


def test_resolve_annual_margin_rate_prefers_decimal_instance_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The instance environment has one decimal-first margin-rate adapter."""
    monkeypatch.delenv("FG_MARGIN_INTEREST_RATE_DECIMAL", raising=False)
    monkeypatch.delenv("FG_MARGIN_INTEREST_RATE", raising=False)
    (tmp_path / ".env").write_text(
        "FG_MARGIN_INTEREST_RATE_DECIMAL=0.12\nFG_MARGIN_INTEREST_RATE=99%\n"
    )

    rate = config.resolve_annual_margin_rate(InstancePaths(root=tmp_path))

    assert rate == pytest.approx(0.12)


def test_generate_applies_configured_rate_to_projected_interest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The production generator wires configured rate policy into guardrails."""
    monkeypatch.setenv("FG_MARGIN_INTEREST_RATE_DECIMAL", "0.12")
    portfolio = _portfolio_state().model_copy(
        update={
            "cash_available": 0.0,
            "monthly_dividend_income": 100.0,
            "monthly_margin_interest": 0.0,
        }
    )
    client = FakeAnthropicClient(cache_reads=[0])

    result = generate(_layer3_bundle(), portfolio, client=client)

    assert result.guardrails.advisory_block == "coverage<2x"
