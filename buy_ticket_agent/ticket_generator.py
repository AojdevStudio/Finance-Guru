"""Claude-backed AOJ-461 buy-ticket generation."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from buy_ticket_agent.config import resolve_annual_margin_rate
from buy_ticket_agent.guardrails import GuardrailResult, check
from buy_ticket_agent.ticket_models import (
    BuyTicket,
    GuardrailContext,
    PortfolioState,
    TicketProposal,
)
from src.models.itc_risk_inputs import ITCRiskResponse

DEFAULT_MODEL = "claude-sonnet-4-6"
TICKET_TOOL_NAME = "emit_buy_ticket"
SYSTEM_MANAGED_TICKET_FIELDS = frozenset(
    {"advisory_block", "itc_applicability", "itc_risk_score"}
)
FRAMEWORK_DOC_PATHS = (
    "fin-guru/templates/buy-ticket-template.md",
    "fin-guru/data/definitions.md",
    "fin-guru/checklists/margin-strategy.md",
)


class TicketUsage(BaseModel):
    """Token usage metadata surfaced from the Anthropic response."""

    model_config = ConfigDict(extra="forbid")

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


class TicketGenerationResult(BaseModel):
    """Validated generation result after guardrail enforcement."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    ticket: BuyTicket
    guardrails: GuardrailResult
    usage: TicketUsage
    model: str = Field(default=DEFAULT_MODEL)


class Layer3ITCError(ValueError):
    """Raised when authoritative ITC evidence cannot support generation."""


def _default_client() -> Any:
    """Build the Anthropic client lazily so tests can inject a fake client."""
    try:
        from anthropic import Anthropic
    except ImportError as exc:  # pragma: no cover - covered by dependency gates
        raise RuntimeError("anthropic SDK is required for ticket generation") from exc
    return Anthropic()


def _load_framework_docs(project_root: Path) -> list[dict[str, str]]:
    """Load public framework docs used as prompt-cache blocks."""
    docs: list[dict[str, str]] = []
    for relative_path in FRAMEWORK_DOC_PATHS:
        path = project_root / relative_path
        if not path.exists():
            continue
        docs.append({"path": relative_path, "text": path.read_text()})
    return docs


def _system_blocks(
    *,
    project_root: Path,
    framework_docs: list[dict[str, str]] | None,
) -> list[dict[str, Any]]:
    docs = (
        framework_docs
        if framework_docs is not None
        else _load_framework_docs(project_root)
    )
    blocks: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Generate a Finance Guru buy-ticket JSON object only through the "
                f"{TICKET_TOOL_NAME} tool. Preserve educational-only compliance "
                "language. Hard risk guardrails are enforced by Python after this "
                "response and are not negotiable."
            ),
        }
    ]
    for doc in docs:
        blocks.append(
            {
                "type": "text",
                "text": f"Framework document: {doc['path']}\n\n{doc['text']}",
                "cache_control": {"type": "ephemeral"},
            }
        )
    return blocks


def _tool_schema() -> dict[str, Any]:
    input_schema = TicketProposal.model_json_schema()
    return {
        "name": TICKET_TOOL_NAME,
        "description": "Emit one structured buy-ticket JSON object.",
        "input_schema": input_schema,
    }


def _user_message(bundle: dict[str, Any], portfolio: PortfolioState) -> dict[str, Any]:
    payload = {
        "layer3_bundle": bundle,
        "portfolio_state": portfolio.model_dump(mode="json"),
        "instructions": (
            "Generate a buy-ticket for the bundle tickers. Use the template schema "
            "and include the educational notice. Do not include approval URLs, "
            "execution instructions, audit-log writes, or private account details."
        ),
    }
    return {
        "role": "user",
        "content": [{"type": "text", "text": json.dumps(payload, sort_keys=True)}],
    }


def _block_value(block: Any, name: str) -> Any:
    if isinstance(block, dict):
        return block.get(name)
    return getattr(block, name, None)


def _extract_tool_input(response: Any) -> dict[str, Any]:
    for block in getattr(response, "content", []):
        if (
            _block_value(block, "type") == "tool_use"
            and _block_value(block, "name") == TICKET_TOOL_NAME
        ):
            tool_input = _block_value(block, "input")
            if isinstance(tool_input, dict):
                return tool_input
            raise ValueError("emit_buy_ticket tool input must be a JSON object")
    raise ValueError("Claude response did not include emit_buy_ticket tool use")


def _usage_value(usage: Any, name: str) -> int:
    value = usage.get(name, 0) if isinstance(usage, dict) else getattr(usage, name, 0)
    return int(value or 0)


def _usage_from_response(response: Any) -> TicketUsage:
    usage = getattr(response, "usage", None)
    return TicketUsage(
        input_tokens=_usage_value(usage, "input_tokens"),
        output_tokens=_usage_value(usage, "output_tokens"),
        cache_creation_input_tokens=_usage_value(
            usage,
            "cache_creation_input_tokens",
        ),
        cache_read_input_tokens=_usage_value(usage, "cache_read_input_tokens"),
    )


def _authoritative_itc(bundle: Mapping[str, Any]) -> ITCRiskResponse:
    """Validate successful Layer 3 ITC evidence before model generation."""
    itc_result = bundle.get("itc")
    if not isinstance(itc_result, Mapping):
        raise Layer3ITCError("Layer 3 ITC result is missing")
    if itc_result.get("status") != "succeeded" or itc_result.get("returncode") != 0:
        raise Layer3ITCError("Layer 3 ITC result did not succeed")
    data = itc_result.get("data")
    if not isinstance(data, Mapping):
        raise Layer3ITCError("Layer 3 ITC data is missing")
    raw_score = data.get("current_risk_score")
    if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
        raise Layer3ITCError("Layer 3 ITC risk score is malformed")
    try:
        evidence = ITCRiskResponse.model_validate(data)
    except ValidationError as exc:
        raise Layer3ITCError("Layer 3 ITC data is malformed") from exc

    primary_ticker = bundle.get("primary_ticker")
    if not isinstance(primary_ticker, str) or (
        evidence.symbol != primary_ticker.strip().upper()
    ):
        raise Layer3ITCError("Layer 3 ITC symbol does not match primary ticker")
    return evidence


def generate(
    bundle: dict[str, Any],
    portfolio_state: PortfolioState | dict,
    *,
    client: Any | None = None,
    project_root: Path | None = None,
    model: str = DEFAULT_MODEL,
    framework_docs: list[dict[str, str]] | None = None,
) -> TicketGenerationResult:
    """Generate a buy-ticket JSON object and enforce hard guardrails."""
    parsed_portfolio = PortfolioState.model_validate(portfolio_state)
    itc = _authoritative_itc(bundle)
    annual_margin_rate = resolve_annual_margin_rate()
    anthropic_client = client if client is not None else _default_client()
    root = project_root or Path.cwd()

    response = anthropic_client.messages.create(
        model=model,
        max_tokens=4096,
        system=_system_blocks(project_root=root, framework_docs=framework_docs),
        messages=[_user_message(bundle, parsed_portfolio)],
        tools=[_tool_schema()],
        tool_choice={
            "type": "tool",
            "name": TICKET_TOOL_NAME,
            "disable_parallel_tool_use": True,
        },
    )
    tool_input = _extract_tool_input(response)
    proposal = TicketProposal.model_validate(
        {
            field_name: value
            for field_name, value in tool_input.items()
            if field_name not in SYSTEM_MANAGED_TICKET_FIELDS
        }
    )
    guardrail_result = check(
        proposal,
        GuardrailContext(
            portfolio=parsed_portfolio,
            itc_risk_score=itc.current_risk_score,
            annual_margin_rate=annual_margin_rate,
        ),
    )
    return TicketGenerationResult(
        ticket=guardrail_result.ticket,
        guardrails=guardrail_result,
        usage=_usage_from_response(response),
        model=model,
    )
