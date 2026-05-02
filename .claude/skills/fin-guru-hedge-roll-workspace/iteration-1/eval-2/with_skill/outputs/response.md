# Hedge Skill Eval — Mode Selection Response

**Date:** 2026-04-22
**User input:** "Let's start protecting my portfolio."
**Skill:** fin-guru-hedge-roll

---

## Mode-Selection Reasoning

The user's phrasing "Let's start protecting my portfolio" is **ambiguous** under the skill's mode-selection rules.

### Signal analysis

| Phrase fragment | Possible interpretation |
|---|---|
| "start" | Suggests initiating something new → OPEN |
| "protecting" | Protective puts → could be OPEN, ROLL, or CLOSE-related |
| No mention of "roll", "renew", "close", "unwind" | Neither ROLL nor CLOSE is explicit |
| No mention of "I don't have puts yet" or "existing puts" | Portfolio state unknown from phrasing alone |

### Why this is ambiguous (not clear-cut OPEN)

"Start protecting" _leans_ toward OPEN, but is not definitive:

1. The user may already have puts in the rolling tracker and be asking to revisit/roll/add to them — "start" could mean "let's get going on this" rather than "open brand-new positions."
2. The user may be framing a close-and-replace action as "starting fresh protection."
3. Per `references/mode-selection.md`: _"Never guess from portfolio state alone. Even if rolling_tracker shows positions near expiry, if the user says 'help me with hedges' you should still ask."_
4. Per `SKILL.md`: _"Do not auto-detect from portfolio state alone."_

The phrase "Let's start protecting" has a similar ambiguity profile to "Help me with hedging" in the mode-selection edge-case table — general protective intent without an explicit action verb that maps cleanly to OPEN, ROLL, or CLOSE.

**Decision: STOP and ask. Do not generate a ticket.**

---

## Clarification Question

The skill would respond to the user with:

> Open, roll, or close?
>
> - **Open** — start a new protective-put program from scratch (or add contracts to an existing one)
> - **Roll** — renew puts you already have that are nearing expiration
> - **Close** — unwind existing puts (thesis changed, gain capture, or budget reallocation)

---

## No Ticket Generated

No ticket was produced. The `fin-guru-hedge-roll` skill requires an unambiguous mode (OPEN | ROLL | CLOSE) before it proceeds to Step 1 (temporal awareness), portfolio loading, sizing, or chain scanning. Generating an OPEN ticket based on phrasing alone would be a premature assumption — if the user actually has existing puts approaching expiry, producing an OPEN ticket wastes a turn and could create duplicate positions.

**Status:** Awaiting user response to clarification question. Work resumes after mode is confirmed.

---

_Educational Notice: For educational purposes only; not investment advice. Options strategies carry risk of total premium loss. Consult qualified financial, tax, and legal advisors before implementing any hedging strategy._
