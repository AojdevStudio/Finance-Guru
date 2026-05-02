# Mode Selection — Edge Cases and Disambiguation

The skill supports three modes: OPEN, ROLL, CLOSE. Mode is determined from user phrasing. This file documents edge cases where phrasing alone is ambiguous.

## Clear-Cut Cases

| User says | Mode |
|---|---|
| "Open a hedge program" | OPEN |
| "Put on protection" | OPEN |
| "Start hedging" | OPEN |
| "I don't have any puts yet" | OPEN |
| "Roll my puts" | ROLL |
| "Roll the hedge" | ROLL |
| "Renew the hedge" | ROLL |
| "My hedges are at 7 DTE" | ROLL (phrased as a state, but implies the action) |
| "Close the hedge" | CLOSE |
| "Unwind my puts" | CLOSE |
| "Close out the protection" | CLOSE |
| "Close QQQ puts, keep SPY" | CLOSE (partial) |

## Ambiguous Cases — Ask the User

| User says | What to ask |
|---|---|
| "Manage my hedges" | "Open, roll, or close?" |
| "What should I do with my puts?" | "Are you looking to open new ones, roll existing, or close?" |
| "Help me with hedging" | "Open a new program, roll existing, or close positions?" |
| "Protection strategy" | "Open, roll, or close?" |

Never guess from portfolio state alone. Even if `rolling_tracker` shows positions near expiry, if the user says "help me with hedges" you should still ask. Auto-inferring wastes a turn if you guess wrong.

## Edge Case: Mixed Intent

**"I want to close QQQ puts and open IWM puts"** — this is TWO actions. Handle as two separate tickets:
1. CLOSE mode for QQQ unwind
2. OPEN mode for IWM addition

Do not try to combine into one ticket. Each mode has its own template for a reason.

## Edge Case: User Refers to "Closing a Roll"

Sometimes the user says things like "let's close this out and not roll." That's CLOSE mode, not ROLL mode.

**Decision cue**: if the user is expressing the *absence* of a roll (skip, let expire, unwind), go to CLOSE. If the user is expressing forward-action to maintain coverage, go to ROLL.

## Edge Case: Early-Close for Gain Capture

**"These puts are deep ITM, let's take the gain"** — CLOSE mode with rationale `gain capture`. Even though this might precede opening new hedges, treat it as CLOSE first; if user wants to then re-open at different strikes, that's a separate OPEN ticket.

**"Roll these deep-ITM puts to capture gain and extend protection"** — ROLL mode with early-roll rationale. The user is explicit about maintaining protection; this is a rotational action, not a sunset.

## Edge Case: No Existing Positions + ROLL Phrasing

User says "roll my puts" but `rolling_tracker_cli status` returns empty. Two possibilities:
1. User has positions that weren't registered in the tracker → ask to seed them, then proceed with ROLL
2. User doesn't actually have positions and is confused → switch to OPEN after confirming

Ask:
> "The rolling tracker shows no positions. Do you have hedges that weren't registered (let's seed them), or would you like to open new hedges (OPEN mode)?"

## Edge Case: Positions Exist + OPEN Phrasing

User says "open hedges" but `rolling_tracker_cli status` shows existing positions. Possibilities:
1. User wants to add to the existing program (more contracts) → treat as OPEN addition
2. User forgot about existing positions → confirm before proceeding

Ask:
> "You already have [N] existing put positions. Are you adding to the program (OPEN addition), rolling the existing ones (ROLL), or did you forget about them?"

## Tone of Disambiguation Questions

Short, direct, three-choice format when possible. Don't over-explain. The user knows their own intent — they just phrased it ambiguously. Pick the phrasing that makes the least assumption about what they meant.

**Good**: "Open, roll, or close?"
**Bad**: "I see you have some positions. Based on your portfolio state and the fact that some positions are approaching expiration, I'm thinking you probably want to roll, but you could also be wanting to add to the program or unwind — which of these three actions do you want to take?"

Brevity respects the user's time.
