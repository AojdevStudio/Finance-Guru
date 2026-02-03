---
title: "Finance Guru Interactive Knowledge Explorer"
status: in-progress
created: 2026-02-02
updated: 2026-02-02
author: "Ossie Irondi"
spec_id: finance-guru-interactive-knowledge-explorer
version: "1.0.0"
description: "Template-based interactive knowledge graph system for Finance Guru onboarding, education, and top-of-funnel marketing"
tags:
  - finance-guru
  - onboarding
  - maya
  - education
  - playground
  - marketing
  - knowledge-graph
references:
  - ../../playgrounds/dividend-strategy-explorer.html
supersedes: []
diagrams:
  human: "diagrams/finance-guru-interactive-knowledge-explorer-arch.png"
  machine: "diagrams/finance-guru-interactive-knowledge-explorer-arch.mmd"
---

# Finance Guru Interactive Knowledge Explorer

## Overview

Transform the dividend strategy explorer playground into a **template-based interactive knowledge graph system** that serves as Finance Guru's visual onboarding layer, Maya's pre-teaching assessment tool, and a standalone top-of-funnel marketing asset. Users self-assess their knowledge across interconnected financial concepts, and the system generates personalized learning prompts or structured learner profiles.

## Problem Statement

### Why This Exists

Finance Guru's onboarding (James Cooper) collects financial data (assets, income, risk tolerance) but has **no way to assess what the user actually knows** about the strategies they'll be using. Maya Brooks (Teaching Specialist) builds learner profiles progressively through conversation, but starts cold with no pre-existing knowledge map. New users approaching Finance Guru for the first time have no visual, low-stakes way to explore what the system teaches before committing to setup.

### Who It's For

1. **Prospective users** discovering Finance Guru through search/social (top-of-funnel)
2. **New Finance Guru users** going through onboarding who need knowledge assessment
3. **Existing users** working with Maya who want to visualize their learning progress
4. **Anyone** who wants a personalized finance learning prompt for any chatbot

### Cost of NOT Doing This

- Maya starts every teaching relationship cold, wasting early sessions on assessment
- New users face intimidating CLI onboarding with no visual preview of what they'll learn
- No shareable marketing artifact that demonstrates Finance Guru's educational depth
- The working prototype sits unused in `.dev/playgrounds/`

### What Triggered This

Working prototype (`dividend-strategy-explorer.html`) proved the concept works. The self-assess → generate prompt → copy to any chatbot flow is validated and compelling. The realization that this pattern maps directly to Maya's learner profile system and James's onboarding flow.

## Vision

### The Funnel

```
Discovery          →  Assessment        →  Conversion         →  Retention
─────────────────────────────────────────────────────────────────────────────
Google/social      →  Knowledge Explorer →  Finance Guru       →  Maya teaching
finds playground       (self-assess)        onboarding (James)     with profile
                   →  Copy prompt        →  Use with any       →  Come back for
                       to clipboard          chatbot                more topics
```

### Core Concept

Each Finance Guru knowledge domain (dividends, options, risk management, portfolio construction, tax optimization) gets its own **interactive knowledge explorer** built from a shared template system. Users:

1. See an interconnected graph of concepts for that domain
2. Click through each node to understand what it covers
3. Self-assess: "I know this" / "I'm fuzzy" / "I don't know this"
4. Get a personalized learning prompt OR a structured learner profile
5. Copy the prompt to any chatbot OR feed the profile into Maya

## Technical Requirements

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Knowledge Explorer Template System                             │
├────────────────────── ┬─────────────────────────────────────────┤
│  Template Engine      │  Topic Data Files (JSON)                │
│  (shared HTML/JS)     │  ├── dividend-strategy.json             │
│                       │  ├── options-greeks.json                │
│                       │  ├── risk-management.json               │
│                       │  ├── portfolio-construction.json        │
│                       │  └── tax-optimization.json              │
├────────────────────── ┴─────────────────────────────────────────┤
│  Output Modes                                                   │
│  ├── Prompt Mode: Generate copy-paste learning prompt           │
│  ├── Profile Mode: Export Maya-compatible learner profile JSON  │
│  └── Marketing Mode: Embeddable widget for aojdevstudio.me      │
└─────────────────────────────────────────────────────────────────┘
```

### Data Model: Topic Definition (JSON)

```json
{
  "topic_id": "dividend-strategy",
  "title": "Dividend Investment Strategy",
  "description": "Master the investment-first mindset and margin flywheel",
  "version": "1.0.0",
  "categories": [
    {
      "id": "foundation",
      "label": "Foundation",
      "color": "#58a6ff"
    }
  ],
  "nodes": [
    {
      "id": "mindset",
      "label": "Investment-First\nMindset",
      "category": "foundation",
      "description": "Invert traditional finance: invest 100% first...",
      "tags": ["core"],
      "prerequisites": [],
      "maya_teaching_level": 1,
      "default_knowledge": "unknown"
    }
  ],
  "edges": [
    {
      "from": "mindset",
      "to": "compound",
      "label": "enables",
      "type": "foundation"
    }
  ],
  "presets": {
    "core": { "filter": "tags:core", "label": "Core Strategy" },
    "risk": { "filter": "category:risk OR tags:risk", "label": "Risk Mgmt" }
  },
  "prompt_template": {
    "intro": "I'm studying {topic_title} for financial independence.",
    "know_prefix": "I already understand:",
    "fuzzy_prefix": "I'm fuzzy on:",
    "unknown_prefix": "I don't understand:",
    "closing": "Please explain the fuzzy and unknown concepts, building on what I already know. Use concrete numbers and real examples.",
    "maya_mode_suffix": {
      "guided": "Break everything into 2-3 minute chunks with check-ins after each concept. I learn best with frequent pauses.",
      "standard": "Use a balanced pace with examples for each concept.",
      "yolo": "Go fast. I learn best by diving deep quickly. Skip the hand-holding."
    }
  }
}
```

### Output: Maya Learner Profile Export

When used in Finance Guru context, the explorer exports a structured profile:

```json
{
  "learner_profile": {
    "topic": "dividend-strategy",
    "assessed_at": "2026-02-02T15:30:00Z",
    "knowledge_state": {
      "know": ["mindset", "compound", "fire"],
      "fuzzy": ["three-bucket", "flywheel", "spread"],
      "unknown": ["drip-nav", "nav-arb", "put-insurance"]
    },
    "learning_mode_preference": "guided",
    "suggested_teaching_order": ["three-bucket", "flywheel", "spread", "drip-nav", "nav-arb", "put-insurance"],
    "estimated_sessions": 3,
    "maya_integration": {
      "skip_concepts": ["mindset", "compound", "fire"],
      "start_with": "three-bucket",
      "depth_needed": {
        "fuzzy": "review_and_reinforce",
        "unknown": "full_teaching_workflow"
      }
    }
  }
}
```

## Scope Definition

| Aspect | Definition |
|--------|------------|
| **In scope** | Template engine, 5 topic data files, 3 output modes, localStorage persistence, mobile/touch support, Maya profile export format, embeddable widget mode |
| **Out of scope** | Backend/database, user accounts, analytics dashboard, real-time sync with Finance Guru CLI, payment/subscription |
| **Stop condition** | User can open any topic explorer, self-assess, and either copy a learning prompt or export a Maya-compatible profile |
| **Edge cases** | Empty knowledge state (all unknown), full knowledge state (all know), single-node topics, topics with 50+ nodes |

## Requirements

### Phase 1: Template System (MVP)

- [ ] Extract shared template from `dividend-strategy-explorer.html`
- [ ] Create topic JSON schema and validator
- [ ] Build template engine that loads topic JSON and renders explorer
- [ ] Migrate dividend strategy data to JSON format
- [ ] Add localStorage persistence (knowledge state survives refresh)
- [ ] Add learning mode selector (guided/standard/yolo) that affects prompt output
- [ ] Add Maya profile export button (downloads JSON file)
- [ ] Add touch support (mobile drag, tap to cycle knowledge)
- [ ] Responsive layout (sidebar collapses on mobile)

### Phase 2: Topic Expansion

- [ ] Create `options-greeks.json` topic data (from Maya's teaching workflow content)
- [ ] Create `risk-management.json` topic data
- [ ] Create `portfolio-construction.json` topic data
- [ ] Create `tax-optimization.json` topic data
- [ ] Build topic selector landing page (card grid showing all available explorers)
- [ ] Add cross-topic concept linking (some nodes appear in multiple topics)

### Phase 3: Finance Guru Integration

- [ ] Add CLI command to Finance Guru: `fin-guru explore <topic>` that opens explorer in browser
- [ ] Maya reads exported learner profile at session start (if file exists)
- [ ] James references available explorers during onboarding ("Want to assess your knowledge first?")
- [ ] Onboarding flow optionally launches explorer before financial data collection
- [ ] Profile export writes directly to `fin-guru/data/learner-profile.json`

### Phase 4: Marketing & Distribution

- [ ] Embeddable mode (iframe-safe, no sidebar, focused layout)
- [ ] Host on aojdevstudio.me as interactive demo
- [ ] SEO-optimized landing pages per topic
- [ ] Social sharing (screenshot of knowledge state + link)
- [ ] "Powered by Finance Guru" branding with CTA to GitHub repo
- [ ] Add to Finance Guru README as interactive demo link

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Template format** | Single HTML file per topic (generated from JSON + template) | Keeps zero-dependency philosophy, ships anywhere |
| **Persistence** | localStorage keyed by topic_id | No backend needed, survives refresh, per-device |
| **Build tool** | Bun script to compile JSON + template → HTML | Finance Guru already uses Bun, simple pipeline |
| **Mobile approach** | Touch events + responsive CSS | Canvas-based rendering already scales with DPI |
| **Profile export** | JSON file download + clipboard | Works standalone and with Finance Guru CLI |

## Topic Coverage Map

| Topic | Concepts | Categories | Edges | Source Material |
|-------|----------|------------|-------|-----------------|
| Dividend Strategy | 21 | 6 | 22 | Existing prototype, Sean/Alex content |
| Options Greeks | ~15 | 4 | ~18 | Maya's teaching-workflow.md Level 1-4 |
| Risk Management | ~18 | 5 | ~20 | Maya's Risk Framework progression |
| Portfolio Construction | ~16 | 4 | ~16 | Maya's Portfolio Construction progression |
| Tax Optimization | ~12 | 3 | ~14 | Tax Optimizer agent knowledge base |

## Acceptance Criteria

- [ ] **AC1**: User opens dividend strategy explorer, refreshes page, knowledge state persists
- [ ] **AC2**: User selects "guided" mode, generated prompt includes ADHD-friendly pacing instructions
- [ ] **AC3**: Topic JSON schema validates all 5 topic files
- [ ] **AC4**: Explorer renders correctly on mobile (375px width) with touch interactions
- [ ] **AC5**: Maya profile export produces valid JSON matching the learner_profile schema
- [ ] **AC6**: Template generates working HTML from any valid topic JSON
- [ ] **AC7**: "Copy Prompt" works on all major browsers (Chrome, Safari, Firefox)
- [ ] **AC8**: All explorers load in under 1 second (no external dependencies)
- [ ] **AC9**: Embeddable mode renders cleanly in an iframe at 800x600px minimum
- [ ] **AC10**: Knowledge state export includes edge relationships for relevant unknown/fuzzy concepts

## Marketing Potential

### Organic Discovery

Each topic explorer is a standalone page optimized for search:
- "interactive dividend investing guide"
- "options greeks visual explainer"
- "portfolio risk management concepts"

### Social Sharing

Users screenshot their knowledge map and share: "I thought I knew dividends until I mapped it out. 14/21 concepts were fuzzy or unknown." → Link to explorer → Viral loop.

### Demo for Finance Guru

The explorer IS the demo. Instead of explaining what Finance Guru teaches, show the interactive graph. "This is one of 5 topic areas. Finance Guru has an AI teacher (Maya) who builds on exactly what you know."

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Topic data creation is slow | Medium | Medium | Start with dividend (already done), add topics incrementally |
| Canvas rendering issues on mobile | Medium | High | Test early on iOS Safari and Android Chrome |
| Maya integration requires Finance Guru changes | High | Low | Profile export works standalone first, integration comes in Phase 3 |
| Scope creep into full LMS | Medium | High | Hard scope boundary: explorers generate prompts, they don't teach |

## Implementation Notes

- The existing prototype at `.dev/playgrounds/dividend-strategy-explorer.html` is the starting point
- Finance Guru repo: `aojdevstudio/Finance-Guru` (private, main branch)
- Maya's teaching workflow and concept progressions provide the raw material for topic data files
- The build script should live in Finance Guru's `scripts/` directory
- Generated explorers deploy to `docs/explorers/` for GitHub Pages or aojdevstudio.me

## Timeline Target

**February 2026** - Phase 1 (Template System MVP) + Phase 2 start (2-3 topic files)
