<!-- Finance Guru adaptation of BMAD create-doc -->

# Create Finance Guru Deliverable from Template

## ⚠️ EXECUTION-CRITICAL GUIDANCE ⚠️

This workflow drives interactive creation of Finance Guru artifacts (analysis reports, investment memos, presentations). It MUST be run step-by-step with user feedback. Skipping the elicitation steps violates compliance and quality guardrails.

1. **No automation shortcuts.** Disable batching; process one section at a time.
2. **Elicitation is mandatory** whenever `elicit: true` in the template metadata.
3. **Respect compliance language.** Ensure disclaimers from `compliance-policy.md` remain verbatim.

## Template Discovery

If the user does not specify a template, list options under `{project-root}/fin-guru/templates/` (e.g., `analysis-report.md`, `presentation-format.md`, `excel-model-spec.md`). Ask which deliverable they need and confirm output filename + format.

If the selected template is `buy-ticket-template.md`, treat it as a canonical trade ticket with a stricter contract:

- Do not create buy tickets from Builder or generic document-only routing; hand off to Strategy Advisor or Dividend Specialist first
- Require upstream portfolio context before drafting
- Confirm deployment amount and available cash buffer
- Require a concrete allocation table with tickers, dollars, weights, prices, and shares
- Require strategy rationale, risk notes, and a price snapshot timestamp
- Save the final ticket under `tickets/`

## Buy Ticket Contract

When creating a buy ticket, do not draft from vague strategy text alone. Confirm the ticket includes all of the following before it is considered complete:

1. Portfolio context loaded from current holdings/balances
2. Explicit deployment amount and available cash
3. Structured execution summary with ticker-level allocations
4. Current price snapshot with timestamp/source
5. Strategy rationale by category or bucket
6. Risk notes relevant to sizing, concentration, volatility, or margin
7. Sources & assumptions block plus the full disclaimer block

ITC risk is a hard cap for supported tickers. The cap reads only successful Layer 3 output, never model-returned fields; a missing, not-run, or failed Layer 3 result blocks ticket generation. Include an ITC advisory section when the Layer 3 signal is materially elevated.

## Interactive Section Processing

For each template section:

1. Load section metadata (owners/editors, elicitation flag, finance context).
2. Draft content following Finance Guru analytical workflow:
   - Align with research → quant → strategy → artifact phases.
   - Cite assumptions, data sources, and timestamps per OutputPolicy.
   - Integrate risk metrics (VaR, drawdowns) and strategy notes when relevant.
   - For buy tickets, preserve the canonical structure: YAML frontmatter + `## Execution Summary` table + rationale/risk/source sections.
3. Provide **detailed rationale** covering:
   - Financial assumptions (rates, fees, tax settings, scenario ranges)
   - Trade-offs made across strategies (margin buffers vs. yield targets)
   - Compliance considerations or disclaimers inserted
4. When `elicit: true`:
   - Present the drafted section + rationale.
   - Offer numbered options using the Finance Guru elicitation format:
     ```text
     **Finance Guru Review Options**
     Choose 1-9:
     1. Proceed to next section
     2. Expand for institutional stakeholders
     3. Critique quantitative robustness
     4. Identify regulatory/compliance risks
     5. Stress-test margin or liquidity assumptions
     6. Align with user’s investment policy statement
     7. Explore alternative strategy angles
     8. Surface tax optimization opportunities
     9. Proceed / No Further Actions
     ```
   - Wait for input before continuing. If user supplies custom feedback, incorporate it and re-offer the menu until they select option 9 or explicitly move on.

## Permissions Handling

- If `owner` or `editors` metadata is present, mention in the document: _"(Owned by {agent}; edits restricted to {roles})"_
- Escalate to the orchestrator if a user request conflicts with ownership rules (e.g., compliance-only sections).

## Saving & Output Policy

- Confirm desired file format using Finance Guru overrides: `[format:xlsx|pptx|pdf|md]`, `[save:/finance/reports/name.ext]`.
- Save analysis reports, memos, presentations, and other research artifacts under `analysis/`.
- Save buy tickets under `tickets/`.
- Append Sources & Assumptions section summarizing:
  - Data sources with timestamps
  - Key assumptions (rates, tax brackets, margin costs)
  - Limitations or data gaps
- Embed compliance disclaimer block:
  - “This is educational analysis, not personalized investment advice.”
  - “Past performance does not guarantee future results.”
  - “Consult a licensed advisor before acting.”

## YOLO Mode

User may enter `#yolo` to process all sections without pauses. When in YOLO mode:

- Still generate detailed rationale per section.
- Summarize outstanding risks or decisions at the end.
- Offer to rerun specific sections interactively if the user wants revisions.

## Final Review Checklist

Before finishing, confirm:

- All sections completed and validated through elicitation or YOLO summary
- Disclaimers, assumptions, and next steps present
- Any models or appendices referenced have been generated or linked
- User approves saving/export instructions
- Buy tickets include portfolio context, execution summary, price snapshot, and risk notes
- Optionally hand off to Compliance Officer for a final audit
