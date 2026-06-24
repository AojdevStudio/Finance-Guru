"""Regression test pinning the Fidelity action_taxonomy contract.

Loads `docs/csv-mappings/fidelity-mapping.json` and applies its `action_taxonomy`
block to a golden 7-row CSV fixture. Asserts both row-level categorization and
aggregate totals match `fidelity_history_golden_expected.json`.

The classify function in this test is the reference implementation Keepfolio's
TypeScript parser should mirror: uppercase the Action field, then test each
category's patterns in declared order — first match wins.
"""

import csv
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MAPPING_PATH = REPO_ROOT / "docs" / "csv-mappings" / "fidelity-mapping.json"
FIXTURE_CSV = Path(__file__).parent / "fixtures" / "fidelity_history_golden.csv"
FIXTURE_EXPECTED = (
    Path(__file__).parent / "fixtures" / "fidelity_history_golden_expected.json"
)


@pytest.fixture(scope="module")
def taxonomy() -> dict:
    """Load the action_taxonomy block from the broker mapping JSON."""
    return json.loads(MAPPING_PATH.read_text(encoding="utf-8"))["action_taxonomy"]


@pytest.fixture(scope="module")
def expected() -> dict:
    return json.loads(FIXTURE_EXPECTED.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def golden_rows() -> list[dict]:
    """Read the golden fixture CSV with the same preamble-skip logic as production."""
    with FIXTURE_CSV.open("r", encoding="utf-8-sig") as fh:
        lines = fh.readlines()
    header_idx = next(
        (i for i, line in enumerate(lines) if line.strip().startswith("Run Date")),
        None,
    )
    assert header_idx is not None, "Fixture CSV missing 'Run Date' header"
    return list(csv.DictReader(lines[header_idx:]))


def classify(action: str, taxonomy: dict) -> str:
    """Apply the JSON action_taxonomy to a single Action string.

    This is the reference matcher — Keepfolio's TS port should produce
    identical category labels for the same Action input.
    """
    action_upper = action.upper()
    for category_name, category_def in taxonomy["categories"].items():
        for pattern in category_def["patterns"]:
            if pattern.upper() in action_upper:
                return category_name
    return taxonomy["fallback_category"]


def parse_amount(raw: str) -> float:
    """Fidelity currency: strip $, commas, treat parentheses as negative."""
    if not raw or not raw.strip():
        return 0.0
    clean = raw.strip().replace("$", "").replace(",", "")
    if clean.startswith("(") and clean.endswith(")"):
        clean = "-" + clean[1:-1]
    return float(clean)


# ---- Row-level assertions -----------------------------------------------


def test_row_count(golden_rows, expected):
    assert len(golden_rows) == expected["row_count"]


@pytest.mark.parametrize("index", range(7))
def test_row_categorization(index, golden_rows, expected, taxonomy):
    """Each golden row classifies into the expected taxonomy category."""
    row = golden_rows[index]
    expected_row = expected["rows"][index]
    actual = classify(row["Action"], taxonomy)
    assert actual == expected_row["expected_category"], (
        f"Row {index} (Action={row['Action'][:60]!r}) "
        f"classified as {actual} but expected {expected_row['expected_category']}"
    )


def test_substitute_payment_pattern_priority(taxonomy):
    """The more-specific 'DIVIDEND RECEIVED SUBSTITUTE PAYMENT' pattern must be
    listed before plain 'DIVIDEND RECEIVED' so it wins on first-match.

    If a future edit reorders the patterns, this guard catches it.
    """
    dividend_patterns = taxonomy["categories"]["INCOME_DIVIDEND"]["patterns"]
    sub_idx = dividend_patterns.index("DIVIDEND RECEIVED SUBSTITUTE PAYMENT")
    plain_idx = dividend_patterns.index("DIVIDEND RECEIVED")
    assert sub_idx < plain_idx, (
        "SUBSTITUTE PAYMENT must precede plain DIVIDEND RECEIVED"
    )


# ---- Aggregate totals (the real contract) -------------------------------


def test_totals_match_expected(golden_rows, expected, taxonomy):
    """The whole point of the taxonomy: produce correct wages/income/spending."""
    wages_total = 0.0
    investment_income_total = 0.0
    true_spending_total = 0.0
    excluded_internal_transfer = 0.0
    excluded_reinvestment = 0.0
    excluded_cc_passthrough = 0.0

    for row in golden_rows:
        amount = parse_amount(row["Amount ($)"])
        category = classify(row["Action"], taxonomy)
        if category == "INCOME_WAGES":
            wages_total += amount
        elif category in ("INCOME_DIVIDEND", "INCOME_CAPITAL_GAIN", "INCOME_INTEREST"):
            investment_income_total += amount
        elif category in (
            "DEBIT_CARD_PURCHASE",
            "CASH_WITHDRAWAL",
            "DIRECT_DEBIT_BILL",
            "AUTO_LOAN_PAYMENT",
            "MARGIN_INTEREST",
            "FEE",
        ):
            true_spending_total += abs(amount)
        elif category == "INTERNAL_TRANSFER":
            excluded_internal_transfer += amount
        elif category == "REINVESTMENT":
            excluded_reinvestment += amount
        elif category == "CC_PAYMENT_PASSTHROUGH":
            excluded_cc_passthrough += amount

    totals = expected["totals"]
    assert wages_total == pytest.approx(totals["wages_total"])
    assert investment_income_total == pytest.approx(totals["investment_income_total"])
    assert (wages_total + investment_income_total) == pytest.approx(
        totals["total_income"]
    )
    assert true_spending_total == pytest.approx(totals["true_spending_total"])

    excluded = totals["_excluded_from_both"]
    assert excluded_internal_transfer == pytest.approx(
        excluded["internal_transfer_amount"]
    )
    assert excluded_reinvestment == pytest.approx(excluded["reinvestment_amount"])
    assert excluded_cc_passthrough == pytest.approx(excluded["cc_passthrough_amount"])


def test_employer_attribution_extracts_payor(golden_rows, expected):
    """For INCOME_WAGES rows, the employer label is parsed from the Action string."""
    wages_row = golden_rows[0]
    action = wages_row["Action"]
    prefix = "DIRECT DEPOSIT "
    assert action.startswith(prefix), "Fixture row 0 should start with DIRECT DEPOSIT"
    suffix_marker = " (Cash)"
    employer = action[len(prefix) :].split(suffix_marker)[0]
    assert employer == expected["rows"][0]["expected_employer"]
