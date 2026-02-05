# Phase 10: Template Engine & Dividend Topic Port - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a pipeline that converts topic JSON + HTML template into standalone interactive knowledge explorers using Cytoscape.js, with the dividend strategy topic as the first output. Feature parity with the existing prototype (`.dev/playgrounds/dividend-strategy-explorer.html`). Knowledge state persistence, learning modes, additional topics, and Maya integration are Phases 11-12.

</domain>

<decisions>
## Implementation Decisions

### Graph visualization engine
- Use Cytoscape.js library instead of the prototype's custom canvas renderer
- Force-directed layout (Cytoscape's `cose` or similar) to match the prototype's organic feel
- Dark theme as default with a light mode toggle (both themes)
- Node colors based on category (Foundation=blue, Strategy=purple, etc.) — knowledge state shown via badge or border indicator, not node fill color
- Template defines a global color palette for category slots; topics assign category names and the template maps them to colors by order

### Explorer interaction model
- Clicking a node opens a bottom drawer detail panel (slides up from bottom, graph stays full width)
- Bottom drawer shows: concept description, related concepts, generated learning prompt, and a "Copy prompt" button
- Knowledge state cycling available via a button inside the detail panel (not by clicking the node directly)
- Preset category filter buttons that highlight/dim nodes by category group
- Text search box to find specific concepts by name (in addition to preset filters)
- Hovering a node highlights its connected edges and adjacent nodes (Cytoscape built-in)

### Topic data structure
- Full topic envelope: JSON includes topic title, description, version, author, categories array, concepts array, edges array
- Each concept: id, name, category, description, difficulty (beginner/intermediate/advanced), prerequisites (array of concept IDs)
- Edges use typed relationships: each edge has {source, target, type, label?} where type is one of (enables, requires, protects, funds, etc.) — type determines edge styling (color, dash pattern)
- Zod schema validates the entire topic JSON structure at build time
- Category colors defined in the template as a global palette, not in topic JSON — topics name their categories, template assigns colors by order

### Build pipeline output
- HTML + separate JS bundle per topic (not single-file inline)
- Cytoscape.js bundled into the JS output during build (works offline, no CDN dependency)
- Bun as the build tool (consistent with project's existing Bun usage)
- Strict Zod validation before build — malformed JSON fails with specific error messages, no broken HTML output
- Output directory: `fin-guru-private/explorers/` (private output, consistent with existing conventions)
- Build command produces: `{topic-slug}.html` + `{topic-slug}.js` per topic

### Claude's Discretion
- Exact Cytoscape.js layout parameters and animation settings
- Bottom drawer animation and sizing details
- Edge type-to-style mapping (which colors/dashes for each relationship type)
- Search implementation details (fuzzy vs exact matching)
- Bun build script internals and file watching for dev mode
- Dark/light theme color palettes and toggle mechanism

</decisions>

<specifics>
## Specific Ideas

- The existing prototype at `.dev/playgrounds/dividend-strategy-explorer.html` is the authoritative reference for feature parity — 21 concepts, 6 categories, 22 edges, same graph structure
- The prototype uses a GitHub-dark aesthetic — the dark theme should feel similar
- Generated learning prompts should be concept-specific and useful when pasted into an AI chatbot
- The detail panel should feel contextual but not obstructive — bottom drawer keeps the graph visible above it

</specifics>

<deferred>
## Deferred Ideas

- Knowledge state persistence via localStorage — Phase 11 (EXPL-05)
- Learning mode selector (guided/standard/yolo) — Phase 11 (EXPL-06)
- Options-greeks and risk-management topic content — Phase 11 (EXPL-09a, EXPL-09b)
- Mobile/touch polish — Phase 11 (EXPL-08)
- Maya learner profile export — Phase 12 (EXPL-07)
- Topic selector landing page — Phase 12 (EXPL-10)
- CLI launcher (`fin_guru.py explore`) — Phase 12 (EXPL-12)

</deferred>

---

*Phase: 10-template-engine-dividend-topic-port*
*Context gathered: 2026-02-03*
