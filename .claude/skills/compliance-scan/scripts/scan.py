#!/usr/bin/env python3
"""Compliance scanner for the Finance Guru repo.

Six layers:
  1. owner-name leak detector  (delegated to existing pytest)
  2. gitignore-coverage test   (delegated to existing bash test)
  3. CRITICAL secret patterns  (regex; built-in)
  4. HIGH PII patterns         (scripts/qa/pii-replacements.txt + built-ins)
  5. untracked sensitive paths (.claude/skills/, notebooks/, etc.)
  6. PRIVACY.md vs .gitignore  (alignment check)

Exit codes:
  0  clean (no findings at or above --fail-on)
  1  findings at or above --fail-on
  2  scan error / wrong cwd
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

# --------------------------------------------------------------------------- #
# Severity                                                                    #
# --------------------------------------------------------------------------- #


class Severity(IntEnum):
    INFO = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def parse(cls, name: str) -> Severity:
        return cls[name.strip().upper()]


# --------------------------------------------------------------------------- #
# Finding                                                                     #
# --------------------------------------------------------------------------- #


@dataclass
class Finding:
    severity: Severity
    layer: str
    rule: str
    path: str
    line: int | None = None
    snippet: str = ""
    remediation: str = ""

    def to_dict(self) -> dict:
        return {
            "severity": self.severity.name,
            "layer": self.layer,
            "rule": self.rule,
            "path": self.path,
            "line": self.line,
            "snippet": self.snippet,
            "remediation": self.remediation,
        }


# --------------------------------------------------------------------------- #
# Built-in pattern catalogs                                                   #
# --------------------------------------------------------------------------- #
# Each entry: (rule_name, regex, severity, remediation_hint)

CRITICAL_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "aws-access-key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "Rotate the AWS key in IAM, scrub from history with git-filter-repo, "
        "store the new key in .env (gitignored).",
    ),
    (
        "github-pat-classic",
        re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
        "Revoke at github.com/settings/tokens, rotate, store in .env.",
    ),
    (
        "github-pat-fine-grained",
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82}\b"),
        "Revoke at github.com/settings/personal-access-tokens, rotate.",
    ),
    (
        "github-server-token",
        re.compile(r"\bghs_[A-Za-z0-9]{36}\b"),
        "Revoke the server-to-server token; rotate.",
    ),
    (
        "anthropic-key",
        re.compile(r"\bsk-ant-[A-Za-z0-9_-]{40,}\b"),
        "Rotate at console.anthropic.com; new key into .env.",
    ),
    (
        "openai-key",
        re.compile(r"\bsk-proj-[A-Za-z0-9_-]{40,}\b|\bsk-[A-Za-z0-9]{48}\b"),
        "Rotate at platform.openai.com; new key into .env.",
    ),
    (
        "slack-bot-token",
        re.compile(r"\bxoxb-\d+-\d+-[A-Za-z0-9]+\b"),
        "Rotate the Slack bot token; reinstall the app if needed.",
    ),
    (
        "slack-user-token",
        re.compile(r"\bxoxp-\d+-\d+-\d+-[a-f0-9]+\b"),
        "Rotate the Slack user token immediately.",
    ),
    (
        "google-api-key",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
        "Rotate in Google Cloud Console > Credentials; restrict by IP/referrer.",
    ),
    (
        "private-key-pem",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
        "Move the key out of the repo; regenerate if it was ever committed.",
    ),
    (
        "jwt-token",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
        ),
        "Treat as compromised — invalidate the session and rotate the signing key.",
    ),
    (
        "bright-data-token",
        re.compile(r"\b[a-f0-9]{64}\b"),
        "Bright Data API token style. Verify it's real, then rotate at brightdata.com.",
    ),
]

HIGH_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "fidelity-account",
        re.compile(r"\bZ0\d{7,}\b"),
        "Replace with `{account_id}` template variable; load real value from "
        "env/onboarding state.",
    ),
    (
        "ssn",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "Never commit. Move to env or local-only file.",
    ),
    (
        "apps-script-dispatcher",
        re.compile(r"https://script\.google\.com/macros/s/[A-Za-z0-9_-]{40,}/exec"),
        "Move the URL to .env or a gitignored config; reference via env var only.",
    ),
    (
        "google-script-deployment-id",
        re.compile(r"\bAKfyc[A-Za-z0-9_-]{50,}\b"),
        "Apps Script deployment ID. Treat like a credential — env var only.",
    ),
]

# Sensitive path prefixes — untracked files in these locations are INFO findings
# unless the file content also matches HIGH/CRITICAL (then severity is upgraded).
SENSITIVE_PATH_PREFIXES: tuple[str, ...] = (
    ".claude/skills/apps-script-run",
    "notebooks/",
    "fin-guru-private/",
    "fin-guru/data/",
    "credentials/",
    "private/",
    "sensitive/",
)

SENSITIVE_PATH_GLOBS: tuple[str, ...] = (
    ".env",
    ".env.*",
    "*.env",
    "*.key",
    "*.pem",
)

# Skill name fragments that should not be tracked even under .claude/skills/
SENSITIVE_SKILL_FRAGMENTS: tuple[str, ...] = (
    "apps-script",
    "dispatcher",
    "webhook",
    "credential",
    "secret",
)

# File extensions that are never scanned (binary or known-safe)
SKIP_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".pdf",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
        ".zip",
        ".gz",
        ".tar",
        ".7z",
        ".mp3",
        ".mp4",
        ".mov",
        ".wav",
        ".pyc",
        ".pyo",
        ".so",
        ".dylib",
        ".dll",
        ".lock",
    }
)

# Paths the scanner ignores (its own data should not flag itself)
SCANNER_SELF_PATHS: tuple[str, ...] = (
    ".claude/skills/compliance-scan/",
    "scripts/qa/pii-replacements.txt",
    "scripts/qa/pii-replacements.template.txt",
    "scripts/qa/author-mailmap.txt",
    "scripts/qa/author-mailmap.template.txt",
    "tests/python/test_no_hardcoded_references.py",
)

# Allowlist file: a list of path globs that are KNOWN-ACCEPTED exceptions.
# Loaded from .claude/skills/compliance-scan/allowlist.json. Each entry has:
#   {"path": "<glob>", "reason": "<why this is OK>", "approved_by": "<name>", "date": "YYYY-MM-DD"}
# Matching paths skip ALL pattern scans. Reserve for cases where the value
# is legitimately committed (e.g., a golden test fixture).
ALLOWLIST_FILE = ".claude/skills/compliance-scan/allowlist.json"


# --------------------------------------------------------------------------- #
# Pattern loading from scripts/qa/pii-replacements.txt                        #
# --------------------------------------------------------------------------- #


def load_pii_replacement_patterns(
    repo_root: Path,
) -> list[tuple[str, re.Pattern[str], str]]:
    """Parse scripts/qa/pii-replacements.txt; convert to HIGH-severity rules.

    File format (per file header):
        literal:PATTERN==>REPLACEMENT
        regex:PATTERN==>REPLACEMENT
    Comment lines start with #.
    """
    path = repo_root / "scripts" / "qa" / "pii-replacements.txt"
    if not path.exists():
        return []

    rules: list[tuple[str, re.Pattern[str], str]] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==>" not in line:
            continue
        lhs, _, replacement = line.partition("==>")
        if lhs.startswith("literal:"):
            literal = lhs[len("literal:") :]
            try:
                rules.append(
                    (
                        f"pii-replacements:{literal[:32]}",
                        re.compile(re.escape(literal)),
                        f"Replace literal with `{replacement}`; source value belongs in "
                        "env/onboarding state.",
                    )
                )
            except re.error:
                continue
        elif lhs.startswith("regex:"):
            pattern = lhs[len("regex:") :]
            try:
                rules.append(
                    (
                        f"pii-replacements:regex:{pattern[:32]}",
                        re.compile(pattern),
                        f"Replace match with `{replacement}`; source value belongs in "
                        "env/onboarding state.",
                    )
                )
            except re.error:
                continue
    return rules


# --------------------------------------------------------------------------- #
# Git helpers                                                                 #
# --------------------------------------------------------------------------- #


def run_git(args: list[str], repo_root: Path) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return res.stdout


def repo_root_or_die() -> Path:
    res = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        sys.stderr.write("compliance-scan: not inside a git repo\n")
        sys.exit(2)
    return Path(res.stdout.strip())


def staged_files(repo_root: Path) -> list[str]:
    out = run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], repo_root)
    return [line for line in out.splitlines() if line]


def push_files(repo_root: Path) -> list[str]:
    upstream = run_git(["rev-parse", "--abbrev-ref", "@{upstream}"], repo_root).strip()
    if not upstream:
        upstream = "origin/main"
    out = run_git(
        ["diff", "--name-only", "--diff-filter=ACMR", f"{upstream}..HEAD"],
        repo_root,
    )
    return [line for line in out.splitlines() if line]


def tree_files(repo_root: Path) -> list[str]:
    tracked = run_git(["ls-files"], repo_root).splitlines()
    untracked = run_git(
        ["ls-files", "--others", "--exclude-standard"], repo_root
    ).splitlines()
    return [p for p in tracked + untracked if p]


def untracked_files(repo_root: Path) -> list[str]:
    out = run_git(["ls-files", "--others", "--exclude-standard"], repo_root)
    return [line for line in out.splitlines() if line]


def file_content_for_scope(path: str, scope: str, repo_root: Path) -> str | None:
    """Return file text. For staged scope, read the staged blob (not the worktree)."""
    if scope == "staged":
        out = subprocess.run(
            ["git", "show", f":{path}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
        if out.returncode != 0:
            return None
        try:
            return out.stdout.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return None
    full = repo_root / path
    if not full.is_file():
        return None
    try:
        return full.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


# --------------------------------------------------------------------------- #
# Scanners                                                                    #
# --------------------------------------------------------------------------- #


LOCKFILE_NAME_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r".*[-_]lock\.json$"),
    re.compile(r".*[-_]lock\.yaml$"),
    re.compile(r".*[-_]lock\.toml$"),
    re.compile(r"^package-lock\.json$"),
    re.compile(r"^pnpm-lock\.yaml$"),
    re.compile(r"^yarn\.lock$"),
    re.compile(r"^uv\.lock$"),
    re.compile(r"^Cargo\.lock$"),
    re.compile(r"^Pipfile\.lock$"),
    re.compile(r"^poetry\.lock$"),
    re.compile(r"^bun\.lockb?$"),
)


def load_allowlist(repo_root: Path) -> list[str]:
    """Return a list of path globs from the allowlist file, or []."""
    path = repo_root / ALLOWLIST_FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []
    entries = data.get("allow", [])
    return [e["path"] for e in entries if isinstance(e, dict) and "path" in e]


_ALLOWLIST_CACHE: list[str] | None = None


def should_skip(path: str, allowlist: list[str] | None = None) -> bool:
    if any(path.startswith(p) for p in SCANNER_SELF_PATHS):
        return True
    suffix = Path(path).suffix.lower()
    if suffix in SKIP_EXTENSIONS:
        return True
    name = Path(path).name
    if any(p.match(name) for p in LOCKFILE_NAME_PATTERNS):
        return True
    if allowlist:
        from fnmatch import fnmatch

        if any(fnmatch(path, glob) for glob in allowlist):
            return True
    return False


def scan_content_layer3_4(
    path: str,
    text: str,
    pii_rules: list[tuple[str, re.Pattern[str], str]],
) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()

    def search(rules, severity: Severity, layer: str) -> None:
        for rule_name, pattern, hint in rules:
            for lineno, line in enumerate(lines, 1):
                m = pattern.search(line)
                if m:
                    findings.append(
                        Finding(
                            severity=severity,
                            layer=layer,
                            rule=rule_name,
                            path=path,
                            line=lineno,
                            snippet=_redact_snippet(line, m),
                            remediation=hint,
                        )
                    )

    search(CRITICAL_PATTERNS, Severity.CRITICAL, "secrets")
    search(HIGH_PATTERNS, Severity.HIGH, "pii-builtin")
    search(pii_rules, Severity.HIGH, "pii-replacements")
    return findings


def _redact_snippet(line: str, match: re.Match[str]) -> str:
    """Show the matched region masked, with up to 40 chars of context each side."""
    start, end = match.span()
    masked = "*" * min(end - start, 8)
    head = line[max(0, start - 40) : start]
    tail = line[end : end + 40]
    return f"{head}[{masked}]{tail}".strip()


def scan_layer5_untracked(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in untracked_files(repo_root):
        is_sensitive = any(path.startswith(p) for p in SENSITIVE_PATH_PREFIXES)
        if not is_sensitive:
            for glob in SENSITIVE_PATH_GLOBS:
                if Path(path).match(glob):
                    is_sensitive = True
                    break
        if not is_sensitive and path.startswith(".claude/skills/"):
            parts = path.split("/")
            if len(parts) >= 3:
                skill_dir = parts[2]
                if any(frag in skill_dir for frag in SENSITIVE_SKILL_FRAGMENTS):
                    is_sensitive = True
        if not is_sensitive:
            continue
        findings.append(
            Finding(
                severity=Severity.INFO,
                layer="untracked-sensitive",
                rule="untracked-in-sensitive-path",
                path=path,
                remediation=(
                    f"Add `{_smallest_ignore_unit(path)}` to .gitignore "
                    "or rerun the scanner with --remediate gitignore."
                ),
            )
        )
    return findings


def _smallest_ignore_unit(path: str) -> str:
    """Pick a sensible .gitignore line for an untracked sensitive path."""
    parts = path.split("/")
    # .env-style files: ignore the file itself
    if parts[-1].startswith(".env") or path.endswith(".key") or path.endswith(".pem"):
        return path
    # .claude/skills/<name>/...  →  .claude/skills/<name>/
    if path.startswith(".claude/skills/") and len(parts) >= 3:
        return f".claude/skills/{parts[2]}/"
    # everything else: ignore the immediate directory
    if len(parts) > 1:
        return f"{parts[0]}/" if len(parts) == 2 else f"{'/'.join(parts[:-1])}/"
    return path


def scan_layer6_privacy_alignment(repo_root: Path) -> list[Finding]:
    """Cross-check PRIVACY.md's 'never leaves' bullets against .gitignore."""
    privacy_md = repo_root / "PRIVACY.md"
    gitignore = repo_root / ".gitignore"
    if not privacy_md.exists() or not gitignore.exists():
        return []

    text = privacy_md.read_text()
    # find the section heading then read bullets until next heading
    section_re = re.compile(
        r"##\s+What never leaves your machine\s*\n(.+?)(?=\n##\s)", re.S
    )
    m = section_re.search(text)
    if not m:
        return []
    bullets = re.findall(r"^[-*]\s+(.+)$", m.group(1), re.M)
    gitignore_text = gitignore.read_text()

    findings: list[Finding] = []
    # look for inline-code-tagged paths in bullets, e.g. `.env`, `notebooks/`
    for bullet in bullets:
        for code in re.findall(r"`([^`]+)`", bullet):
            if "/" not in code and not code.startswith("."):
                continue
            if ":" in code or " " in code:
                continue  # not a path — likely a code identifier or sentence fragment
            normalized = code.rstrip("/")
            if normalized in gitignore_text or f"{normalized}/" in gitignore_text:
                continue
            findings.append(
                Finding(
                    severity=Severity.INFO,
                    layer="privacy-alignment",
                    rule="privacy-md-not-in-gitignore",
                    path="PRIVACY.md",
                    snippet=bullet[:120],
                    remediation=(
                        f"Add `{normalized}` (or matching glob) to .gitignore, "
                        "or remove the claim from PRIVACY.md."
                    ),
                )
            )
    return findings


# --------------------------------------------------------------------------- #
# Layers 1 + 2: orchestrate existing tests                                    #
# --------------------------------------------------------------------------- #


def run_existing_tests(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    pytest_path = repo_root / "tests" / "python" / "test_no_hardcoded_references.py"
    bash_path = repo_root / "tests" / "integration" / "test_gitignore_protection.sh"

    if pytest_path.exists():
        res = subprocess.run(
            ["uv", "run", "pytest", str(pytest_path), "-q", "--no-cov", "--no-header"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            findings.append(
                Finding(
                    severity=Severity.MEDIUM,
                    layer="owner-name",
                    rule="test_no_hardcoded_references",
                    path=str(pytest_path.relative_to(repo_root)),
                    snippet=_tail(res.stdout, 8),
                    remediation=(
                        "Owner name detected outside the allowlist. Replace with "
                        "`{user_name}` template variable or add file to ALLOWED_FILES "
                        "in test_no_hardcoded_references.py with justification."
                    ),
                )
            )

    if bash_path.exists():
        res = subprocess.run(
            ["bash", str(bash_path)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            findings.append(
                Finding(
                    severity=Severity.HIGH,
                    layer="gitignore-coverage",
                    rule="test_gitignore_protection",
                    path=str(bash_path.relative_to(repo_root)),
                    snippet=_tail(res.stdout + res.stderr, 8),
                    remediation=(
                        ".gitignore is missing coverage for one or more sensitive "
                        "paths. Read the test output and harden the patterns."
                    ),
                )
            )
    return findings


def _tail(text: str, n: int) -> str:
    return "\n".join(text.splitlines()[-n:])


# --------------------------------------------------------------------------- #
# Auto-remediation: gitignore                                                 #
# --------------------------------------------------------------------------- #


REMEDIATION_HEADER = "# Compliance scan auto-remediation"


def remediate_gitignore(findings: list[Finding], repo_root: Path) -> list[str]:
    targets: list[str] = []
    for f in findings:
        if f.rule == "untracked-in-sensitive-path":
            unit = _smallest_ignore_unit(f.path)
            if unit not in targets:
                targets.append(unit)
    if not targets:
        return []

    gitignore = repo_root / ".gitignore"
    text = gitignore.read_text() if gitignore.exists() else ""
    existing = set(line.strip() for line in text.splitlines())
    new_targets = [t for t in targets if t not in existing]
    if not new_targets:
        return []

    block = f"\n\n{REMEDIATION_HEADER}\n" + "\n".join(new_targets) + "\n"
    if REMEDIATION_HEADER in text:
        idx = text.index(REMEDIATION_HEADER)
        end = text.find("\n\n", idx)
        end = end if end != -1 else len(text)
        text = text[:end] + "\n" + "\n".join(new_targets) + text[end:]
    else:
        text += block
    gitignore.write_text(text)
    return new_targets


# --------------------------------------------------------------------------- #
# Reporting                                                                   #
# --------------------------------------------------------------------------- #


def render_text(findings: list[Finding], fail_on: Severity, scope: str) -> str:
    if not findings:
        return f"compliance-scan ({scope}): PASS — no findings.\n"
    by_sev: dict[Severity, list[Finding]] = {}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)
    lines = [f"compliance-scan ({scope}): {len(findings)} finding(s)\n"]
    for sev in sorted(by_sev.keys(), reverse=True):
        lines.append(f"\n=== {sev.name} ({len(by_sev[sev])}) ===")
        for f in by_sev[sev]:
            loc = f"{f.path}:{f.line}" if f.line else f.path
            lines.append(f"  [{f.layer}/{f.rule}] {loc}")
            if f.snippet:
                lines.append(f"      {f.snippet}")
            if f.remediation:
                lines.append(f"      → {f.remediation}")
    blocking = [f for f in findings if f.severity >= fail_on]
    verdict = "FAIL" if blocking else "PASS"
    lines.append(
        f"\nVerdict: {verdict} ({len(blocking)} finding(s) at or above {fail_on.name})"
    )
    return "\n".join(lines) + "\n"


def render_md(findings: list[Finding], fail_on: Severity, scope: str) -> str:
    if not findings:
        return f"# Compliance scan — {scope}\n\n**PASS** — no findings.\n"
    lines = [f"# Compliance scan — {scope}\n"]
    by_sev: dict[Severity, list[Finding]] = {}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)
    for sev in sorted(by_sev.keys(), reverse=True):
        lines.append(f"\n## {sev.name} ({len(by_sev[sev])})\n")
        for f in by_sev[sev]:
            loc = f"`{f.path}:{f.line}`" if f.line else f"`{f.path}`"
            lines.append(f"- **{f.layer}/{f.rule}** — {loc}")
            if f.snippet:
                lines.append(f"  - `{f.snippet}`")
            if f.remediation:
                lines.append(f"  - _Fix:_ {f.remediation}")
    blocking = [f for f in findings if f.severity >= fail_on]
    verdict = "FAIL" if blocking else "PASS"
    lines.append(f"\n## Verdict: {verdict}\n")
    lines.append(f"{len(blocking)} finding(s) at or above {fail_on.name}.\n")
    return "\n".join(lines)


def render_json(findings: list[Finding], fail_on: Severity, scope: str) -> str:
    blocking = [f for f in findings if f.severity >= fail_on]
    payload = {
        "scope": scope,
        "fail_on": fail_on.name,
        "findings": [f.to_dict() for f in findings],
        "verdict": "FAIL" if blocking else "PASS",
        "blocking_count": len(blocking),
        "total_count": len(findings),
    }
    return json.dumps(payload, indent=2)


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--scope",
        choices=("staged", "push", "tree"),
        default="staged",
        help="What to scan. staged = git diff --cached; push = upstream..HEAD; tree = full working tree.",
    )
    parser.add_argument(
        "--fail-on",
        type=Severity.parse,
        default=Severity.HIGH,
        help="Minimum severity to fail the scan (CRITICAL, HIGH, MEDIUM, INFO). Default HIGH.",
    )
    parser.add_argument(
        "--severity-floor",
        type=Severity.parse,
        default=Severity.INFO,
        help="Minimum severity to report. Default INFO.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "md"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--remediate",
        choices=("none", "gitignore"),
        default="none",
        help="Auto-remediation. 'gitignore' appends ignore lines for untracked sensitive paths.",
    )
    parser.add_argument(
        "--skip-existing-tests",
        action="store_true",
        help="Skip layers 1 and 2 (the existing pytest + bash tests). Use for fast inner-loop runs.",
    )
    args = parser.parse_args()

    repo_root = repo_root_or_die()
    pii_rules = load_pii_replacement_patterns(repo_root)
    allowlist = load_allowlist(repo_root)

    # Choose file list
    if args.scope == "staged":
        files = staged_files(repo_root)
    elif args.scope == "push":
        files = push_files(repo_root)
    else:
        files = tree_files(repo_root)

    findings: list[Finding] = []

    # Layer 3 + 4: content scan
    for path in files:
        if should_skip(path, allowlist):
            continue
        text = file_content_for_scope(path, args.scope, repo_root)
        if text is None:
            continue
        findings.extend(scan_content_layer3_4(path, text, pii_rules))

    # Layer 5: untracked sensitive paths (only meaningful for tree scope)
    if args.scope == "tree":
        findings.extend(scan_layer5_untracked(repo_root))

    # Layer 6: PRIVACY.md alignment
    findings.extend(scan_layer6_privacy_alignment(repo_root))

    # Layers 1 + 2: existing tests (slow; gated)
    if not args.skip_existing_tests and args.scope in ("tree", "push"):
        findings.extend(run_existing_tests(repo_root))

    # Auto-remediation
    remediated: list[str] = []
    if args.remediate == "gitignore":
        remediated = remediate_gitignore(findings, repo_root)
        if remediated:
            sys.stderr.write(
                f"compliance-scan: appended {len(remediated)} entries to .gitignore: "
                + ", ".join(remediated)
                + "\n"
            )
            # Drop now-resolved INFO findings from the report
            findings = [
                f
                for f in findings
                if not (
                    f.rule == "untracked-in-sensitive-path"
                    and _smallest_ignore_unit(f.path) in remediated
                )
            ]

    # Filter by severity floor
    findings = [f for f in findings if f.severity >= args.severity_floor]

    # Render
    renderer = {"text": render_text, "json": render_json, "md": render_md}[args.format]
    sys.stdout.write(renderer(findings, args.fail_on, args.scope))

    blocking = [f for f in findings if f.severity >= args.fail_on]
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
