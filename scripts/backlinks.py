"""Link the first prose mention of every third-party vendor in the reader-facing docs.

Usage:
    uv run python scripts/backlinks.py            # rewrite the default targets
    uv run python scripts/backlinks.py --check    # exit 1 when a target would change
    uv run python scripts/backlinks.py docs/x.md  # limit to the given files

A vendor is linked at its first mention per file, unless an earlier link in that
file already carries the vendor name as its text. Fenced code, inline code,
front matter, headings, HTML blocks, existing links, image alt text, and bare
URLs are left alone.

The default targets are the reader-facing guides. Dated records (docs/plans,
docs/reports, docs/solutions, docs/adr, docs/brainstorms, docs/VISION.md) are
excluded on purpose: they are historical evidence, not setup paths, and linking
them would churn files nobody maintains.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Vendor:
    name: str
    url: str
    pattern: str


def _vendor(name: str, url: str, pattern: str | None = None) -> Vendor:
    return Vendor(name, url, pattern or rf"\b{re.escape(name)}\b")


VENDORS: tuple[Vendor, ...] = (
    _vendor("SnapTrade", "https://snaptrade.com/"),
    _vendor("SimpleFIN", "https://www.simplefin.org/"),
    _vendor("yfinance", "https://github.com/ranaroussi/yfinance"),
    _vendor("Finnhub", "https://finnhub.io/"),
    _vendor("Fidelity", "https://www.fidelity.com/"),
    _vendor("Plaid", "https://plaid.com/"),
    _vendor("Keepfolio", "https://keepfolio.app/"),
    _vendor("Claude Code", "https://code.claude.com/"),
    _vendor("Codex", "https://github.com/openai/codex"),
    _vendor("Anthropic", "https://www.anthropic.com/"),
    _vendor("OpenAI", "https://openai.com/"),
    _vendor("Pydantic", "https://docs.pydantic.dev/"),
    _vendor("SQLite", "https://www.sqlite.org/"),
    _vendor("pandas", "https://pandas.pydata.org/"),
    _vendor("NumPy", "https://numpy.org/", r"\b[Nn]um[Pp]y\b"),
    _vendor("uv", "https://docs.astral.sh/uv/"),
    _vendor("Bun", "https://bun.sh/"),
    _vendor("ruff", "https://docs.astral.sh/ruff/"),
    _vendor("mypy", "https://mypy-lang.org/"),
    _vendor("pytest", "https://docs.pytest.org/"),
    _vendor("gitleaks", "https://github.com/gitleaks/gitleaks"),
    _vendor("markdownlint", "https://github.com/DavidAnson/markdownlint"),
    _vendor("CodeRabbit", "https://www.coderabbit.ai/"),
    _vendor("release-please", "https://github.com/googleapis/release-please"),
    _vendor(
        "conventional commits",
        "https://www.conventionalcommits.org/",
        r"\b[Cc]onventional [Cc]ommits\b",
    ),
    _vendor("Diátaxis", "https://diataxis.fr/", r"\bDi[aá]taxis\b"),
    _vendor("GitHub Pages", "https://pages.github.com/"),
    _vendor("Slack", "https://slack.com/"),
    _vendor(
        "AGPL-3.0", "https://www.gnu.org/licenses/agpl-3.0.html", r"\bAGPL(?:-3\.0)?\b"
    ),
)

DEFAULT_TARGETS: tuple[str, ...] = (
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "PRIVACY.md",
    "docs/index.md",
    "docs/CONTRIBUTING.md",
    "docs/setup/*.md",
    "docs/reference/*.md",
    "docs/runbooks/*.md",
    "docs/guides/*.md",
    "docs-site/src/content/docs/**/*.md",
)

INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK = re.compile(r"!?\[(?P<text>[^\]\n]*)\]\([^)\n]*\)")
BARE_URL = re.compile(r"<?https?://[^\s>)]+>?")
FENCE_OPEN = re.compile(r"^\s*(`{3,}|~{3,})")
FENCE_CLOSE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")
VOID_TAGS = "area|base|br|col|embed|hr|img|input|link|meta|source|track|wbr"
HTML_OPEN = re.compile(rf"<(?!(?:{VOID_TAGS})\b)[a-z][\w-]*\b[^>]*(?<!/)>", re.I)
HTML_CLOSE = re.compile(r"</[a-z][\w-]*\s*>", re.I)


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    link_text: bool


def protected_spans(line: str) -> list[Span]:
    spans = [Span(m.start(), m.end(), False) for m in INLINE_CODE.finditer(line)]
    spans += [Span(m.start(), m.end(), False) for m in BARE_URL.finditer(line)]
    for m in LINK.finditer(line):
        is_image = line[m.start()] == "!"
        spans.append(Span(m.start(), m.start("text"), False))
        spans.append(Span(m.start("text"), m.end("text"), not is_image))
        spans.append(Span(m.end("text"), m.end(), False))
    return spans


def _covering(spans: list[Span], start: int, end: int) -> Span | None:
    return next((s for s in spans if s.start <= start and end <= s.end), None)


def _prose_lines(lines: list[str]) -> list[int]:
    """Indexes of lines eligible for linking."""
    eligible: list[int] = []
    fence: str | None = None
    html_depth = 0
    in_front_matter = lines[:1] == ["---"]
    for i, line in enumerate(lines):
        if in_front_matter:
            if i > 0 and line.strip() == "---":
                in_front_matter = False
            continue
        if fence is not None:
            marker = FENCE_CLOSE.match(line)
            if (
                marker
                and marker.group(1)[0] == fence[0]
                and len(marker.group(1)) >= len(fence)
            ):
                fence = None
            continue
        marker = FENCE_OPEN.match(line)
        if marker:
            fence = marker.group(1)
            continue
        stripped = line.lstrip()
        html_depth += len(HTML_OPEN.findall(stripped)) - len(
            HTML_CLOSE.findall(stripped)
        )
        if html_depth > 0 or not stripped or stripped[0] in "#<":
            continue
        if re.match(r"^\[[^\]]+\]:\s", stripped):
            continue
        eligible.append(i)
    return eligible


def link_vendors(text: str, vendors: tuple[Vendor, ...] = VENDORS) -> str:
    lines = text.split("\n")
    eligible = _prose_lines(lines)
    for vendor in vendors:
        pattern = re.compile(vendor.pattern)
        done = False
        for i in eligible:
            spans = protected_spans(lines[i])
            for m in pattern.finditer(lines[i]):
                cover = _covering(spans, m.start(), m.end())
                if cover is None:
                    lines[i] = (
                        f"{lines[i][: m.start()]}[{m.group(0)}]({vendor.url}){lines[i][m.end() :]}"
                    )
                    done = True
                elif cover.link_text:
                    done = True
                if done:
                    break
            if done:
                break
    return "\n".join(lines)


def resolve_targets(patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        path = Path(pattern)
        if path.is_file():
            paths.add(path)
        else:
            paths.update(p for p in REPO_ROOT.glob(pattern) if p.is_file())
    return sorted(paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "paths", nargs="*", help="files or globs; defaults to the doc surfaces"
    )
    parser.add_argument(
        "--check", action="store_true", help="report drift without writing"
    )
    args = parser.parse_args(argv)

    changed: list[Path] = []
    for path in resolve_targets(args.paths or list(DEFAULT_TARGETS)):
        original = path.read_text(encoding="utf-8")
        updated = link_vendors(original)
        if updated == original:
            continue
        changed.append(path)
        if not args.check:
            path.write_text(updated, encoding="utf-8")

    verb = "would change" if args.check else "updated"
    for path in changed:
        print(f"{verb}: {path.relative_to(REPO_ROOT) if path.is_absolute() else path}")
    if args.check and changed:
        print("run `uv run python scripts/backlinks.py` to link the vendor mentions")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
