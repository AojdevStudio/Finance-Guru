"""Tests for compliance-scan layer 7, the financial-figure detector.

The detector lives outside src/, but its behavior gates every push. Each case
here pins a rule that was verified against a real leak on 2026-08-31.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_SCAN_PATH = (
    Path(__file__).resolve().parents[2]
    / ".claude"
    / "skills"
    / "compliance-scan"
    / "scripts"
    / "scan.py"
)
_spec = importlib.util.spec_from_file_location("compliance_scan", _SCAN_PATH)
assert _spec is not None and _spec.loader is not None
scan = importlib.util.module_from_spec(_spec)
sys.modules["compliance_scan"] = scan
_spec.loader.exec_module(scan)

DOC = ".claude/skills/example/SKILL.md"
ALLOWED = frozenset({"1,234.56", "383,900"})


def _hits(path: str, text: str) -> int:
    return len(scan.scan_layer7_financial_figures(path, text, ALLOWED))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("equity of $204,753", 1),
        ("spend was $7,936.23", 1),
        ("interest of $729.81", 1),
        ("a $50,000 example portfolio", 0),
        ("deposit $2,000.00 monthly", 0),
        ("a $0.45 verification deposit", 0),
        ("the fixture uses $1,234.56", 0),
        ("bracket edge at $383,900", 0),
    ],
)
def test_precision_separates_real_money_from_scenarios(
    text: str, expected: int
) -> None:
    assert _hits(DOC, text) == expected


def test_code_comments_are_covered() -> None:
    assert _hits(".claude/skills/example/tool.py", "# saw $204,753 here") == 1


def test_paths_outside_doc_prefixes_are_not_covered() -> None:
    assert _hits("src/analysis/notes.py", "$204,753") == 0


def test_scanner_self_exemption_does_not_apply_to_layer7() -> None:
    path = ".claude/skills/compliance-scan/scripts/scan.py"
    assert scan.should_skip(path) is True
    assert _hits(path, "# example: $204,753") == 1
