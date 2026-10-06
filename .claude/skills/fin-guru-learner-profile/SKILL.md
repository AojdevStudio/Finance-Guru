---
name: fin-guru-learner-profile
description: "Build or update the owner's learner profile for teaching and onboarding, covering literacy level, learning preferences, risk tolerance, goals, time limits, and ADHD-friendly pacing. Use when the owner starts learning sessions, asks to be taught a concept from scratch, or wants the teaching pace changed. Not for the instance setup itself (use instance-onboarding)."
---

# Learner Profile Skill

Build comprehensive learner/client profiles through progressive questioning.

## Profile Components

1. **Financial Literacy Level** — Assess current knowledge (beginner/intermediate/advanced)
2. **Learning Preferences** — Visual, textual, interactive, video preferences
3. **Risk Tolerance** — Conservative, moderate, aggressive assessment
4. **Investment Goals** — Short-term, medium-term, long-term objectives
5. **Time Constraints** — Available learning time, session preferences
6. **Neurodivergent Accommodations** — ADHD-friendly pacing, chunk sizes, break frequency
7. **Prior Experience** — Previous investment experience, platforms, asset classes

## Learning Modes

| Mode | Description | Pacing |
|------|-------------|--------|
| Guided | ADHD-friendly: 2-3 min chunks, frequent check-ins, break prompts | Slow |
| Standard | Balanced pacing with examples, moderate check-ins | Medium |
| YOLO | Fast-track for experienced learners, minimal interruptions | Fast |

## Workflow

1. Greet warmly and explain profiling purpose
2. Ask questions one at a time, building understanding progressively
3. Adapt question depth based on responses
4. Store profile context (max 200 tokens for context efficiency)
5. Use profile to personalize teaching sessions and onboarding

## Requirements

- Never overwhelm with initial questions — progressive profiling only
- Default to guided mode for new learners
- Explain clearly why each piece of information matters
- Ensure all clients understand Finance Guru is educational-only
- Learner profile max 200 tokens for context efficiency
