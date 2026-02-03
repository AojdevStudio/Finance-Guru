# Phase 9: Template Engine & Dividend Topic Port - Research

**Researched:** 2026-02-02
**Domain:** Standalone HTML generation pipeline (Bun build + Cytoscape.js graph visualization + JSON schema validation)
**Confidence:** HIGH

## Summary

Phase 9 requires building a reusable pipeline that converts topic JSON into standalone interactive HTML knowledge explorers. The research covers four domains: (1) graph visualization library selection, (2) Bun-based build pipeline for single-file HTML output, (3) JSON schema validation, and (4) template engine architecture.

The existing prototype at `.dev/playgrounds/dividend-strategy-explorer.html` is a fully functional 990-line single-file HTML application using Canvas 2D with a hand-rolled force-directed layout. It contains 21 concept nodes, 22 edges, 6 categories, knowledge-level tracking (know/fuzzy/unknown), preset filters, sidebar navigation, tooltips, and a dynamic learning prompt generator. This prototype defines the feature parity target.

The recommended approach replaces the hand-rolled Canvas renderer with Cytoscape.js (which provides production-grade graph rendering, layouts, and interactions out of the box), uses Zod for topic JSON schema validation at build time, and uses a two-stage Bun build pipeline that first bundles TypeScript/CSS, then inlines everything into a single standalone HTML file using Bun's HTMLRewriter API.

**Primary recommendation:** Use Cytoscape.js 3.33.x with Canvas renderer (not WebGL), Zod for schema validation, and a two-stage Bun build pipeline (bundle + inline) to produce zero-dependency standalone HTML files from topic JSON.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Cytoscape.js | 3.33.1 | Graph visualization (nodes, edges, layouts, interactions) | De facto standard for web graph visualization. 10.8k GitHub stars, MIT license, no external dependencies, ~434KB minified (~110KB gzipped). Canvas 2D renderer works on all modern browsers. |
| Zod | 3.x (latest) | Topic JSON schema validation at build time | TypeScript-first schema validation. Already in project dependencies (plaid-dashboard). Infers TypeScript types from schemas. Clear error messages for build failures. |
| Bun | 1.3.7 (installed) | Build pipeline runtime, HTML bundling, TypeScript transpilation | Already the project's JS runtime. Native HTML bundler, HTMLRewriter API, fast TypeScript transpilation. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| cytoscape-fcose | latest | Force-directed layout with constraints | If CoSE built-in layout produces poor results for knowledge graphs. fCoSE is the modern replacement for cose-bilkent with constraint support. |
| layout-base + cose-base | latest | Dependencies for fcose | Required by fcose if used |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Cytoscape.js | Keep hand-rolled Canvas 2D (current prototype) | Simpler, zero dependencies, but no layout algorithms, no built-in interactions (zoom/pan/drag), no styling system, significant maintenance burden for each new feature |
| Cytoscape.js | D3.js force-directed graph | More flexible but much more code required for equivalent graph features. D3 is general-purpose; Cytoscape.js is graph-specific. |
| Cytoscape.js | Sigma.js | Better for very large graphs (100k+ nodes). Overkill for 20-50 node knowledge explorers. |
| Zod | AJV (JSON Schema) | AJV uses JSON Schema standard (interoperable) but doesn't infer TypeScript types. Zod is more ergonomic for TypeScript projects. |
| Bun build + inline | Vite/esbuild | Would work but adds another tool. Bun is already the project runtime. |

**Installation:**
```bash
bun add cytoscape
bun add -d @types/cytoscape
# Only if built-in cose layout is insufficient:
bun add cytoscape-fcose
```

## Architecture Patterns

### Recommended Project Structure
```
src/explorer/
├── build.ts                    # Build pipeline entry point
├── schemas/
│   └── topic-schema.ts         # Zod schema for topic JSON
├── template/
│   ├── template.html           # HTML shell template
│   ├── explorer.ts             # Main Cytoscape.js application logic
│   └── styles.css              # Explorer styles (dark theme)
├── topics/
│   └── dividend-strategy.json  # First topic (ported from prototype)
└── dist/                       # Build output (gitignored)
    └── dividend-strategy-explorer.html  # Standalone output
```

### Pattern 1: Two-Stage Build Pipeline
**What:** Stage 1 bundles TypeScript into a single IIFE JS file and CSS into a single CSS file. Stage 2 reads the HTML template, inlines the bundled JS and CSS, injects the topic JSON data, and produces a single standalone HTML file.

**When to use:** Always -- this is the core pipeline pattern.

**Why two stages:** Bun's HTML bundler (`bun build index.html --outdir=dist`) produces SEPARATE files (HTML referencing external JS/CSS with hashed filenames). It does NOT produce a single self-contained file. The second stage uses Bun's HTMLRewriter API (or simple string manipulation) to inline everything.

**Example:**
```typescript
// Source: Bun docs (https://bun.sh/docs/bundler/html, https://bun.sh/docs/runtime/html-rewriter)
// build.ts

import { z } from "zod";
import { TopicSchema } from "./schemas/topic-schema";

const TOPIC_FILE = process.argv[2];
if (!TOPIC_FILE) {
  console.error("Usage: bun run build.ts <topic.json>");
  process.exit(1);
}

// --- Stage 0: Validate topic JSON ---
const rawJson = await Bun.file(TOPIC_FILE).json();
const parseResult = TopicSchema.safeParse(rawJson);
if (!parseResult.success) {
  console.error("Topic JSON validation failed:");
  console.error(parseResult.error.format());
  process.exit(1);
}
const topic = parseResult.data;

// --- Stage 1: Bundle JS and CSS ---
const jsResult = await Bun.build({
  entrypoints: ["./src/explorer/template/explorer.ts"],
  minify: true,
  target: "browser",
  format: "iife",
});
if (!jsResult.success) {
  console.error("JS build failed:", jsResult.logs);
  process.exit(1);
}
const bundledJs = await jsResult.outputs[0].text();

const cssContent = await Bun.file("./src/explorer/template/styles.css").text();

// --- Stage 2: Assemble standalone HTML ---
const templateHtml = await Bun.file("./src/explorer/template/template.html").text();

const finalHtml = templateHtml
  .replace("/* __INJECT_CSS__ */", cssContent)
  .replace("/* __INJECT_TOPIC_DATA__ */", `const TOPIC_DATA = ${JSON.stringify(topic)};`)
  .replace("/* __INJECT_APP_JS__ */", bundledJs);

const outputName = topic.metadata.slug || "explorer";
await Bun.write(`./src/explorer/dist/${outputName}.html`, finalHtml);
console.log(`Built: ./src/explorer/dist/${outputName}.html`);
```

### Pattern 2: Topic JSON Data Injection
**What:** Topic data is injected into the HTML template as a global JavaScript constant before the application code runs.

**When to use:** Always -- this is how topics become different explorers.

**Example:**
```html
<!-- template.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TOPIC_TITLE__</title>
  <style>/* __INJECT_CSS__ */</style>
</head>
<body>
  <!-- UI chrome: header, sidebar, graph container, prompt panel -->
  <script>
    /* __INJECT_TOPIC_DATA__ */
    /* __INJECT_APP_JS__ */
  </script>
</body>
</html>
```

### Pattern 3: Cytoscape.js Element Data Model
**What:** Transform topic JSON nodes/edges into Cytoscape.js element format at runtime.

**When to use:** In the explorer application code.

**Example:**
```typescript
// Source: Cytoscape.js docs (https://js.cytoscape.org)
// Transform topic nodes to Cytoscape elements
function topicToElements(topic: TopicData): cytoscape.ElementDefinition[] {
  const nodes = topic.nodes.map(node => ({
    data: {
      id: node.id,
      label: node.label,
      category: node.category,
      description: node.description,
      knowledge: node.knowledge || "fuzzy",
      tags: node.tags,
    },
  }));

  const edges = topic.edges.map(edge => ({
    data: {
      id: `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      type: edge.type,
    },
  }));

  return [...nodes, ...edges];
}

// Initialize Cytoscape
const cy = cytoscape({
  container: document.getElementById("cy"),
  elements: topicToElements(TOPIC_DATA),
  style: [ /* ... category-based styling ... */ ],
  layout: {
    name: "cose",
    animate: false,
    nodeDimensionsIncludeLabels: true,
    idealEdgeLength: (edge) => 120,
    nodeRepulsion: (node) => 8000,
    gravity: 0.25,
  },
});

// Interactions
cy.on("tap", "node", (evt) => {
  const node = evt.target;
  showTooltip(node.data());
});
```

### Pattern 4: Cytoscape.js via CDN vs Bundled
**What:** Decision on how Cytoscape.js is included in the standalone HTML.

**Recommendation: Bundle into the HTML file (not CDN).**

The requirement states "zero external dependencies." Cytoscape.js minified is 434KB (~110KB gzipped). When inlined into the HTML, the total file will be ~500-600KB. This is acceptable for a local knowledge tool (not a public website optimized for TTFB). CDN would add a network dependency and break offline use.

**Implementation:** Import Cytoscape.js in `explorer.ts`, let Bun's bundler include it in the IIFE output, then inline that into the HTML.

```typescript
// explorer.ts
import cytoscape from "cytoscape";
// Bun's bundler will include the full cytoscape library in the output
```

### Anti-Patterns to Avoid
- **Dynamic script loading in standalone HTML:** Don't use `fetch()` or dynamic `import()` in the generated HTML. Everything must be self-contained. If it needs a network request, it's not standalone.
- **Separate topic JSON file alongside HTML:** The topic data must be injected INTO the HTML, not loaded from a sibling file. One file = one artifact.
- **Using Cytoscape.js WebGL renderer:** The WebGL renderer is in preview (added v3.31) with significant limitations (only straight/haystack/bezier edges, no dashed lines, no gradients, solid colors only, triangle arrows only). For 20-50 node knowledge graphs, Canvas 2D is more than performant enough and has full feature support.
- **Hand-rolling force-directed layout:** The prototype has a custom 200-iteration force simulation. Cytoscape.js built-in CoSE layout is superior -- constraint-aware, optimized, battle-tested.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Graph layout algorithm | Custom force-directed simulation (like current prototype's 200-iteration loop) | Cytoscape.js `cose` or `fcose` layout | CoSE handles compound nodes, edge weight, nesting. Hand-rolled layouts produce overlapping nodes, poor edge routing, no animation. |
| Node drag & drop | Custom mousedown/mousemove/mouseup handlers on Canvas | Cytoscape.js built-in dragging | Handles touch events, momentum, bounds checking, hitbox calculation with labels. |
| Zoom & pan | Custom scroll/pinch handlers | Cytoscape.js built-in zoom/pan | Handles pinch-to-zoom, scroll zoom, trackpad gestures, pan limits, min/max zoom. |
| Graph styling | Manual Canvas draw calls per node type | Cytoscape.js stylesheet selectors | CSS-like selectors with data-driven values: `'background-color': 'data(categoryColor)'`. |
| Tooltip positioning | Manual coordinate math avoiding canvas edges | Cytoscape.js `position()` API + HTML tooltip | Cytoscape provides screen coordinates for nodes; position HTML tooltips relative to those. |
| JSON validation | Custom if/else checking of JSON fields | Zod schema with `.safeParse()` | Produces structured errors with paths, handles nested objects, infers TypeScript types. |
| HTML minification | Custom regex-based minification | Bun `--minify` flag | Handles JS, CSS, and whitespace. Don't regex-replace HTML. |

**Key insight:** The existing prototype hand-rolls approximately 600 lines of code for graph rendering, layout, interaction, and tooltip handling. Cytoscape.js provides all of this with ~30 lines of configuration. The template engine's value is in reusability and correctness, not in reimplementing a graph library.

## Common Pitfalls

### Pitfall 1: Cytoscape.js Container Must Have Explicit Dimensions
**What goes wrong:** Cytoscape.js renders nothing -- blank container, no error.
**Why it happens:** Cytoscape.js requires its container DOM element to have explicit width and height. If the container is `display: none`, has `height: 0`, or relies on content for sizing, Cytoscape renders nothing silently.
**How to avoid:** Set explicit CSS dimensions on the container:
```css
#cy {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}
```
**Warning signs:** Empty white/black rectangle where graph should be. No console errors.

### Pitfall 2: Bun Build Produces Separate Files, Not Single HTML
**What goes wrong:** Developer expects `bun build index.html --outdir=dist` to produce one file but gets HTML + separate JS + separate CSS with hashed filenames.
**Why it happens:** Bun's HTML bundler is designed for web deployment (cache-friendly separate assets), not single-file distribution.
**How to avoid:** Use the two-stage build pattern: Stage 1 bundles JS/CSS separately via `Bun.build()` API, Stage 2 inlines results into template HTML using string replacement.
**Warning signs:** Output directory contains multiple files instead of one HTML.

### Pitfall 3: IIFE Format Required for Inline Scripts
**What goes wrong:** Bundled JS uses `import`/`export` at top level, which fails when inlined into a `<script>` tag.
**Why it happens:** Bun defaults to ESM format. ESM requires `type="module"` on script tags and cannot be concatenated. IIFE (Immediately Invoked Function Expression) wraps everything in a closure.
**How to avoid:** Always use `format: "iife"` in `Bun.build()`:
```typescript
const result = await Bun.build({
  entrypoints: ["./explorer.ts"],
  format: "iife",
  target: "browser",
  minify: true,
});
```
**Warning signs:** "Cannot use import statement outside a module" error in browser console.

### Pitfall 4: Cytoscape.js Layout Runs Before DOM Ready
**What goes wrong:** Layout calculates positions based on container size 0x0, all nodes stack at origin.
**Why it happens:** Script runs before container has dimensions (e.g., before CSS is applied).
**How to avoid:** Initialize Cytoscape after the DOM is fully loaded:
```typescript
document.addEventListener("DOMContentLoaded", () => {
  const cy = cytoscape({ /* ... */ });
});
```
Or place the `<script>` at the end of `<body>` (which the template does).

### Pitfall 5: Topic JSON Schema Too Rigid or Too Loose
**What goes wrong:** Schema is too rigid -- minor additions require schema changes. Or too loose -- malformed JSON produces broken HTML instead of build error.
**Why it happens:** Schema design requires balancing strictness with extensibility.
**How to avoid:** Use Zod's `.strict()` on the root object (catches extra keys) but allow `.passthrough()` on node `data` or `metadata` objects where extensibility is needed. Validate the structure (required fields, types, edge references) but allow optional extension fields.
**Warning signs:** Build succeeds but explorer shows missing labels, broken edges, or no nodes.

### Pitfall 6: Prototype Feature Parity Drift
**What goes wrong:** New explorer is "done" but is missing features from the prototype: preset filters, knowledge badges, learning prompt generation, copy-to-clipboard.
**Why it happens:** Focus on graph rendering and template engine; forget about the sidebar, prompt panel, and interaction features.
**How to avoid:** Create a feature checklist from the prototype before starting:
1. Graph visualization with category-colored nodes
2. Knowledge level badges (know/fuzzy/unknown) with click-to-cycle
3. Category legend in sidebar
4. Concept list in sidebar with knowledge badges
5. Preset filter buttons (All, Core Strategy, Risk Mgmt, Implementation, Advanced)
6. Auto-layout button
7. Set all knowledge buttons
8. Reset button
9. Hover tooltips with description and category
10. Dynamic learning prompt generation based on knowledge gaps
11. Copy prompt button
12. Stats display (N know, N fuzzy, N unknown)
13. Node drag interaction
14. Edge labels shown on hover

## Code Examples

Verified patterns from official sources:

### Cytoscape.js Initialization with Styled Knowledge Graph
```typescript
// Source: Cytoscape.js docs (https://js.cytoscape.org)
import cytoscape from "cytoscape";

const cy = cytoscape({
  container: document.getElementById("cy"),

  elements: topicToElements(TOPIC_DATA),

  style: [
    {
      selector: "node",
      style: {
        label: "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "text-wrap": "wrap",
        "text-max-width": "80px",
        "font-size": "11px",
        color: "#e6edf3",
        "background-color": "data(categoryColor)",
        "border-width": 2,
        "border-color": "data(categoryColor)",
        width: 72,
        height: 72,
      },
    },
    {
      selector: "edge",
      style: {
        width: 1.5,
        "line-color": "#30363d",
        "target-arrow-color": "#30363d",
        "target-arrow-shape": "triangle",
        "curve-style": "bezier",
        label: "data(label)",
        "font-size": "9px",
        color: "#8b949e",
        "text-rotation": "autorotate",
        "text-background-opacity": 1,
        "text-background-color": "#0d1117",
        "text-background-padding": "3px",
      },
    },
    {
      selector: "node:active",
      style: {
        "overlay-opacity": 0.1,
      },
    },
    {
      selector: "edge:active",
      style: {
        "overlay-opacity": 0,
      },
    },
  ],

  layout: {
    name: "cose",
    animate: false,
    fit: true,
    padding: 40,
    nodeDimensionsIncludeLabels: true,
    randomize: true,
    idealEdgeLength: (edge) => 120,
    nodeRepulsion: (node) => 8000,
    gravity: 0.25,
    numIter: 2000,
  },

  // Interaction settings
  minZoom: 0.3,
  maxZoom: 3,
  wheelSensitivity: 0.3,
});
```

### Cytoscape.js Event Handling for Knowledge Badges
```typescript
// Source: Cytoscape.js docs - events (https://js.cytoscape.org/#cy.on)
const KNOWLEDGE_LEVELS = ["fuzzy", "know", "unknown"] as const;

cy.on("tap", "node", (evt) => {
  const node = evt.target;
  const currentLevel = node.data("knowledge");
  const currentIdx = KNOWLEDGE_LEVELS.indexOf(currentLevel);
  const nextLevel = KNOWLEDGE_LEVELS[(currentIdx + 1) % KNOWLEDGE_LEVELS.length];
  node.data("knowledge", nextLevel);
  updateSidebar();
  updatePrompt();
});
```

### Zod Topic Schema
```typescript
// Source: Zod docs (https://zod.dev)
import { z } from "zod";

const CategorySchema = z.object({
  id: z.string().regex(/^[a-z][a-z0-9-]*$/),
  label: z.string().min(1),
  color: z.string().regex(/^#[0-9a-fA-F]{6}$/),
});

const NodeSchema = z.object({
  id: z.string().regex(/^[a-z][a-z0-9-]*$/),
  label: z.string().min(1),
  category: z.string(),
  description: z.string().min(1),
  knowledge: z.enum(["know", "fuzzy", "unknown"]).default("fuzzy"),
  tags: z.array(z.string()).default([]),
});

const EdgeSchema = z.object({
  source: z.string(),
  target: z.string(),
  label: z.string().min(1),
  type: z.string().optional(),
});

const PresetSchema = z.object({
  id: z.string(),
  label: z.string().min(1),
  filter: z.union([
    z.object({ tags: z.array(z.string()) }),
    z.object({ categories: z.array(z.string()) }),
    z.object({ nodeIds: z.array(z.string()) }),
    z.literal("all"),
  ]),
});

export const TopicSchema = z.object({
  metadata: z.object({
    title: z.string().min(1),
    slug: z.string().regex(/^[a-z][a-z0-9-]*$/),
    version: z.string().default("1.0.0"),
    description: z.string().optional(),
  }),
  categories: z.array(CategorySchema).min(1),
  nodes: z.array(NodeSchema).min(1),
  edges: z.array(EdgeSchema),
  presets: z.array(PresetSchema).default([]),
  promptTemplate: z.object({
    intro: z.string(),
    knowPrefix: z.string(),
    fuzzyPrefix: z.string(),
    unknownPrefix: z.string(),
    edgePrefix: z.string(),
    outro: z.string(),
  }).optional(),
});

export type TopicData = z.infer<typeof TopicSchema>;
```

### Bun Build Pipeline (Complete)
```typescript
// Source: Bun docs (https://bun.sh/docs/bundler, https://bun.sh/docs/runtime/html-rewriter)
// build.ts - Run with: bun run src/explorer/build.ts topics/dividend-strategy.json

import { TopicSchema } from "./schemas/topic-schema";

async function build(topicPath: string) {
  // Validate
  const raw = await Bun.file(topicPath).json();
  const result = TopicSchema.safeParse(raw);
  if (!result.success) {
    console.error("Validation failed:");
    for (const issue of result.error.issues) {
      console.error(`  ${issue.path.join(".")}: ${issue.message}`);
    }
    process.exit(1);
  }
  const topic = result.data;

  // Cross-validate: all edge source/target IDs must exist in nodes
  const nodeIds = new Set(topic.nodes.map((n) => n.id));
  for (const edge of topic.edges) {
    if (!nodeIds.has(edge.source))
      throw new Error(`Edge references unknown source node: ${edge.source}`);
    if (!nodeIds.has(edge.target))
      throw new Error(`Edge references unknown target node: ${edge.target}`);
  }

  // Bundle JS
  const jsBundle = await Bun.build({
    entrypoints: ["./src/explorer/template/explorer.ts"],
    format: "iife",
    target: "browser",
    minify: true,
    define: {
      "process.env.NODE_ENV": '"production"',
    },
  });
  if (!jsBundle.success) {
    console.error("JS bundle failed:", jsBundle.logs);
    process.exit(1);
  }
  const js = await jsBundle.outputs[0].text();

  // Read CSS
  const css = await Bun.file("./src/explorer/template/styles.css").text();

  // Read template
  const template = await Bun.file("./src/explorer/template/template.html").text();

  // Assemble
  const html = template
    .replace("__TOPIC_TITLE__", topic.metadata.title)
    .replace("/* __INJECT_CSS__ */", css)
    .replace(
      "/* __INJECT_TOPIC_DATA__ */",
      `const TOPIC_DATA = ${JSON.stringify(topic)};`
    )
    .replace("/* __INJECT_APP_JS__ */", js);

  const outPath = `./src/explorer/dist/${topic.metadata.slug}-explorer.html`;
  await Bun.write(outPath, html);
  console.log(`Built: ${outPath} (${(html.length / 1024).toFixed(1)} KB)`);
}

const topicFile = process.argv[2];
if (!topicFile) {
  console.error("Usage: bun run build.ts <topic.json>");
  process.exit(1);
}
await build(topicFile);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hand-rolled Canvas 2D graph rendering | Cytoscape.js library | Always been available; prototype predates research | Eliminates ~600 lines of custom rendering code. Gains layout algorithms, built-in interactions, styling system. |
| Cytoscape.js Canvas-only rendering | Cytoscape.js with optional WebGL mode | v3.31 (Jan 2025) - preview | WebGL mode gives >5x FPS improvement for large graphs (1200+ nodes). NOT recommended for this use case -- 20-50 node graphs run fine on Canvas 2D, and WebGL has edge rendering limitations. |
| Manual JSON validation with if/else | Zod schema validation | Zod stable since 2022 | Type-safe, structured errors, TypeScript type inference. |
| Webpack/Rollup for HTML bundling | Bun native HTML bundler | Bun 1.0+ (2023), improved in 1.3 | Zero-config bundling. But still outputs separate files, requiring inline post-processing. |

**Deprecated/outdated:**
- Cytoscape.js `cose-bilkent` layout: Superseded by `fcose` (faster, supports constraints). Use built-in `cose` for simple cases or `fcose` for complex ones.
- `cytoscape.load()` API: Deprecated. Use constructor `elements` option or `cy.add()`.

## Cytoscape.js WebGL vs Canvas Decision

**Decision: Use Canvas 2D renderer (default). Do NOT use WebGL.**

Rationale:
1. **Node count is tiny:** Knowledge explorers have 20-50 nodes. Canvas 2D handles thousands without issue. WebGL gains are meaningless at this scale.
2. **WebGL is preview:** Added in v3.31 (Jan 2025) with explicit "provisional, may change" warning.
3. **WebGL has edge limitations:** Only straight/haystack/bezier edges; no dashed lines; no gradients; single center labels only; triangle arrows only. These constraints would limit styling options.
4. **Canvas has full feature support:** All edge types, all arrow types, dashed/dotted lines, gradients, overlays, labels at source/target/center.
5. **Standalone file size:** WebGL doesn't add size (it's built into core). But enabling it adds complexity for zero performance benefit at this scale.

## Open Questions

Things that couldn't be fully resolved:

1. **Cytoscape.js node text wrapping with newlines**
   - What we know: The prototype uses `\n` in labels (e.g., `"Investment-First\nMindset"`). Cytoscape.js supports `text-wrap: "wrap"` with `text-max-width`.
   - What's unclear: Whether Cytoscape.js respects `\n` in label data for explicit line breaks, or only wraps at `text-max-width` boundaries.
   - Recommendation: Test during implementation. If `\n` doesn't work, use `text-max-width` to force wrapping at the right width, or pre-process labels.

2. **Optimal CoSE layout parameters for knowledge graphs**
   - What we know: CoSE has many tuning parameters (gravity, repulsion, idealEdgeLength, numIter). The prototype uses custom force parameters.
   - What's unclear: Exact optimal values for 20-50 node knowledge graphs with 6 categories.
   - Recommendation: Start with defaults, tune iteratively. Store layout params in topic JSON if per-topic tuning is needed.

3. **Prompt template complexity**
   - What we know: The prototype has a sophisticated prompt generator that builds context-aware learning prompts based on knowledge levels and graph relationships.
   - What's unclear: Whether the prompt generation logic should live in the topic JSON (declarative) or in the template engine code (imperative).
   - Recommendation: Topic JSON provides prompt fragments (intro, prefixes, outro). Template engine code handles the assembly logic (filtering by knowledge level, selecting relevant edges). This keeps the template engine generic while allowing per-topic prompt customization.

4. **fcose dependency bundling**
   - What we know: fcose requires `layout-base` and `cose-base` as dependencies.
   - What's unclear: Whether Bun's bundler correctly tree-shakes and bundles these when imported via `cytoscape.use(fcose)`.
   - Recommendation: Start with built-in `cose` layout. Only add fcose if layout quality is insufficient. Test bundling if added.

## Sources

### Primary (HIGH confidence)
- Bun HTML bundler docs (https://bun.sh/docs/bundler/html) -- Fetched 2026-02-02. Confirmed: produces separate files, not single HTML.
- Bun Bundler API docs (https://bun.sh/docs/bundler) -- Fetched 2026-02-02. Confirmed: `format: "iife"` support, `Bun.build()` API.
- Cytoscape.js official site (https://js.cytoscape.org) -- Fetched 2026-02-02. Confirmed: v3.33.1 current, 434KB minified, Canvas 2D renderer, no external deps.
- Cytoscape.js WebGL preview blog post (https://blog.js.cytoscape.org/2025/01/13/webgl-preview/) -- Fetched 2026-02-02. Confirmed: preview status, v3.31+, limitations documented.
- Zod official docs (https://zod.dev) -- Via Exa code search. Confirmed: `.safeParse()`, `.strict()`, type inference.
- Existing prototype at `.dev/playgrounds/dividend-strategy-explorer.html` -- Read directly from codebase. 990 lines, complete feature inventory extracted.

### Secondary (MEDIUM confidence)
- Bun HTMLRewriter API for inlining assets -- Perplexity search confirmed pattern exists; exact API usage needs validation during implementation.
- Cytoscape.js CoSE layout parameters for knowledge graphs -- Multiple Stack Overflow + docs sources agree on parameter meanings.

### Tertiary (LOW confidence)
- Cytoscape.js gzipped size (~110KB) -- Estimated at 25% of 434KB minified. Not verified with actual compression.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified via official documentation. Cytoscape.js version, size, and features confirmed. Zod already in project.
- Architecture: HIGH - Two-stage build pipeline validated against Bun docs. Template injection pattern is straightforward string replacement. Prototype read and analyzed for full feature inventory.
- Pitfalls: HIGH - Container sizing, IIFE format, DOM ready timing are well-documented Cytoscape.js issues. Build pipeline pitfalls verified against Bun docs.

**Research date:** 2026-02-02
**Valid until:** 2026-03-04 (30 days -- Cytoscape.js and Bun are stable releases)
