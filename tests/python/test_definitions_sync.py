"""Drift-detector for fin-guru/data/definitions.md.

The glossary cites specific values from src/ (and from the skill files). When
the source-of-truth changes — someone bumps the default risk-free rate, swaps
the $50k-per-contract sizing rule, retires a constant — this test catches the
divergence so the glossary doesn't quietly rot.

When this test fails:
  1. Decide which side is canonical (usually src/, sometimes the skill).
  2. Fix the OTHER side to match. NEVER silence the test by editing only it.
  3. If the constant has moved (renamed or relocated), update both this test
     and the table in definitions.md §1.

RUNNING:
    uv run pytest tests/python/test_definitions_sync.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFINITIONS_PATH = REPO_ROOT / "fin-guru" / "data" / "definitions.md"


@pytest.fixture(scope="module")
def doc_text() -> str:
    return DEFINITIONS_PATH.read_text(encoding="utf-8")


def _row_value(constant_name: str, doc_text: str) -> str:
    """Return the second column ("Value") of a row in §1 whose first column matches `constant_name`.

    The §1 table uses backticks around the constant name: `| `NAME` | VALUE | ... |`.
    """
    pattern = rf"\|\s*`{re.escape(constant_name)}`\s*\|\s*([^|]+?)\s*\|"
    match = re.search(pattern, doc_text)
    if match is None:
        raise AssertionError(
            f"Constant {constant_name!r} not found in definitions.md §1 constants table. "
            "Add a row, or remove the test for this constant."
        )
    return match.group(1).strip()


def _constraint_value(field, attr: str):
    """Pluck `ge` / `le` / etc. from a Pydantic v2 field's metadata list.

    Pydantic uses annotated_types under the hood; each constraint exposes the
    value via `.ge`, `.le`, `.gt`, `.lt`. We tolerate either the typed objects
    or the dict-style metadata.
    """
    for entry in getattr(field, "metadata", []):
        value = getattr(entry, attr, None)
        if value is not None:
            return value
    return None


class TestNamedConstants:
    def test_portfolio_per_contract(self, doc_text):
        from src.analysis.hedge_sizer import DEFAULT_RATIO_PER_CONTRACT

        assert DEFAULT_RATIO_PER_CONTRACT == 50_000.0, (
            "DEFAULT_RATIO_PER_CONTRACT changed. Update definitions.md §1 "
            "(PORTFOLIO_PER_CONTRACT) and §11.1 (the sizing rule)."
        )
        documented = _row_value("PORTFOLIO_PER_CONTRACT", doc_text)
        assert "$50,000" in documented, (
            f"definitions.md §1 documents PORTFOLIO_PER_CONTRACT = {documented!r} "
            f"but src/analysis/hedge_sizer.py has 50000.0."
        )

    def test_default_implied_volatility(self, doc_text):
        from src.analysis.rolling_tracker import DEFAULT_IV

        assert DEFAULT_IV == 0.30
        documented = _row_value("IMPLIED_VOLATILITY_DEFAULT", doc_text)
        assert "0.30" in documented, (
            f"definitions.md says IV default = {documented!r} but rolling_tracker.py has {DEFAULT_IV}."
        )

    def test_default_risk_free_rate_consistent_across_modules(self, doc_text):
        """All three independent declarations of the 4.5% default must agree."""
        from src.analysis.options_chain_cli import (
            DEFAULT_RISK_FREE_RATE as OCC_RFR,
        )
        from src.analysis.rolling_tracker import (
            DEFAULT_RISK_FREE_RATE as RT_RFR,
        )

        assert RT_RFR == 0.045, (
            "rolling_tracker.DEFAULT_RISK_FREE_RATE drifted from 0.045"
        )
        assert OCC_RFR == 0.045, (
            "options_chain_cli.DEFAULT_RISK_FREE_RATE drifted from 0.045"
        )
        assert RT_RFR == OCC_RFR, (
            f"Two src/ modules disagree on DEFAULT_RISK_FREE_RATE: "
            f"rolling_tracker={RT_RFR}, options_chain_cli={OCC_RFR}. "
            "Pick one canonical home and import everywhere."
        )

        documented = _row_value("RISK_FREE_RATE_DEFAULT", doc_text)
        assert "0.045" in documented, (
            f"definitions.md says RFR default = {documented!r} but src says {RT_RFR}."
        )

    def test_trading_days_per_year(self, doc_text):
        from src.analysis import risk_metrics
        from src.utils.trading_calendar import TRADING_DAYS_PER_YEAR

        assert TRADING_DAYS_PER_YEAR == 252
        assert risk_metrics.TRADING_DAYS_PER_YEAR is TRADING_DAYS_PER_YEAR, (
            "risk_metrics.py must annualize with the shared trading-calendar constant."
        )
        documented = _row_value("TRADING_DAYS_PER_YEAR", doc_text)
        assert "252" in documented

    def test_put_call_parity_tolerance(self, doc_text):
        from src.analysis.options import PUT_CALL_PARITY_ARBITRAGE_DOLLARS

        assert PUT_CALL_PARITY_ARBITRAGE_DOLLARS == 0.10, (
            "The put-call parity tolerance moved. Update definitions.md §1 "
            "(PUT_CALL_PARITY_TOLERANCE) and §10.4."
        )
        documented = _row_value("PUT_CALL_PARITY_TOLERANCE", doc_text)
        assert "0.10" in documented


class TestPydanticFields:
    def test_black_scholes_risk_free_default(self):
        from src.models.options_inputs import BlackScholesInput

        field = BlackScholesInput.model_fields["risk_free_rate"]
        assert field.default == 0.045, (
            "BlackScholesInput.risk_free_rate default drifted from 0.045. "
            "Update definitions.md §1 if intentional."
        )

    def test_dividend_yield_bounds(self, doc_text):
        from src.models.options_inputs import BlackScholesInput

        field = BlackScholesInput.model_fields["dividend_yield"]
        assert field.default == 0.0
        ge = _constraint_value(field, "ge")
        le = _constraint_value(field, "le")
        assert ge == 0.0, f"dividend_yield ge constraint = {ge!r}, expected 0.0"
        assert le == 0.20, f"dividend_yield le constraint = {le!r}, expected 0.20"

        documented = _row_value("DIVIDEND_YIELD_DEFAULT", doc_text)
        assert "[0.0, 0.20]" in documented, (
            f"definitions.md describes dividend_yield bounds as {documented!r}; "
            f"actual Pydantic constraint is [{ge}, {le}]."
        )

    def test_var_confidence_default(self, doc_text):
        from src.models.risk_inputs import RiskCalculationConfig

        field = RiskCalculationConfig.model_fields["confidence_level"]
        assert field.default == 0.95, (
            "RiskCalculationConfig.confidence_level default drifted from 0.95."
        )
        documented = _row_value("VAR_CONFIDENCE_DEFAULT", doc_text)
        assert "0.95" in documented

    def test_rolling_window_default_is_one_trading_year(self):
        """Rolling window default = 252 reinforces the trading-day constant."""
        from src.models.risk_inputs import RiskCalculationConfig

        field = RiskCalculationConfig.model_fields["rolling_window"]
        assert field.default == 252, (
            "rolling_window default drifted from 252 (one trading year). "
            "If trading-day count itself changed, update definitions.md §1 "
            "TRADING_DAYS_PER_YEAR row too."
        )


class TestInlineLiterals:
    def test_calendar_days_365_in_total_return(self, doc_text):
        tr = (REPO_ROOT / "src" / "analysis" / "total_return.py").read_text()
        assert re.search(r"365\.0\s*/\s*calendar_days", tr), (
            "total_return.py no longer applies the canonical "
            "(1 + total_return) ** (365.0 / calendar_days) − 1 annualization. "
            "If the calendar-day base genuinely moved, update definitions.md §1 "
            "(CALENDAR_DAYS_PER_YEAR) and §3.3."
        )
        documented = _row_value("CALENDAR_DAYS_PER_YEAR", doc_text)
        assert "365" in documented


class TestSkillConstants:
    def test_margin_rate_default_matches_skill(self, doc_text):
        skill = (
            REPO_ROOT / ".claude" / "skills" / "margin-management" / "SKILL.md"
        ).read_text()
        assert "FG_MARGIN_INTEREST_RATE" in skill, (
            "margin-management/SKILL.md must read the margin rate from .env, "
            "not tracked personal strategy numbers."
        )
        documented = _row_value("MARGIN_RATE_FIDELITY_DEFAULT", doc_text)
        assert "FG_MARGIN_INTEREST_RATE" in documented

    def test_concentration_limit_hard_matches_skill(self, doc_text):
        skill_path = (
            REPO_ROOT / ".claude" / "skills" / "fin-guru-buy-ticket" / "SKILL.md"
        )
        if not skill_path.exists():
            pytest.skip(
                f"{skill_path.relative_to(REPO_ROOT)} not committed yet — "
                "buy-ticket skill is WIP. Test re-activates once the skill lands on main."
            )
        skill = skill_path.read_text()
        assert "30%" in skill or "0.30" in skill, (
            "fin-guru-buy-ticket/SKILL.md no longer enforces the 30% single-position cap. "
            "Update definitions.md §1 (CONCENTRATION_LIMIT_HARD) and §15."
        )
        documented = _row_value("CONCENTRATION_LIMIT_HARD", doc_text)
        assert "0.30" in documented or "30%" in documented


CONSTANTS_TESTED = (
    "PORTFOLIO_PER_CONTRACT",
    "IMPLIED_VOLATILITY_DEFAULT",
    "RISK_FREE_RATE_DEFAULT",
    "DIVIDEND_YIELD_DEFAULT",
    "VAR_CONFIDENCE_DEFAULT",
    "TRADING_DAYS_PER_YEAR",
    "CALENDAR_DAYS_PER_YEAR",
    "PUT_CALL_PARITY_TOLERANCE",
    "MARGIN_RATE_FIDELITY_DEFAULT",
    "CONCENTRATION_LIMIT_HARD",
)


@pytest.mark.parametrize("constant", CONSTANTS_TESTED)
def test_every_tested_constant_is_documented(doc_text, constant):
    """If a constant has a test below, it must also have a row in §1."""
    _row_value(constant, doc_text)
