---
date: 2026-02-20
topic: markdown-rendering-quality
related: docs/plans/2026-02-20-selection-ux-open-tui-implementation-plan.md (D2 dependency)
---

# Markdown Rendering Quality Brainstorm

## What We're Building

A Glamour-inspired markdown rendering system for Finance Guru's TUI, built natively on OpenTUI's `MarkdownRenderable` component. The renderer must handle all agent response surfaces (streaming chat, portfolio tables, welcome screen, static help content) at a visual quality level matching Charm's Glamour library, using the FG brand palette of Black, Gold, and Cyan.

## Why This Approach

We evaluated three paths:

1. **Shell out to Glow CLI**: Instant Glamour quality but _kills streaming UX_ because Glow renders complete documents only. Finance Guru streams AI responses token-by-token, so buffering the entire response before rendering is unacceptable. Also adds a ~15MB external binary dependency with no brand customization.

2. **Port Glamour's stylesheet system to TypeScript**: Maximum control but massive effort duplicating a mature Go library. Glamour's JSON stylesheet approach is elegant but the rendering engine is tightly coupled to Go's goldmark parser.

3. **OpenTUI native, Glamour-inspired styling** (chosen): Use OpenTUI's `MarkdownRenderable` with streaming mode, Tree-sitter syntax highlighting, and conceal mode. Apply a custom theme that matches Glamour's dark theme visual quality using the FG brand palette. Best balance of streaming support, brand control, integration with the selection UX controller, and development effort.

## Brand Identity

### Logo Reference
`docs/images/finance-guru-logo.png` — elegant gold "FG" monogram on pure black. Calligraphic, minimalist, premium. The rendering theme must match this aesthetic: luxury minimal, clean spacing, not busy.

### Canonical Brand Palette

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Background | Black | `#000000` | Dominant surface, terminal background assumed dark |
| Primary accent | Gold | `#F59E0B` | Headers, emphasis, premium indicators, FG identity |
| Secondary accent | Cyan | `#06B6D4` | Data values, metrics, code keywords, technical content |
| Semantic: success | Green | `green` | Positive values, gains, passing states |
| Semantic: warning | Yellow | `yellow` | Caution, margin alerts, approaching thresholds |
| Semantic: error | Red | `red` | Losses, violations, critical alerts |
| Body text | White | `white` | Standard readable text |
| Muted | Gray | `gray` | Timestamps, metadata, disabled items |

### Agent Color Map (Existing)
Each specialist agent retains a distinct badge color. These do NOT change the markdown theme — they only affect the agent badge and header accent when that agent is responding.

### Brand Tone for Rendering
- **Luxury minimal**: clean, spacious, no clutter or heavy borders
- **Restrained color usage**: gold for structure (headers, rules), cyan for data, white for body
- **Inspired by**: Glamour "dark" base, but toned down — less neon, more refined
- **Anti-patterns**: rainbow syntax highlighting, heavy ASCII borders, emoji-heavy headers, busy decorations

## Key Decisions

- **OpenTUI `MarkdownRenderable`** is the single rendering path for all markdown content. No separate renderer for different surfaces.
- **Streaming mode** is mandatory for chat responses. Tokens render incrementally as they arrive.
- **Conceal mode** hides raw markdown markers (no visible `#`, `*`, `` ` `` in rendered output).
- **Purple is removed** from the brand palette. The previous `#7C3AED` primary accent is replaced by Gold `#F59E0B`.
- **theme.ts must be updated** to reflect the corrected brand palette before any rendering work begins.
- **All markdown elements are equally prioritized** — no phased rollout of element support. Tables, code blocks, headers, lists, bold/italic, blockquotes, and horizontal rules must all render at the same quality level from day one.

## Markdown Element Rendering Spec

### Headers (H1-H6)
- H1: Gold (`#F59E0B`), bold, full-width underline rule
- H2: Gold, bold, no rule
- H3-H6: White, bold, decreasing visual weight
- No `#` markers visible (conceal mode)

### Code Blocks
- Background: slightly lighter than terminal black (e.g., `#1A1A2E` or terminal's dimmed palette)
- Border: thin gold left-edge accent or no border (luxury minimal)
- Syntax highlighting: Tree-sitter via OpenTUI, using a muted color scheme — not rainbow
- Language label: small muted text above block
- Inline code: cyan background highlight or backtick-style distinct from body

### Tables
- Header row: gold text, bold
- Border style: thin single-line or no borders (Glamour uses thin Unicode box-drawing)
- Cell alignment: respect markdown alignment markers
- Alternating row shading: subtle if supported, not mandatory
- Financial data: right-align numeric columns automatically where detected

### Lists
- Bullet: gold `>` or `*` marker, or Unicode bullet
- Numbered: gold number, period
- Nested: indentation with muted indent guides
- Task lists: checkbox rendering if supported

### Bold / Italic / Strikethrough
- Bold: white, bold weight
- Italic: white, italic (or underline fallback in terminals without italic)
- Strikethrough: muted gray with strikethrough
- No `*` or `_` markers visible

### Blockquotes
- Gold left border (2-char wide)
- Slightly dimmed text
- Nested quotes: progressively dimmer

### Horizontal Rules
- Gold thin line, full width
- Clean spacing above and below

### Links
- Cyan text with underline
- URL shown in muted gray after link text if terminal doesn't support clickable links

## Streaming Behavior

- Tokens render incrementally via OpenTUI's streaming mode
- Markdown structure is parsed progressively — partial headings/tables render as they complete
- No full-screen rerender on each token — batch updates at ~30fps (matching the existing anti-flicker pattern from Phase 5 of the TUI build)
- Active menu focus is NEVER stolen by streaming markdown updates (critical integration with selection UX spec)

## Integration with Selection UX

- Markdown rendering and selection menus coexist on screen
- Keyboard input routes to the active surface (menu vs text) — markdown content is passive/non-interactive
- Agent badge color in rendered headers matches the `agentColors` map
- Status line reflects which agent produced the currently visible markdown

## Open Questions

- Should code block syntax highlighting use a specific named theme (e.g., "GitHub Dark", "One Dark") or a custom FG-derived palette?
- What fallback rendering should occur in terminals that don't support the full OpenTUI feature set?
- Should markdown rendering quality degrade gracefully in narrow terminals (<80 cols) or maintain full styling?
- Should we support user-selectable themes in the future (dark-only for now)?

## Next Steps

1. Update `theme.ts` to replace purple with the corrected Black/Gold/Cyan palette.
2. Research OpenTUI `MarkdownRenderable` API — streaming mode, conceal mode, custom styling hooks.
3. Build a Glamour-inspired FG theme configuration for OpenTUI markdown rendering.
4. Implement rendering across all surfaces (chat, portfolio, welcome, help).
5. Visual regression tests comparing rendering output against Glamour reference screenshots.
6. Integration test: streaming + selection UX focus stability.
