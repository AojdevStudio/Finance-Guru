# Phase 11: Self-Assessment, Persistence & Additional Topics - Research

**Researched:** 2026-02-03
**Domain:** Browser APIs (localStorage, Clipboard, Pointer Events), Cytoscape.js integration, topic data curation
**Confidence:** HIGH

## Summary

Phase 11 enhances the Phase 10 template engine with interactive features (4-state knowledge self-assessment, localStorage persistence, learning mode selector, cross-browser clipboard copy, mobile/touch support) and adds two new financial topic data files (options-greeks, risk-management). The technical domain is standard browser APIs -- all universally supported since 2019-2020 -- integrated with Cytoscape.js event and styling systems from Phase 10.

The primary risk is NOT browser API compatibility (all APIs are stable with 5+ years of universal support) but rather: (1) correct integration with Phase 10's Cytoscape.js application architecture, (2) the file:// protocol limitation for Clipboard API (confirmed: `navigator.clipboard.writeText` fails on `file://` in all browsers -- the textarea fallback is mandatory), and (3) curating high-quality concept graph data for two financial topics that matches the depth and tone of the existing dividend-strategy prototype.

Phase 10's architecture establishes key integration points: `explorer.ts` contains all application logic, Cytoscape.js manages graph rendering and events via `cy.on('tap', 'node', ...)`, node data is updated via `node.data(key, value)` which automatically triggers style recalculation through data-driven selectors (e.g., `node[knowledge = "know"]`), and the template HTML provides the DOM structure. Phase 11 modifies these existing files additively -- no structural rewrites required.

**Primary recommendation:** Modify `explorer.ts` to add persistence, 4-state cycling, learning modes, and clipboard features using the existing Cytoscape.js event system. All browser API access must use try/catch with silent degradation. Use `cy.batch()` for bulk node data updates (e.g., "Set All" buttons). Create topic JSON files conforming to the Phase 10 Zod schema exactly.

## Standard Stack

### Core

No new libraries required. Phase 11 uses only browser-native APIs integrated with Phase 10's existing Cytoscape.js.

| API | Support Since | Purpose | Why Standard |
|-----|--------------|---------|--------------|
| localStorage | All browsers since 2015 | Persist knowledge states and learning mode across page refreshes | Native, synchronous, 5MB per origin, sufficient for ~2KB of concept state data |
| navigator.clipboard.writeText | Chrome 66+, Firefox 63+, Safari 13.1+ (March 2020 baseline) | Copy generated learning prompt to clipboard | Universal support, async API, W3C standard |
| Pointer Events | Chrome 55+, Firefox 59+, Safari 13+ (July 2020 baseline) | Unified touch/mouse/pen input handling for graph interactions | W3C standard, replaces separate touch/mouse event handling |
| Blob + URL.createObjectURL | All browsers | JSON export fallback when localStorage unavailable | Standard pattern for client-side file downloads |

Source: MDN Web Docs (fetched 2026-02-03), CanIUse baseline data.

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| JSON.stringify/parse | Serialize/deserialize localStorage data | Every localStorage read/write |
| CSS @media (max-width: 768px) | Responsive sidebar for mobile viewports | Sidebar collapse to bottom drawer |
| CSS touch-action: none | Prevent browser default gestures on Cytoscape container | Applied to `#cy` element |
| cy.batch() | Batch Cytoscape.js data updates to avoid redundant style recalculations | "Set All Know/Fuzzy/Unknown" buttons, state restore on load |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| localStorage | IndexedDB | Overkill for ~2KB of knowledge state; localStorage is simpler and synchronous |
| localStorage | sessionStorage | Would NOT persist across page refreshes (session-scoped); violates EXPL-05 |
| Pointer Events | Touch Events + Mouse Events | Requires separate code paths; Pointer Events unify both; universal since Safari 13 (2019) |
| navigator.clipboard.writeText | document.execCommand('copy') only | execCommand is deprecated; clipboard API is the standard. But execCommand is needed as FALLBACK for file:// protocol |
| 4-state cycling | 3-state cycling (prototype's know/fuzzy/unknown) | Success criteria explicitly specifies 4 states: unknown/familiar/confident/mastered |

**Installation:** None required. All APIs are browser-native. Phase 10's cytoscape dependency is already installed.

## Architecture Patterns

### How Phase 11 Integrates with Phase 10

Phase 10 creates: `explorer.ts` + `template.html` + `styles.css` + `build.ts` + `topic-schema.ts`
Phase 11 modifies: `explorer.ts` (add features), `template.html` (add UI elements), `styles.css` (add styles)
Phase 11 creates: `options-greeks.json`, `risk-management.json` (new topic data)

```
src/explorer/
  build.ts                          # Phase 10 creates (no changes needed for Phase 11)
  schemas/
    topic-schema.ts                 # Phase 10 creates (may need knowledge enum update)
  template/
    template.html                   # Phase 10 creates, Phase 11 modifies (adds mode selector, export btn)
    explorer.ts                     # Phase 10 creates, Phase 11 modifies (adds persistence, modes, etc.)
    styles.css                      # Phase 10 creates, Phase 11 modifies (adds responsive, state colors)
  topics/
    dividend-strategy.json          # Phase 10 creates
    options-greeks.json             # Phase 11 creates (EXPL-09a)
    risk-management.json            # Phase 11 creates (EXPL-09b)
  dist/                             # Build output (gitignored)
    dividend-strategy-explorer.html
    options-greeks-explorer.html
    risk-management-explorer.html
```

### Phase 10 Integration Points (Critical for Phase 11 Planning)

Phase 10's `explorer.ts` establishes these integration contracts that Phase 11 must respect:

1. **Cytoscape instance** (`cy`): Global Cytoscape.js instance initialized with CoSE layout
2. **Knowledge cycling via tap**: `cy.on('tap', 'node', ...)` cycles knowledge state via `node.data('knowledge', nextLevel)`
3. **Data-driven styling**: Knowledge state controls node border-color via Cytoscape selectors: `node[knowledge = "know"]`
4. **Style auto-refresh**: Cytoscape.js automatically recalculates styles when `node.data()` changes -- no manual refresh needed
5. **Batch updates**: `cy.batch()` defers style recalculation until batch ends -- use for bulk operations
6. **TOPIC_DATA**: Global constant injected at build time, contains all topic metadata, nodes, edges, presets, promptTemplate
7. **DOM elements**: Template HTML provides `#cy`, `#node-list`, `#prompt-text`, `#stat-*`, `#copy-btn`, `#preset-buttons`, etc.
8. **Update functions**: `updateSidebar()`, `updatePrompt()`, `updateStats()` called after every state change

**Phase 11 changes to these contracts:**

- **Knowledge enum**: Phase 10 uses `['fuzzy', 'know', 'unknown']`. Phase 11 changes to `['unknown', 'familiar', 'confident', 'mastered']`. This requires:
  - Adding new Cytoscape style selectors for `familiar`, `confident`, `mastered`
  - Updating `cycleKnowledge` function
  - Updating stats display for 4 states
  - Updating prompt generation for 4 states
  - **Schema consideration**: Phase 10 Zod schema defines `knowledge: z.enum(["know", "fuzzy", "unknown"])`. Phase 11 must extend this to include `"familiar"`, `"confident"`, `"mastered"` OR use a backward-compatible approach where the schema allows any string and validation is in the application.

- **No structural changes**: Phase 11 adds features INTO the existing architecture. No refactors, no new files beyond topic JSONs, no dependency additions.

### Pattern 1: Safe localStorage Wrapper with Version-Keyed Storage

**What:** A thin wrapper around localStorage that handles all failure modes (private browsing, quota exceeded, security restrictions, disabled storage) with silent degradation.
**When to use:** Every localStorage read/write in the explorer.

```typescript
// Source: MDN localStorage docs (fetched 2026-02-03), Perplexity quota research
const STORAGE_PREFIX = 'fin-guru-explorer';
const STORAGE_VERSION = 'v1';

function storageKey(topicId: string): string {
  return `${STORAGE_PREFIX}.${STORAGE_VERSION}.${topicId}`;
}

// Feature detection -- test write/read/remove (catches all failure modes)
function isStorageAvailable(): boolean {
  const testKey = '__storage_test__';
  try {
    localStorage.setItem(testKey, 'test');
    localStorage.removeItem(testKey);
    return true;
  } catch {
    return false;
  }
}

const storageAvailable = isStorageAvailable();

interface ExplorerState {
  version: string;
  topicId: string;
  knowledge: Record<string, string>; // nodeId -> knowledge state
  learningMode: string;              // 'guided' | 'standard' | 'yolo'
  updatedAt: number;
}

function saveState(topicId: string, knowledge: Record<string, string>, learningMode: string): boolean {
  if (!storageAvailable) return false;
  try {
    const data: ExplorerState = {
      version: STORAGE_VERSION,
      topicId,
      knowledge,
      learningMode,
      updatedAt: Date.now(),
    };
    localStorage.setItem(storageKey(topicId), JSON.stringify(data));
    return true;
  } catch {
    // QuotaExceededError (DOMException code 22) or SecurityError -- degrade silently
    return false;
  }
}

function loadState(topicId: string): ExplorerState | null {
  if (!storageAvailable) return null;
  try {
    const raw = localStorage.getItem(storageKey(topicId));
    if (!raw) return null;
    const data = JSON.parse(raw) as ExplorerState;
    if (data.version !== STORAGE_VERSION) {
      return null; // Discard incompatible versions (migration point for future)
    }
    return data;
  } catch {
    return null;
  }
}
```

**Key details verified:**
- localStorage quota is 5MB per origin across Chrome, Safari, Firefox (Perplexity search, verified 2026-02-03)
- Each explorer's state is ~2KB max (20 nodes x 30 bytes per node ID + state), well under 5MB even with hundreds of topics
- Private browsing: data persists during session but cleared on tab close (MDN, fetched 2026-02-03). No throw on write.
- `file://` origin: may throw SecurityError in some browsers (MDN, fetched 2026-02-03). The try/catch wrapper handles this.

### Pattern 2: 4-State Knowledge Cycling via Cytoscape Data

**What:** Clicking a node cycles through 4 knowledge states using Cytoscape.js's `node.data()` API, which auto-triggers style updates through data-driven selectors.
**When to use:** Node tap interaction and sidebar badge click.

```typescript
// Source: Cytoscape.js docs cy.on (fetched 2026-02-03), success criteria SC-1
const KNOWLEDGE_STATES = ['unknown', 'familiar', 'confident', 'mastered'] as const;

const KNOWLEDGE_COLORS: Record<string, { ring: string; badge: string; text: string }> = {
  unknown:   { ring: '#f85149', badge: 'rgba(248,81,73,0.15)', text: '#f85149' },
  familiar:  { ring: '#d29922', badge: 'rgba(210,153,34,0.15)', text: '#d29922' },
  confident: { ring: '#58a6ff', badge: 'rgba(88,166,255,0.15)', text: '#58a6ff' },
  mastered:  { ring: '#3fb950', badge: 'rgba(63,185,80,0.15)', text: '#3fb950' },
};

// Cytoscape style selectors for knowledge-driven border colors
// These go in the stylesheet array and automatically apply when data changes
const knowledgeStyles = [
  { selector: 'node[knowledge = "unknown"]',   style: { 'border-color': '#f85149', 'border-width': 2.5 } },
  { selector: 'node[knowledge = "familiar"]',  style: { 'border-color': '#d29922', 'border-width': 2.5 } },
  { selector: 'node[knowledge = "confident"]', style: { 'border-color': '#58a6ff', 'border-width': 2.5 } },
  { selector: 'node[knowledge = "mastered"]',  style: { 'border-color': '#3fb950', 'border-width': 2.5 } },
];

// Tap handler -- replaces Phase 10's 3-state cycling
cy.on('tap', 'node', (evt) => {
  const node = evt.target;
  const current = node.data('knowledge') as string;
  const idx = KNOWLEDGE_STATES.indexOf(current as any);
  const next = KNOWLEDGE_STATES[(idx + 1) % KNOWLEDGE_STATES.length];
  node.data('knowledge', next);
  // Style update is AUTOMATIC -- Cytoscape recalculates from selectors
  debouncedSave();
  updateSidebar();
  updatePrompt();
  updateStats();
});
```

**Verified:** Cytoscape.js automatically recalculates styles when node data changes via `.data()` (Cytoscape.js docs, fetched 2026-02-03). No manual style refresh needed. `cy.batch()` should be used for bulk updates (e.g., "Set All Unknown").

### Pattern 3: Learning Mode Prompt Generation

**What:** Three prompt complexity tiers that change the vocabulary, structure, and relationship limit of the generated learning prompt.
**When to use:** Prompt generation in the prompt panel, triggered by any knowledge change or mode switch.

```typescript
// Source: Project spec (finance-guru-interactive-knowledge-explorer.md), adapted for 4-state model
const LEARNING_MODES = {
  guided: {
    label: 'Guided',
    description: 'Step-by-step explanations with examples',
    promptStyle: {
      prefix: "I'm a beginner learning about",
      unknownVerb: "Please explain from scratch",
      familiarVerb: "Please clarify with simple examples",
      confidentVerb: "Just confirm my understanding of",
      suffix: "Use analogies, concrete numbers, and build up step-by-step. Define any technical terms before using them.",
      maxRelationships: 4,
    },
  },
  standard: {
    label: 'Standard',
    description: 'Balanced depth with context',
    promptStyle: {
      prefix: "I'm studying",
      unknownVerb: "I need to learn",
      familiarVerb: "I need deeper understanding of",
      confidentVerb: "I want to verify my knowledge of",
      suffix: "Explain with practical examples and show how concepts connect. Include relevant formulas where applicable.",
      maxRelationships: 8,
    },
  },
  yolo: {
    label: 'YOLO',
    description: 'Dense, technical, no hand-holding',
    promptStyle: {
      prefix: "Advanced study of",
      unknownVerb: "Cover comprehensively",
      familiarVerb: "Deepen my understanding of",
      confidentVerb: "Challenge my assumptions about",
      suffix: "Be technical and precise. Include edge cases, mathematical foundations, and real-world failure modes. Skip introductory context.",
      maxRelationships: 12,
    },
  },
} as const;
```

**Integration with Phase 10 prompt generation:**
Phase 10's `updatePrompt()` uses `promptTemplate` from TOPIC_DATA with `knowPrefix`, `fuzzyPrefix`, `unknownPrefix`. Phase 11 must:
1. Wrap the existing prompt generation to accept a `learningMode` parameter
2. Replace the static prefixes with the mode's verb variants
3. Replace the hardcoded edge limit (8 in Phase 10) with `maxRelationships`
4. Append the mode's suffix instead of (or in addition to) the promptTemplate's outro
5. Persist the selected mode in localStorage alongside knowledge state

### Pattern 4: Cross-Browser Clipboard with Mandatory Fallback

**What:** Copy prompt text using Clipboard API with a MANDATORY fallback for `file://` protocol.
**When to use:** Copy button click handler.

```typescript
// Source: MDN Clipboard API (fetched 2026-02-03), Perplexity file:// research (2026-02-03)
//
// CRITICAL: navigator.clipboard.writeText DOES NOT WORK on file:// protocol
// in ANY browser (Chrome, Safari, Firefox). The textarea fallback is NOT optional.

async function copyPrompt(): Promise<void> {
  const text = document.getElementById('prompt-text')?.textContent || '';
  const btn = document.getElementById('copy-btn');
  if (!btn) return;

  let copied = false;

  // Try modern Clipboard API first (works on HTTPS and localhost)
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      copied = true;
    }
  } catch {
    // NotAllowedError (no user gesture), SecurityError (non-secure context), etc.
  }

  // Fallback: deprecated but works on file:// in most browsers
  if (!copied) {
    copied = fallbackCopy(text);
  }

  if (copied) {
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
  }
}

function fallbackCopy(text: string): boolean {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  textarea.select();
  textarea.setSelectionRange(0, 99999); // Mobile selection range
  let success = false;
  try {
    success = document.execCommand('copy');
  } catch {
    success = false;
  }
  document.body.removeChild(textarea);
  return success;
}
```

**IMPORTANT:** The `copyPrompt` function must be called DIRECTLY from the click event handler (not wrapped in additional async chains) to preserve user gesture context for the Clipboard API permission check.

### Pattern 5: Responsive Sidebar with Mobile Touch

**What:** Sidebar collapses to bottom drawer on mobile viewports. Cytoscape container uses `touch-action: none` to prevent browser gesture conflicts.
**When to use:** Screens narrower than 768px.

```css
/* Source: MDN Pointer Events docs (fetched 2026-02-03) */

/* Prevent browser default touch gestures on the graph container */
#cy {
  touch-action: none;
}

/* Mobile responsive sidebar */
@media (max-width: 768px) {
  .main {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    max-height: 40vh;
    border-right: none;
    border-bottom: 1px solid var(--border);
    order: 1; /* Move below canvas on mobile */
  }
  .graph-container {
    order: 0;
    min-height: 50vh;
  }
  .prompt-panel {
    order: 2;
  }
  .header-controls {
    flex-wrap: wrap;
    gap: 4px;
  }
  .mode-selector {
    width: 100%;
    justify-content: center;
  }
}
```

**Pointer Events note for Phase 11:**
Cytoscape.js internally handles pointer events for its canvas. Phase 11 does NOT need to add custom pointer event listeners for graph interactions -- Cytoscape's `tap` event already works across mouse, touch, and pen. The `touch-action: none` CSS is the only required addition to prevent browser gesture conflicts.

**What Phase 11 adds for mobile:**
- CSS `touch-action: none` on `#cy`
- Responsive sidebar CSS with `@media (max-width: 768px)`
- Viewport meta tag: `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
- Sidebar touch scrolling works naturally (do NOT add touch-action: none to sidebar)

### Pattern 6: Debounced Save Utility

**What:** Prevents excessive localStorage writes by batching rapid state changes.
**When to use:** After knowledge cycling (which can happen rapidly when clicking multiple nodes).

```typescript
function debounce<T extends (...args: any[]) => void>(fn: T, delay: number): T {
  let timer: ReturnType<typeof setTimeout>;
  return ((...args: any[]) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  }) as T;
}

const debouncedSave = debounce(() => {
  const knowledge: Record<string, string> = {};
  cy.nodes().forEach((node) => {
    knowledge[node.id()] = node.data('knowledge');
  });
  saveState(TOPIC_DATA.metadata.slug, knowledge, currentLearningMode);
}, 500);
```

### Pattern 7: JSON Export Fallback

**What:** When localStorage is unavailable, users can export their progress as a downloadable JSON file.
**When to use:** Always available as secondary action; prominent when localStorage is unavailable.

```typescript
// Source: Standard Blob/URL API pattern
function exportStateAsJSON(): void {
  const knowledge: Record<string, string> = {};
  cy.nodes().forEach((node) => {
    knowledge[node.id()] = node.data('knowledge');
  });
  const state = {
    topicId: TOPIC_DATA.metadata.slug,
    knowledge,
    learningMode: currentLearningMode,
    exportedAt: new Date().toISOString(),
  };
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${TOPIC_DATA.metadata.slug}-progress.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
```

### Anti-Patterns to Avoid

- **Saving to localStorage on every interaction:** Debounce saves to 500ms intervals. Only save on knowledge change + mode change, not on pointer moves or hovers.
- **Topic-specific JavaScript in template:** ALL interactive logic must work generically with any topic JSON via TOPIC_DATA. The template code must NEVER reference specific concept IDs.
- **Blocking render on localStorage load:** Render the graph immediately with default state, then apply persisted state after. Show graph first, restore state second.
- **Using touch events alongside pointer events:** Do NOT mix touch/mouse event listeners with pointer event listeners on the same element. Cytoscape handles this internally -- use its `tap` event.
- **Custom pointer event listeners on Cytoscape container:** Do NOT add `pointerdown`/`pointermove`/`pointerup` listeners on `#cy`. Cytoscape manages its own events. Only add event listeners for non-Cytoscape UI elements (buttons, sidebar).
- **Calling clipboard.writeText from nested async:** Must be called directly in click handler to preserve user gesture context.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Graph node click/tap | Custom pointer event hit testing | Cytoscape.js `cy.on('tap', 'node', ...)` | Cytoscape handles hit testing, touch/mouse unification, z-ordering |
| Node drag on mobile | Custom pointermove handler | Cytoscape.js built-in drag (default enabled) | Handles momentum, bounds, touch capture automatically |
| Knowledge state visual | Manual canvas draw per state | Cytoscape data-driven selectors `node[knowledge = "X"]` | Auto-refreshes when `node.data()` changes, zero manual work |
| Bulk node updates | Loop + individual `node.data()` calls | `cy.batch(() => { ... })` | Limits style recalculations to 1, limits redraws to 1 |
| Storage availability | userAgent sniffing | try/catch test write (Pattern 1) | Catches ALL failure modes: disabled, private, security, quota |
| Clipboard copy | Selection/range manipulation | navigator.clipboard.writeText + textarea fallback | The dual pattern covers 100% of browsers and protocols |
| Touch gesture prevention | Multiple event.preventDefault() calls | CSS `touch-action: none` on container | One CSS rule, works universally |

**Key insight:** Phase 11's value is in orchestrating existing APIs correctly, not in building new abstractions. Every feature maps to a well-supported browser API or Cytoscape.js capability. The risk is incorrect integration, not missing capability.

## Common Pitfalls

### Pitfall 1: Knowledge Schema Mismatch Between Phase 10 and Phase 11

**What goes wrong:** Phase 10 Zod schema defines `knowledge: z.enum(["know", "fuzzy", "unknown"])`. Phase 11 needs `["unknown", "familiar", "confident", "mastered"]`. Existing dividend-strategy.json defaults all nodes to "fuzzy".
**Why it happens:** Phase 11 upgrades the knowledge model without updating the schema.
**How to avoid:** Two options:
  - **Option A (recommended):** Update the Zod schema to accept ALL 7 values: `z.enum(["know", "fuzzy", "unknown", "familiar", "confident", "mastered"]).default("unknown")`. The explorer application only uses the 4-state cycle but the schema accepts legacy values for backward compatibility.
  - **Option B:** Change the schema to use `z.string().default("unknown")` and validate the application-level cycle in explorer.ts.
**Warning signs:** Build validation fails on the new topic JSONs because the schema rejects "familiar"/"confident"/"mastered" values.

### Pitfall 2: localStorage Key Collisions Between Topics

**What goes wrong:** Multiple explorer pages overwrite each other's state because they use the same localStorage key.
**Why it happens:** All explorers are on the same origin (file:// or localhost), so they share one localStorage namespace.
**How to avoid:** Include the topic slug in the storage key: `fin-guru-explorer.v1.{topicSlug}`. Each topic gets its own key. Verified: the slug comes from `TOPIC_DATA.metadata.slug`.
**Warning signs:** Switching between explorer pages resets your knowledge states.

### Pitfall 3: Clipboard API Fails on file:// Protocol

**What goes wrong:** `navigator.clipboard.writeText` throws `NotAllowedError` or `SecurityError` when the HTML is opened directly from disk (file:// protocol).
**Why it happens:** Clipboard API requires secure context (HTTPS or localhost). `file://` is NOT a secure context in Chrome, Safari, or Firefox (Perplexity search, verified 2026-02-03).
**How to avoid:** ALWAYS include the `fallbackCopy()` function using deprecated `document.execCommand('copy')` with a hidden textarea. The fallback works on `file://` in most browsers. Both copy paths must be implemented.
**Warning signs:** Copy button works in development (localhost) but fails when user opens the built HTML file directly from Finder/Explorer.

### Pitfall 4: Canvas Touch Gestures Conflict with Browser

**What goes wrong:** On mobile, interacting with the graph triggers page scroll, pinch-to-zoom, or pull-to-refresh instead of graph interaction.
**Why it happens:** Browser default touch behaviors are not suppressed on the Cytoscape container element.
**How to avoid:** Add `touch-action: none` CSS on `#cy` (the Cytoscape container). Cytoscape.js handles `preventDefault()` internally for its events, but `touch-action: none` is the CSS-level declaration that tells the browser to not process any default gestures on that element (MDN Pointer Events, fetched 2026-02-03).
**Warning signs:** Graph interactions work on desktop but fail or stutter on mobile.

### Pitfall 5: Bulk State Operations Without Batching

**What goes wrong:** "Set All Know" button is sluggish because it triggers style recalculation + redraw for each of 20 nodes individually.
**Why it happens:** Calling `node.data('knowledge', ...)` in a loop triggers N style calculations + N redraws.
**How to avoid:** Wrap bulk updates in `cy.batch()`:
```typescript
cy.batch(() => {
  cy.nodes(':visible').forEach(node => {
    node.data('knowledge', 'mastered');
  });
});
```
Verified: `cy.batch()` limits style updates to `eles.length` and redraws to exactly one (Cytoscape.js docs, fetched 2026-02-03).
**Warning signs:** "Set All" buttons cause visible flicker or lag.

### Pitfall 6: State Restore Applied Before Cytoscape Ready

**What goes wrong:** Persisted state is loaded and applied before Cytoscape has finished layout, causing visual glitch or state being overwritten by initialization.
**Why it happens:** localStorage.getItem is synchronous and fast, Cytoscape layout is async.
**How to avoid:** Apply persisted state AFTER Cytoscape initialization completes. Sequence: (1) Initialize Cytoscape with default data, (2) Run initial layout, (3) Load persisted state, (4) Apply knowledge states to nodes via batch update, (5) Update sidebar/stats/prompt.
**Warning signs:** Knowledge states show correct on first render but then reset to defaults.

### Pitfall 7: Topic Data Quality -- Disconnected Concept Graphs

**What goes wrong:** The CoSE layout places some concepts far from the main cluster because they have no edges connecting them to the rest of the graph.
**Why it happens:** Topic data is curated without checking for graph connectivity.
**How to avoid:** Every concept node must have at least one edge (source or target). Cross-validate during curation: build the edge set, verify every node ID appears in at least one edge.
**Warning signs:** One or more concept nodes float in isolation, far from the main cluster.

## Code Examples

### Cytoscape.js Knowledge Cycling with Auto-Style (Verified Pattern)

```typescript
// Source: Cytoscape.js docs - cy.on, node.data(), style selectors (fetched 2026-02-03)
// Key insight: node.data() change auto-triggers style recalculation from selectors

// In stylesheet array:
const knowledgeStyleRules = [
  { selector: 'node[knowledge = "unknown"]',   style: { 'border-color': '#f85149', 'border-width': 2.5 } },
  { selector: 'node[knowledge = "familiar"]',  style: { 'border-color': '#d29922', 'border-width': 2.5 } },
  { selector: 'node[knowledge = "confident"]', style: { 'border-color': '#58a6ff', 'border-width': 2.5 } },
  { selector: 'node[knowledge = "mastered"]',  style: { 'border-color': '#3fb950', 'border-width': 2.5 } },
];

// Event handler:
cy.on('tap', 'node', (evt) => {
  const node = evt.target;
  const current = node.data('knowledge');
  const idx = KNOWLEDGE_STATES.indexOf(current);
  const next = KNOWLEDGE_STATES[(idx + 1) % KNOWLEDGE_STATES.length];
  node.data('knowledge', next); // Style updates automatically
  debouncedSave();
  updateSidebar();
  updatePrompt();
  updateStats();
});
```

### Batch State Restore from localStorage

```typescript
// Apply persisted state after Cytoscape init
function restoreState(): void {
  const state = loadState(TOPIC_DATA.metadata.slug);
  if (!state) return;

  cy.batch(() => {
    for (const [nodeId, knowledge] of Object.entries(state.knowledge)) {
      const node = cy.getElementById(nodeId);
      if (node.length > 0 && KNOWLEDGE_STATES.includes(knowledge as any)) {
        node.data('knowledge', knowledge);
      }
    }
  });

  if (state.learningMode && state.learningMode in LEARNING_MODES) {
    setLearningMode(state.learningMode);
  }

  updateSidebar();
  updatePrompt();
  updateStats();
}
```

### Learning Mode UI Element

```html
<!-- In template.html header-controls area -->
<div class="mode-selector">
  <button class="mode-btn" data-mode="guided" title="Step-by-step explanations">Guided</button>
  <button class="mode-btn active" data-mode="standard" title="Balanced depth">Standard</button>
  <button class="mode-btn" data-mode="yolo" title="Dense, technical">YOLO</button>
</div>
```

```typescript
// Mode button wiring in explorer.ts
function initModeSelector(): void {
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = (btn as HTMLElement).dataset.mode;
      if (mode && mode in LEARNING_MODES) {
        setLearningMode(mode);
      }
    });
  });
}

function setLearningMode(mode: string): void {
  currentLearningMode = mode;
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.classList.toggle('active', (btn as HTMLElement).dataset.mode === mode);
  });
  debouncedSave();
  updatePrompt();
}
```

## Topic Data: Options Greeks (EXPL-09a)

Curated concept graph for the options-greeks topic. Confidence: MEDIUM (based on established financial domain knowledge -- concept selection is well-grounded but edge relationships are editorial judgments that should be reviewed).

### Concept Structure (~20 nodes, 5 categories, ~22 edges)

**Categories:**
| ID | Label | Color | Concept Count |
|----|-------|-------|---------------|
| core-greeks | Core Greeks | #58a6ff | 5 |
| option-fundamentals | Option Fundamentals | #3fb950 | 5 |
| time-effects | Time Effects | #d29922 | 3 |
| volatility-effects | Volatility Effects | #f85149 | 3 |
| strategy-impact | Strategy Impact | #bc8cff | 4 |

**Nodes (20):**
1. delta (Core Greeks) - "Measures how much option price changes per $1 move in underlying. Calls: 0 to 1, Puts: -1 to 0. ATM options have ~0.50 delta."
2. gamma (Core Greeks) - "Rate of change of delta. Highest for ATM options near expiration. Shows how quickly your directional exposure shifts."
3. theta (Core Greeks) - "Daily time decay -- how much value an option loses per day. Accelerates near expiration. Negative for long options, positive for short."
4. vega (Core Greeks) - "Sensitivity to implied volatility. A 1% IV increase changes option price by vega amount. Highest for ATM options with more time."
5. rho (Core Greeks) - "Interest rate sensitivity. Smallest impact for short-term options. Matters more for LEAPS and in high-rate environments."
6. option-premium (Option Fundamentals) - "Total price paid for an option. Composed of intrinsic value (real worth) plus extrinsic value (time + volatility premium)."
7. intrinsic-value (Option Fundamentals) - "What the option is worth if exercised now. Call: max(0, stock - strike). Put: max(0, strike - stock)."
8. extrinsic-value (Option Fundamentals) - "Time value + volatility premium. Decays to zero at expiration. The part of premium most sensitive to Greeks."
9. moneyness (Option Fundamentals) - "ITM/ATM/OTM status. Determines which Greeks dominate. ATM: max gamma/vega. Deep ITM: delta near 1. OTM: all extrinsic."
10. implied-volatility (Option Fundamentals) - "Market's forecast of future volatility baked into option prices. Higher IV = higher premiums. Driven by supply/demand."
11. time-decay-acceleration (Time Effects) - "Theta increases exponentially as expiration approaches. The last 30 days destroy the most time value. Sellers' advantage."
12. expiration-dynamics (Time Effects) - "At expiration: extrinsic value goes to zero, gamma spikes for ATM options, and delta snaps to 0 or 1."
13. dte-impact (Time Effects) - "Days to expiration affects ALL Greeks. More DTE = more vega, less gamma, slower theta. Trade-off between time protection and cost."
14. iv-crush (Volatility Effects) - "Sharp drop in implied volatility after known events (earnings, FDA decisions). Options lose value even if underlying moves favorably."
15. iv-skew (Volatility Effects) - "OTM puts typically have higher IV than OTM calls (fear premium). Skew changes with market conditions and affects relative pricing."
16. vol-regime (Volatility Effects) - "Low-vol vs high-vol environments change which strategies work. Low vol favors long vega; high vol favors short vega."
17. delta-hedging (Strategy Impact) - "Maintaining delta-neutral positions by adjusting stock/option ratios. Used by market makers. Requires frequent rebalancing due to gamma."
18. gamma-risk (Strategy Impact) - "Short gamma positions can suffer catastrophic losses on large moves near expiration. The hidden risk in selling options."
19. theta-harvesting (Strategy Impact) - "Selling options to collect time decay. Covered calls, cash-secured puts, iron condors. Profitable in range-bound markets."
20. vega-trading (Strategy Impact) - "Trading volatility rather than direction. Buy options when IV is cheap, sell when expensive. Straddles, strangles, calendar spreads."

**Edges (22):** delta->gamma (accelerated by), gamma->delta-hedging (necessitates), theta->time-decay-acceleration (manifests as), vega->implied-volatility (measures sensitivity to), option-premium->intrinsic-value (composed of), option-premium->extrinsic-value (composed of), moneyness->delta (determines), moneyness->gamma (peaks at ATM), implied-volatility->iv-crush (collapses in), implied-volatility->iv-skew (shapes), implied-volatility->vol-regime (defines environment), time-decay-acceleration->expiration-dynamics (culminates in), dte-impact->theta (scales), dte-impact->vega (scales), dte-impact->gamma (scales inversely), gamma-risk->gamma (drives), theta-harvesting->theta (exploits), vega-trading->vega (targets), delta-hedging->gamma-risk (mitigates), iv-crush->vega-trading (threatens), vol-regime->theta-harvesting (determines effectiveness of), rho->dte-impact (amplified by longer).

**Preset Filters:**
- "All" (all nodes)
- "Core Greeks" (core-greeks category)
- "Volatility & Time" (time-effects + volatility-effects categories)
- "Strategy Applications" (strategy-impact category)

### Connectivity validation: Every node appears in at least 1 edge. No orphan nodes.

## Topic Data: Risk Management (EXPL-09b)

Curated concept graph for the risk-management topic. Confidence: MEDIUM (same basis as options-greeks).

### Concept Structure (~20 nodes, 5 categories, ~22 edges)

**Categories:**
| ID | Label | Color | Concept Count |
|----|-------|-------|---------------|
| risk-measurement | Risk Measurement | #f85149 | 5 |
| performance-metrics | Performance Metrics | #58a6ff | 4 |
| position-management | Position Management | #3fb950 | 4 |
| portfolio-diversification | Portfolio Diversification | #d29922 | 4 |
| risk-control-strategies | Risk Control Strategies | #bc8cff | 3 |

**Nodes (20):**
1. var (Risk Measurement) - "Value at Risk: maximum expected loss over a time period at a confidence level. Example: 95% 1-day VaR of $10k means only 5% chance of losing more than $10k in a day."
2. cvar (Risk Measurement) - "Conditional VaR (Expected Shortfall): average loss BEYOND VaR. Answers 'when things go bad, how bad?' Better tail risk measure than VaR."
3. volatility (Risk Measurement) - "Standard deviation of returns. Measures price fluctuation magnitude. Annualized vol of 20% means ~1.26% daily moves expected."
4. beta (Risk Measurement) - "Systematic risk relative to market. Beta 1.5 = 50% more volatile than benchmark. Cannot be diversified away."
5. max-drawdown (Risk Measurement) - "Largest peak-to-trough decline. SPY's worst: -56% in 2008. Critical for sizing positions and setting expectations."
6. sharpe-ratio (Performance Metrics) - "Risk-adjusted return: (return - risk-free rate) / volatility. Above 1.0 is good, above 2.0 is excellent. Penalizes both upside and downside vol."
7. sortino-ratio (Performance Metrics) - "Like Sharpe but only penalizes DOWNSIDE volatility. Better for asymmetric return distributions. Preferred for strategies with positive skew."
8. alpha (Performance Metrics) - "Excess return above benchmark after adjusting for risk. Positive alpha = skill or edge. Hard to sustain long-term."
9. calmar-ratio (Performance Metrics) - "Annualized return divided by max drawdown. Measures return per unit of worst-case pain. Higher is better."
10. position-sizing (Position Management) - "Determining how much capital to allocate per position. Controls risk exposure. The single most important risk management decision."
11. kelly-criterion (Position Management) - "Mathematical formula for optimal bet size: f* = (bp - q) / b. Maximizes long-term growth. Full Kelly is too aggressive -- use half-Kelly."
12. stop-loss (Position Management) - "Exit rule to limit losses on a position. Fixed percentage, trailing, volatility-based (2x ATR). Prevents catastrophic single-position losses."
13. concentration-risk (Position Management) - "Over-exposure to a single position, sector, or factor. Rule of thumb: no single position > 5-10% of portfolio."
14. diversification (Portfolio Diversification) - "Spreading investments to reduce unsystematic risk. Requires low-correlation assets. More positions don't help if everything is correlated."
15. correlation (Portfolio Diversification) - "How assets move together. -1 to +1 scale. Low/negative correlation improves diversification. Correlations increase in crises (correlation breakdown)."
16. asset-allocation (Portfolio Diversification) - "Strategic portfolio mix across asset classes (stocks, bonds, alternatives). Drives 90%+ of portfolio return variation."
17. rebalancing (Portfolio Diversification) - "Adjusting portfolio back to target weights. Calendar-based (quarterly) or threshold-based (5% drift). Enforces buy-low-sell-high discipline."
18. hedging (Risk Control Strategies) - "Using offsetting positions to reduce specific risks. Puts for downside protection, shorts for market exposure reduction. Has a cost (insurance premium)."
19. vol-regime-awareness (Risk Control Strategies) - "Markets alternate between low-volatility (calm) and high-volatility (crisis) regimes. Risk management approach should adapt to current regime."
20. tail-risk (Risk Control Strategies) - "Risk of extreme, rare events (3+ sigma moves). Standard models underestimate it. Black swans, fat tails, crash risk. Managed through position limits and hedging."

**Edges (22):** var->cvar (extended by), volatility->var (input to), volatility->sharpe-ratio (denominator of), beta->volatility (component of systematic), max-drawdown->calmar-ratio (denominator of), sharpe-ratio->sortino-ratio (refined by), alpha->sharpe-ratio (contextualized by), position-sizing->concentration-risk (prevents), kelly-criterion->position-sizing (optimizes), stop-loss->max-drawdown (limits), diversification->correlation (depends on low), correlation->asset-allocation (informs), asset-allocation->rebalancing (maintained by), hedging->volatility (reduces portfolio), hedging->tail-risk (protects against), vol-regime-awareness->hedging (triggers), vol-regime-awareness->position-sizing (adjusts), tail-risk->cvar (measured by), concentration-risk->diversification (solved by), rebalancing->concentration-risk (prevents drift toward), stop-loss->position-sizing (complements), beta->alpha (adjusted for in).

**Preset Filters:**
- "All" (all nodes)
- "Risk Measurement" (risk-measurement category)
- "Performance & Metrics" (performance-metrics category)
- "Position & Portfolio" (position-management + portfolio-diversification categories)
- "Risk Controls" (risk-control-strategies category)

### Connectivity validation: Every node appears in at least 1 edge. No orphan nodes.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| document.execCommand('copy') | navigator.clipboard.writeText + execCommand fallback | 2018-2019 Clipboard API, but file:// still needs fallback in 2026 | Dual approach required: modern API + legacy fallback |
| Separate mouse + touch events | Pointer Events API + Cytoscape tap event | Safari 13 (2019) completed universal support | Cytoscape.js abstracts this entirely; zero custom pointer code needed |
| Binary know/unknown states | Multi-level self-assessment (4 states) | Ongoing in education tech | Finer granularity produces better targeted learning prompts |
| Manual style updates after data change | Cytoscape.js data-driven stylesheet auto-refresh | Core Cytoscape feature since v2 | Zero manual style management when using data selectors |
| Individual node updates | cy.batch() for bulk operations | Core Cytoscape feature | Single redraw for N updates; critical for "Set All" operations |

**Deprecated/outdated:**
- `document.execCommand('copy')`: Deprecated in all browsers but REQUIRED as fallback for file:// protocol. Do not use as primary approach.
- Touch Events for unified handling: Pointer Events API is the standard. But Cytoscape.js handles this internally, so Phase 11 needs zero custom pointer event code.
- PEP (Pointer Events Polyfill): Unnecessary since Safari 13 (2019).

## Open Questions

1. **Zod Schema Knowledge Enum Update**
   - What we know: Phase 10 schema uses `z.enum(["know", "fuzzy", "unknown"])`. Phase 11 needs 4 new states.
   - What is unclear: Whether Phase 10 has already been executed (schema exists) or whether Phase 11 planning can specify schema changes.
   - Recommendation: Phase 11 Plan 02 (template enhancements) should include updating the Zod schema to accept all 7 values with `.default("unknown")`. This is a one-line change in `topic-schema.ts`. New topic JSONs use "unknown" as default. Existing dividend-strategy.json keeps "fuzzy" defaults (backward compatible).

2. **Prompt Template Integration Depth**
   - What we know: Phase 10 defines a `promptTemplate` field in the topic JSON with `knowPrefix`, `fuzzyPrefix`, `unknownPrefix`. Phase 11 adds learning modes that override these prefixes.
   - What is unclear: The exact precedence when both `promptTemplate` from topic JSON AND learning mode are active.
   - Recommendation: Learning mode vocabulary takes precedence when a mode is selected. The topic JSON `promptTemplate.intro` and `promptTemplate.outro` provide topic-specific context. Learning mode provides vocabulary (`unknownVerb`, `familiarVerb`, etc.) and structure (`maxRelationships`). These compose: topic provides context, mode provides complexity level.

3. **State Migration When Knowledge States Change**
   - What we know: A user who used the Phase 10 explorer with 3-state knowledge ("know"/"fuzzy"/"unknown") will have localStorage data with those values.
   - What is unclear: How to map old states to new states when the user opens the Phase 11 explorer.
   - Recommendation: Implement simple migration in `loadState()`: map "know" -> "mastered", "fuzzy" -> "familiar", "unknown" -> "unknown". This preserves user progress with reasonable mappings. The version field in the state object (STORAGE_VERSION) enables detecting old formats.

4. **Performance Budget for Sub-1-Second Load (EXPL-16)**
   - What we know: Generated HTML is ~400-600KB (Cytoscape.js ~434KB minified + topic data + app code + CSS). Loading from local filesystem is effectively instant for I/O.
   - What is unclear: Whether Cytoscape.js CoSE layout computation for 20 nodes takes notable time.
   - Recommendation: CoSE layout with `animate: false` and `numIter: 2000` on 20 nodes should compute in <100ms. Total budget: file load (<10ms local), HTML parse + CSS apply (<50ms), JS execute (<100ms), CoSE layout (<100ms) = well under 1 second. No performance optimization needed.

## Sources

### Primary (HIGH confidence)
- MDN Web Docs - localStorage: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage (fetched 2026-02-03)
- MDN Web Docs - Clipboard API writeText: https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText (fetched 2026-02-03)
- MDN Web Docs - Pointer Events: https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events (fetched 2026-02-03)
- Cytoscape.js docs - cy.on event handling: https://js.cytoscape.org/#cy.on (fetched 2026-02-03)
- Cytoscape.js docs - data-driven styling: https://js.cytoscape.org/#style/data-mapping (fetched 2026-02-03)
- Cytoscape.js docs - cy.batch: https://js.cytoscape.org/#cy.batch (fetched 2026-02-03)
- Phase 10 research and plans: `.planning/phases/10-template-engine-dividend-topic-port/10-RESEARCH.md`, `10-01-PLAN.md`, `10-02-PLAN.md`, `10-03-PLAN.md` (read from codebase)
- Existing prototype: `.dev/playgrounds/dividend-strategy-explorer.html` (990 lines, read from codebase)
- Project spec: `.dev/specs/backlog/finance-guru-interactive-knowledge-explorer.md` (read from codebase)

### Secondary (MEDIUM confidence)
- Perplexity search: localStorage quota 5MB per origin confirmed across Chrome/Safari/Firefox (2026-02-03)
- Perplexity search: navigator.clipboard.writeText fails on file:// in all browsers (2026-02-03)
- Exa code search: Cytoscape.js tap event patterns from official docs and Stack Overflow (2026-02-03)
- Financial topic data: Based on established options pricing theory and risk management principles; relationships are editorial judgments

### Tertiary (LOW confidence)
- Learning mode UI patterns: Original design for this project, not based on specific EdTech implementations. The guided/standard/yolo tier design is project-specific.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All browser APIs verified via MDN with universal support since 2019-2020. Cytoscape.js integration patterns verified via official docs.
- Architecture patterns: HIGH - All patterns verified against Phase 10 architecture and Cytoscape.js docs. Integration points are well-defined.
- Topic data curation: MEDIUM - Concepts are well-established financial knowledge. Edge relationships are editorial judgments. Node descriptions are practitioner-level but should be reviewed.
- Pitfalls: HIGH - All 7 pitfalls are verified failure modes: file:// clipboard failure (Perplexity), schema mismatch (codebase analysis), batch performance (Cytoscape docs), storage key collision (standard localStorage behavior).

**Research date:** 2026-02-03
**Valid until:** 2026-03-05 (30 days -- browser APIs and Cytoscape.js are stable; topic data is evergreen)
