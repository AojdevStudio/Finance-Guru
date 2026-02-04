# Phase 3: Onboarding Wizard - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Interactive CLI wizard that collects a new user's financial profile across 8 sections and generates personalized config files (user-profile.yaml, CLAUDE.md, .env). Porting the existing TypeScript scaffold (scripts/onboarding/sections/) to Python using the `questionary` library. Save/resume is Phase 4 — this phase covers the core wizard flow and config generation.

</domain>

<decisions>
## Implementation Decisions

### Question interaction style
- Predefined choices (risk tolerance, investment philosophy, time horizon): **arrow-key select menus** using `questionary.select()`
- Multi-select questions (focus areas): **checkbox lists** using `questionary.checkbox()` with space-to-toggle
- Dollar amounts and numbers: **plain text with smart parsing** — accept `$25,000`, `25000`, `25k` formats, all normalized internally
- Free-text lists (account structure, account list): **comma-split into YAML list** — user types "Fidelity, Vanguard 401k, Roth IRA" and it becomes a list in the YAML
- Percentages: **human-friendly input** — user types `4.5` meaning 4.5%, stored as `0.045` internally. Prompt says: "e.g., 4.5 for 4.5%"

### Section flow and ordering
- **Two-stage flow:**
  - Stage 1 (Financial): Liquid Assets -> Investments -> Cash Flow -> Debt -> Preferences -> **Summary/Review**
  - Stage 2 (Config): Broker Selection -> Env Setup -> **Config Generation**
- **8 total sections** — all sections are required entry (user must go through each one)
- Within each section, individual questions can be optional (e.g., account structure description, focus areas)
- Broker selection and env setup are **both required** sections (not skippable)
- At summary/review: if user says "something's wrong", show numbered section list — user picks which section to redo, only that section re-runs, then back to summary

### Validation and error handling
- **Inline correction with example** on validation failure: "That doesn't look like a dollar amount. Try: 25000, $25,000, or 25k"
- **Retry counter visible**: "Invalid input (attempt 2/3). Try: $25,000"
- After 3 failed attempts on a required field: offer skip with `(y/n)` prompt
- Skipped required fields stored as **null** — summary shows "Not provided", agents handle missing data gracefully
- Percentage fields accept human-friendly input (4.5 = 4.5%), converted to decimal internally

### Welcome and completion UX
- **Welcome screen**: Large, beautiful ASCII art banner for Finance Guru branding + brief explanation of what onboarding does + estimated section count + what files will be created
- **Progress indicator**: Both section header with counter ("Section 3 of 8: Cash Flow") AND a visual progress bar
- **Completion screen**: Celebratory banner/ASCII art + list of all generated files with checkmarks + clear "Next steps" (launch Claude Code, activate Finance Guru)
- **Env setup section**: Each API key prompt shows what the key unlocks — "Alpha Vantage API key (unlocks real-time market data in spreadsheet). Skip if not needed:"

### Claude's Discretion
- ASCII art design for welcome and completion banners
- Exact wording of section introductions and transitions
- Progress bar visual style (characters, width)
- Error message wording per field type (as long as it follows the "inline correction with example" pattern)
- How the "jump to section" re-edit flow presents the numbered list

</decisions>

<specifics>
## Specific Ideas

- Two-stage flow separates "telling Finance Guru about your finances" from "configuring the system" — the financial summary/review happens before any config steps
- The TS scaffold (scripts/onboarding/sections/) is the blueprint for question content — Python port should have the same data collection but use questionary's richer interaction patterns
- Smart dollar parsing (25k, $25,000, 25000) is a key usability win over the TS scaffold's strict validation

</specifics>

<deferred>
## Deferred Ideas

- Save/resume (Ctrl+C handling, .onboarding-progress.json) — Phase 4
- Hook cleanup and Bun TypeScript ports — Phase 4
- Regression test suite for onboarding — Phase 4

</deferred>

---

*Phase: 03-onboarding-wizard*
*Context gathered: 2026-02-03*
