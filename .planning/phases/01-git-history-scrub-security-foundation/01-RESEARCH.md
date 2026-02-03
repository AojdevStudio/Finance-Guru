# Phase 1: Git History Scrub & Security Foundation - Research

**Researched:** 2026-02-02
**Domain:** Git history rewriting, PII scrubbing, secrets detection, CI security gates
**Confidence:** HIGH

## Summary

This phase addresses a critical prerequisite for public release: the git history contains severe PII exposure across 157 commits. The audit found **1,645 matches** for the primary PII search pattern (`account|brokerage|Z057|net.worth|LLC`) in `git log --all -p`. Specific exposures include a real Fidelity brokerage account number (Z05724592), real financial data ($192K brokerage value, $365K mortgage, $500K net worth), LLC names (MaryFinds LLC, KC Ventures Consulting Group LLC), employer names (Avanade, CBN), a Google Sheets spreadsheet ID (1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4), a Bright Data API token committed in .mcp.json, personal email addresses (admin@kamdental.com, admin@unifiedental.com), and the full Google Forms financial assessment CSV with detailed personal financial data.

The standard approach uses `git-filter-repo --replace-text` with an expressions file to scrub PII from all blob content across history, `--replace-message` to scrub commit messages, and `--mailmap` to rewrite author identities. Post-scrub, a `gitleaks` pre-commit hook prevents future PII leaks, and a CI grep test validates zero PII matches on every push.

**Primary recommendation:** Fresh clone, run git-filter-repo with comprehensive expressions file, delete old GitHub repo, create new one, push cleaned history. This is the only approach that guarantees PII removal from GitHub's infrastructure.

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| git-filter-repo | latest (installed at /opt/homebrew/bin) | Rewrite git history to scrub PII from blobs and messages | Official git-scm recommended replacement for git-filter-branch. Orders of magnitude faster. Single Python file, no deps beyond Git 2.36+ and Python 3.6+ |
| gitleaks | v8.28.0 (installed at /opt/homebrew/bin) | Pre-commit secrets scanning and full-history audit | Industry standard for secrets detection. TOML config for custom rules. Pre-commit integration. Go binary, no runtime deps |

### Supporting
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| pre-commit | v4.5.1 | Git hook management framework | Manages gitleaks hook installation, auto-updates, consistent team experience |
| grep (builtin) | N/A | CI PII pattern verification | Success criteria #1 validation: `git log --all -p \| grep -iE "pattern"` returns zero |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| git-filter-repo | BFG Repo-Cleaner | BFG is simpler for file deletion but lacks `--replace-text` with regex. git-filter-repo is more flexible for text replacement within files |
| gitleaks | trufflehog | Trufflehog is stronger at entropy-based detection but gitleaks has better custom rule TOML config and simpler pre-commit integration |
| gitleaks | detect-secrets (Yelp) | detect-secrets uses a baseline file approach, good for reducing false positives but heavier setup. gitleaks is simpler for this use case |
| pre-commit framework | Manual git hooks | Manual hooks work but pre-commit handles versioning, auto-install, and multi-language hooks cleanly |

**Installation:**
```bash
# Already installed:
# git-filter-repo: /opt/homebrew/bin/git-filter-repo
# gitleaks: /opt/homebrew/bin/gitleaks v8.28.0

# Needs installation:
brew install pre-commit   # or: pip install pre-commit
# Alternatively, skip pre-commit framework and use gitleaks directly as a git hook
```

## Architecture Patterns

### Recommended Project Structure (new files this phase creates)
```
.
├── .gitleaks.toml              # Custom gitleaks rules for this repo's PII patterns
├── .pre-commit-config.yaml     # Pre-commit hook configuration
├── .gitignore                  # Updated with comprehensive protection
├── .github/
│   └── workflows/
│       └── pii-check.yml       # CI workflow for PII grep test (SEC-03)
└── scripts/
    └── qa/
        └── pii-audit.sh        # Reusable PII pattern grep script
```

### Pattern 1: Expressions File for git-filter-repo
**What:** A text file listing all PII patterns to replace across entire git history.
**When to use:** During the one-time history rewrite (SEC-01).
**Example:**
```
# File: pii-replacements.txt
# Format: pattern==>replacement (or just pattern for default ***REMOVED***)
# Prefix: literal: (default), regex:, glob:

# Fidelity account number
literal:Z05724592==>REDACTED_ACCOUNT
regex:Z0\d{7,}==>REDACTED_ACCOUNT

# Google Sheets spreadsheet ID
literal:1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4==>REDACTED_SPREADSHEET_ID

# Bright Data API token
literal:9424526a719032acbe090cc883accedb1b7eb167e89f855d78a7a0fec0aaf441==>REDACTED_API_TOKEN

# LLC names
literal:MaryFinds LLC==>REDACTED_LLC_1
literal:KC Ventures Consulting Group LLC==>REDACTED_LLC_2

# Employer names
literal:Avanade==>REDACTED_EMPLOYER_1
literal:CBN==>REDACTED_EMPLOYER_2

# Personal financial amounts from user-profile.yaml
literal:365139.76==>REDACTED_AMOUNT
literal:1712.68==>REDACTED_AMOUNT

# Personal name
literal:Ossie Irondi==>REDACTED_NAME
literal:Ossie==>REDACTED_NAME

# Email addresses
literal:admin@kamdental.com==>redacted@example.com
literal:admin@unifiedental.com==>redacted@example.com

# File paths with account numbers
regex:Balances_for_Account_Z\d+==>Balances_for_Account_REDACTED
regex:History_for_Account_Z\d+==>History_for_Account_REDACTED

# CSV filename pattern
regex:Portfolio_Positions_\w+-\d+-\d+\.csv==>Portfolio_Positions_REDACTED.csv
```

### Pattern 2: Mailmap for Author Rewriting
**What:** Rewrite git author names and emails to generic identifiers.
**When to use:** During history rewrite to remove personal email addresses from commit metadata.
**Example:**
```
# File: .mailmap
# Format: New Name <new@email> Old Name <old@email>
Finance Guru Developer <dev@example.com> AOJDevStudio <admin@unifiedental.com>
Finance Guru Developer <dev@example.com> AOJDevStudio <admin@kamdental.com>
Finance Guru Developer <dev@example.com> Ossie Irondi <admin@unifiedental.com>
```

### Pattern 3: Custom Gitleaks Rules
**What:** TOML configuration file with custom regex rules for this repo's specific PII patterns.
**When to use:** Permanently, as a pre-commit hook and CI scan.
**Example:**
```toml
# .gitleaks.toml
title = "Finance Guru PII Detection"

[[rules]]
id = "fidelity-account-number"
description = "Fidelity brokerage account number pattern"
regex = '''Z0\d{7,}'''
keywords = ["Z0", "Account"]

[[rules]]
id = "google-sheets-id"
description = "Google Sheets spreadsheet ID (44 chars)"
regex = '''[A-Za-z0-9_-]{44}'''
entropy = 3.5
keywords = ["spreadsheet", "sheets", "docs.google.com"]

[[rules]]
id = "personal-llc-names"
description = "Known LLC business entity names"
regex = '''(?i)(MaryFinds|KC\s*Ventures\s*Consulting\s*Group)\s*LLC'''
keywords = ["LLC"]

[[rules]]
id = "employer-names"
description = "Known employer names"
regex = '''\b(Avanade|CBN)\b'''
keywords = ["Avanade", "CBN"]

[[rules]]
id = "personal-names"
description = "Personal name references"
regex = '''(?i)\b(Ossie|Irondi)\b'''
keywords = ["Ossie", "Irondi"]

[[rules]]
id = "brightdata-api-token"
description = "Bright Data API token pattern"
regex = '''[a-f0-9]{64}'''
entropy = 4.0
keywords = ["API_TOKEN", "api_token"]

[allowlist]
description = "Global allowlists"
paths = [
  '''\.gitleaks\.toml''',
  '''\.planning/phases/.*/.*-RESEARCH\.md''',
]
```

### Anti-Patterns to Avoid
- **Partial scrub then push:** Running git-filter-repo with an incomplete expressions file, pushing, then discovering missed PII. This is IRREVERSIBLE -- once pushed publicly, PII is exposed forever. The expressions file MUST be comprehensive before running.
- **Force-pushing to existing repo:** GitHub caches old objects in protected namespaces (refs/pull/*). Force-pushing does NOT guarantee old commits are purged from GitHub's infrastructure. Delete the repo and create a new one.
- **Using git-filter-branch:** Deprecated, slow, error-prone. Always use git-filter-repo.
- **Only scrubbing blobs, not messages:** Commit messages may contain PII (account numbers, names, financial details). Must use BOTH `--replace-text` and `--replace-message`.
- **Forgetting author metadata:** Git commits contain author name and email. `--mailmap` must be used to rewrite these.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Git history rewriting | Custom git-filter-branch scripts | git-filter-repo `--replace-text` | filter-repo handles edge cases (binary files, merge commits, empty commits, encoding) that custom scripts miss |
| Secrets detection | Custom grep-based pre-commit hook | gitleaks with `.gitleaks.toml` | gitleaks handles entropy analysis, regex, path filtering, allowlists, and 150+ built-in rules for common secret patterns |
| Hook management | Manual `.git/hooks/` scripts | pre-commit framework | pre-commit handles installation, versioning, environment isolation, and works across clones |
| PII pattern matching | Simple string grep | Regex patterns with word boundaries | Simple grep for "CBN" would match legitimate uses like variable names. Regex with `\b` boundaries is essential |

**Key insight:** The history rewrite is a one-shot, irreversible operation. The consequences of getting it wrong (PII exposed publicly forever) vastly outweigh the cost of using proven tools with comprehensive pattern coverage.

## Common Pitfalls

### Pitfall 1: Incomplete PII Pattern List
**What goes wrong:** The expressions file misses a PII pattern. After force-push, someone clones the repo and discovers the missed PII in history. Cannot be undone.
**Why it happens:** PII patterns are scattered across many formats: account numbers in filenames, dollar amounts in commit messages, names in author fields, spreadsheet IDs in code, API tokens in config files.
**How to avoid:** Run the full audit grep BEFORE creating the expressions file. After running git-filter-repo, verify with `git log --all -p | grep -iE "pattern"` on the filtered clone BEFORE pushing anywhere.
**Warning signs:** The audit found 1,645 matches. If the post-scrub verification finds any matches, the scrub is incomplete.

### Pitfall 2: Generic Patterns Causing Collateral Damage
**What goes wrong:** A regex like `\d{6,}` intended to catch account numbers also replaces legitimate code (timestamps, line numbers, hash values), breaking the codebase.
**Why it happens:** Overly broad patterns match unintended content.
**How to avoid:** Use literal replacements for known PII values first. Only use regex for patterns that are genuinely unique to PII (e.g., `Z0\d{7,}` not `\d{7,}`). Test on a throwaway clone before the real run.
**Warning signs:** After filter-repo, run tests to verify code still works. Check for broken references, corrupted data.

### Pitfall 3: CBN as Employer vs CBN as Acronym
**What goes wrong:** Replacing "CBN" globally corrupts unrelated content. CBN could appear in contexts like "CBN 401(k) Plan" (PII - employer plan name) but also potentially in other legitimate uses.
**Why it happens:** Short strings match broadly.
**How to avoid:** Use `\bCBN\b` (word boundary) in regex and manually review the match list before scrubbing. Consider using `--blob-callback` for context-aware replacement if simple regex causes too many false positives. Alternatively, target only the specific file paths where CBN appears in PII context.
**Warning signs:** grep -c for the pattern returns more matches than expected PII occurrences.

### Pitfall 4: Forgetting to Scrub Commit Messages
**What goes wrong:** File contents are clean but commit messages still contain "Z05724592" or "MaryFinds LLC" or financial amounts.
**Why it happens:** `--replace-text` only operates on blob content (file data). Commit messages require `--replace-message`.
**How to avoid:** Use BOTH `--replace-text expressions.txt` AND `--replace-message expressions.txt` in the same git-filter-repo invocation.
**Warning signs:** Post-scrub, `git log --all --oneline | grep -i "PII_PATTERN"` still returns matches.

### Pitfall 5: GitHub Retains Old Objects
**What goes wrong:** After force-pushing rewritten history to the SAME repo, GitHub's object cache, pull request refs, and fork network still contain the original PII-laden commits.
**Why it happens:** GitHub stores objects in protected namespaces that force-push cannot overwrite. Old PR refs persist.
**How to avoid:** Delete the GitHub repository entirely. Create a new repository. Push the cleaned history to the new repo. This is the ONLY way to guarantee GitHub's infrastructure does not retain old objects.
**Warning signs:** `gh api repos/OWNER/REPO/git/commits/OLD_SHA` still returns data for pre-rewrite commit SHAs.

### Pitfall 6: Collaborator Clones Retain Old History
**What goes wrong:** Anyone who cloned the repo before the scrub still has the full PII in their local .git directory.
**Why it happens:** Git is distributed -- every clone has the complete history.
**How to avoid:** For this repo (private, single developer), verify no other clones exist. After scrub, delete ALL local copies except the freshly filtered clone. If GitHub Actions runners cached the repo, clear those caches too.
**Warning signs:** N/A for single-developer repo, but important for any future collaborators.

### Pitfall 7: .onboarding-progress.json / .onboarding-state.json Not in .gitignore
**What goes wrong:** The .gitignore lists `.onboarding-state.json` but the requirements specify `.onboarding-progress.json`. If the filename was changed, the old name might not be covered.
**Why it happens:** Requirements and implementation can drift.
**How to avoid:** Add BOTH patterns to .gitignore. Verify with `git check-ignore` after updating.
**Warning signs:** `git ls-files | grep onboarding` returns unexpected results.

## Code Examples

### Example 1: Full git-filter-repo Invocation
```bash
# Source: git-filter-repo official documentation
# MUST be run on a fresh clone

# Step 1: Fresh clone
git clone https://github.com/AojdevStudio/Finance-Guru.git finance-guru-clean
cd finance-guru-clean

# Step 2: Run filter-repo with all replacements
git filter-repo \
  --replace-text ../pii-replacements.txt \
  --replace-message ../pii-replacements.txt \
  --mailmap ../author-mailmap.txt \
  --force

# Step 3: Verify scrub is complete
git log --all -p | grep -ciE "Z05724592|MaryFinds|KC Ventures|Avanade|1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4|admin@kamdental|admin@unifiedental|9424526a719032acbe090cc883accedb1b7eb167e89f855d78a7a0fec0aaf441"
# MUST return 0

# Step 4: Verify the broader pattern
git log --all -p | grep -ciE "account|brokerage|Z057|net.worth|LLC"
# Review remaining matches -- some may be legitimate (e.g., "account" in code comments about generic accounts)

# Step 5: Run tests to verify code integrity
uv run pytest

# Step 6: Push to NEW repo (old repo deleted first)
git remote add origin https://github.com/NEW_ORG/Finance-Guru.git
git push --force --all origin
git push --force --tags origin
```

### Example 2: Gitleaks Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
# Source: gitleaks GitHub README
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.24.2
    hooks:
      - id: gitleaks
```

### Example 3: CI PII Grep Test (GitHub Actions)
```yaml
# .github/workflows/pii-check.yml
name: PII Check

on: [push, pull_request]

jobs:
  pii-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for thorough scan

      - name: Check for known PII patterns in working tree
        run: |
          # Patterns specific to this repo's known PII
          PATTERNS="Z05724592|Z0[0-9]{7,}|MaryFinds|KC.Ventures|1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4|admin@kamdental|admin@unifiedental|9424526a[a-f0-9]{56}"

          # Scan all tracked files (exclude binary, test fixtures, and this workflow itself)
          MATCHES=$(git ls-files | grep -v '.github/workflows/pii-check.yml' | xargs grep -rlE "$PATTERNS" 2>/dev/null || true)

          if [ -n "$MATCHES" ]; then
            echo "FAIL: PII patterns found in these files:"
            echo "$MATCHES"
            exit 1
          fi

          echo "PASS: No PII patterns found in working tree"

      - name: Scan git history for PII
        run: |
          PATTERNS="Z05724592|MaryFinds LLC|KC Ventures|1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4|admin@kamdental|admin@unifiedental"
          COUNT=$(git log --all -p | grep -ciE "$PATTERNS" || true)

          if [ "$COUNT" -gt 0 ]; then
            echo "FAIL: Found $COUNT PII pattern matches in git history"
            exit 1
          fi

          echo "PASS: Zero PII matches in git history"

      - name: Run gitleaks on full history
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Example 4: Updated .gitignore Additions (ONBD-15)
```gitignore
# --- Additions for ONBD-15 ---

# User financial profile (CRITICAL - contains real financial data)
fin-guru/data/user-profile.yaml

# Onboarding state files (both known names)
.onboarding-state.json
.onboarding-progress.json

# Environment files (API keys)
.env
.env.*

# Private analysis and reports
fin-guru-private/

# CSV exports (may contain account data)
*.csv
!tests/python/fixtures/sample_transactions.csv

# MCP config (contains API tokens)
.mcp.json
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| git-filter-branch | git-filter-repo | 2020+ (git-scm official recommendation) | 10-50x faster, safer, handles edge cases |
| BFG Repo-Cleaner | git-filter-repo --replace-text | 2020+ | BFG only does file deletion and simple replacement. git-filter-repo supports regex, message rewriting, author rewriting in one pass |
| Manual .git/hooks/ scripts | pre-commit framework + gitleaks | 2023+ standard | Versioned, reproducible, auto-installing hooks |
| Custom grep CI tests | gitleaks-action + custom grep | Current | Layered approach: gitleaks catches standard secrets, custom grep catches repo-specific PII |

**Deprecated/outdated:**
- **git-filter-branch:** Officially deprecated by git-scm. Has "plethora of pitfalls that can produce non-obvious manglings." Use git-filter-repo.
- **BFG Repo-Cleaner:** Still works but limited to file deletion and simple text replacement. Cannot do regex, cannot rewrite commit messages, cannot rewrite authors. git-filter-repo does all of these.

## PII Audit Results (Critical Input for Planning)

### Confirmed PII in Git History

| Category | Pattern | Occurrences in History | In Working Tree | Severity |
|----------|---------|----------------------|-----------------|----------|
| Fidelity Account Number | `Z05724592` | ~15 commits | 13 tracked files | CRITICAL |
| Google Sheets ID | `1HtHRP3CbnOePb8RQ0RwzFYOQxk0uWC6L8ZMJeQYfWk4` | ~10 commits | 3 tracked files | HIGH |
| Bright Data API Token | `9424526a719032...` | 4 occurrences | 0 (deleted from tree) | CRITICAL |
| LLC Name: MaryFinds | `MaryFinds LLC` | ~5 commits | 0 (in planning docs only) | HIGH |
| LLC Name: KC Ventures | `KC Ventures Consulting Group LLC` | ~5 commits | 0 (in planning docs only) | HIGH |
| Employer: Avanade | `Avanade` | ~3 commits | 0 (in planning docs only) | MEDIUM |
| Employer: CBN | `CBN` | ~5 commits | 2 tracked files | MEDIUM |
| Personal Name | `Ossie Irondi` / `Ossie` | ~20+ commits | 21 tracked files | MEDIUM |
| Email: kamdental | `admin@kamdental.com` | In author metadata | In author metadata | HIGH |
| Email: unifiedental | `admin@unifiedental.com` | In author metadata | In author metadata | HIGH |
| Financial Assessment CSV | Full financial survey data | 2 commits (added then deleted) | 0 (deleted from tree) | CRITICAL |
| user-profile.yaml | $192K brokerage, holdings, mortgage | 2 commits (added then deleted) | 0 (gitignored) | CRITICAL |
| .mcp.json | API token | 3 commits (added, modified, deleted) | 0 (gitignored) | CRITICAL |
| File naming: Account_ | `Balances_for_Account_Z05724592.csv` | ~8 commits | 13 tracked files | HIGH |
| Mortgage balance | `365139.76` | ~3 commits | 0 | MEDIUM |

### Files in Working Tree Requiring Cleanup (ONBD-14)

**13 tracked files** still contain `Z05724592` in the working tree:
1. `.claude/hooks/load-fin-core-config.ts`
2. `.claude/skills/PortfolioSyncing/SKILL.md`
3. `.claude/skills/PortfolioSyncing/workflows/SyncPortfolio.md`
4. `.claude/skills/TransactionSyncing/SKILL.md`
5. `.claude/skills/TransactionSyncing/workflows/SyncTransactions.md`
6. `.claude/skills/fin-core/SKILL.md`
7. `.claude/skills/margin-management/SKILL.md`
8. `.planning/research/PITFALLS.md`
9. `.planning/research/SUMMARY.md`
10. `docs/hooks.md`
11. `fin-guru/tasks/load-portfolio-context.md`
12. `tests/integration/gitignore-protection.test.ts`
13. `tests/integration/test_gitignore_protection.sh`

**3 tracked files** contain the Google Sheets spreadsheet ID.
**2 tracked files** contain "CBN" as employer reference.
**21 tracked files** contain "Ossie" or "Irondi" references.

### .gitignore Gaps (ONBD-15)

Current .gitignore coverage:
- `.env` -- COVERED
- `user-profile.yaml` -- COVERED (via `fin-guru/data/user-profile.yaml`)
- `fin-guru-private/` -- COVERED
- `.mcp.json` -- COVERED
- `*.csv` -- COVERED
- `.onboarding-state.json` -- COVERED
- `notebooks/` -- COVERED

**Gaps identified:**
- `.onboarding-progress.json` -- NOT in .gitignore (requirements specify this filename)
- `user-profile.yaml` only covers the specific path, not the filename globally

### Author Metadata Exposure

Git commit author fields contain:
- `AOJDevStudio <admin@unifiedental.com>` (majority of commits)
- `AOJDevStudio <admin@kamdental.com>` (older commits)
- `Ossie Irondi <admin@unifiedental.com>` (1 commit)
- `Claude <noreply@anthropic.com>` (co-author, safe to keep)

### Remote Repository Status

- **Remote:** `https://github.com/AojdevStudio/Finance-Guru.git` (currently private)
- **Commits:** 157 total
- **Recommendation:** Delete this repo after scrub. Create new repo. Push cleaned history.

## Open Questions

1. **What should replace personal references in working tree files?**
   - The 13 files with `Z05724592` need the account number replaced with a variable/placeholder. What format? `{ACCOUNT_NUMBER}`, `EXAMPLE_ACCOUNT`, or something else?
   - Recommendation: Use template variables like `{account_id}` for code, `EXAMPLE_ACCOUNT_123` for documentation examples, consistent with the existing `{user_name}` pattern.

2. **Should author identity be anonymized or just genericized?**
   - `AOJDevStudio` username is linked to GitHub profile. Is this PII?
   - Recommendation: Rewrite to a generic identity since the repo is going public. Use `Finance Guru Developer <dev@example.com>` or keep `AOJDevStudio` but replace the real email addresses.

3. **Should planning/research docs that mention PII be scrubbed or excluded?**
   - `.planning/research/PITFALLS.md` and `.planning/research/SUMMARY.md` contain PII references as part of documenting the problem. Should these be cleaned or is `.planning/` going to be gitignored?
   - Recommendation: If `.planning/` stays tracked, scrub PII from those files too. Consider whether planning docs should be in the public repo at all.

4. **What about the "CBN" false positive risk?**
   - "CBN" is only 3 characters and appears in contexts like "CBN 401(k) Plan" and "CBN 401k". How aggressively should this be scrubbed?
   - Recommendation: Use `regex:\bCBN\s+401` to target the specific PII context rather than all "CBN" occurrences.

5. **Bright Data API token -- needs rotation?**
   - The token `9424526a...` was committed and is permanently in git history until scrubbed. Even after scrub, if anyone ever cloned this repo, the token is compromised.
   - Recommendation: Rotate this token immediately, regardless of the scrub timeline. Mark as CRITICAL action item.

## Sources

### Primary (HIGH confidence)
- **git-filter-repo official docs** (`Documentation/git-filter-repo.txt` from repo) -- `--replace-text` expressions file format, `--replace-message`, `--mailmap`, `--blob-callback`, regex prefix syntax
- **gitleaks v8.28.0** (installed locally, verified) -- TOML config format, rule structure, pre-commit hook
- **git-filter-repo GitHub** (https://github.com/newren/git-filter-repo) -- Installation, requirements (Git >= 2.36.0, Python 3 >= 3.6)
- **gitleaks GitHub** (https://github.com/gitleaks/gitleaks) -- v8.24.2+ config, custom rules, pre-commit integration
- **pre-commit.com** -- v4.5.1, installation, .pre-commit-config.yaml format
- **Local audit** -- Direct grep of git history and working tree (157 commits, 1,645 pattern matches)

### Secondary (MEDIUM confidence)
- **git-filter-repo FAQ and issues** (https://github.com/newren/git-filter-repo/issues/227) -- GitHub caching behavior, force-push limitations, recommendation to delete and recreate repo
- **GitHub docs** (https://docs.github.com/enterprise-cloud@latest/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) -- Official guidance on removing sensitive data
- **gitleaks default config** (https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml) -- Rule format with id, description, regex, entropy, keywords, allowlists

### Tertiary (LOW confidence)
- **Community patterns** for CI PII scanning workflows -- assembled from multiple GitHub Actions examples. Needs validation in actual CI environment.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - git-filter-repo and gitleaks are installed locally, versions verified, official docs consulted
- Architecture: HIGH - Based on official documentation for expressions file format, mailmap, gitleaks TOML config
- Pitfalls: HIGH - Based on direct audit of this repo's actual PII exposure (1,645 real matches found) and official git-filter-repo documentation on limitations
- PII inventory: HIGH - Based on direct grep of actual git history, not hypothetical patterns

**Research date:** 2026-02-02
**Valid until:** 2026-03-04 (30 days -- tools are stable, PII inventory is snapshot-in-time)
