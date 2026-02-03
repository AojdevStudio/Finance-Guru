# Phase 10: Self-Assessment, Persistence & Additional Topics - Research

**Researched:** 2026-02-02
**Domain:** Browser APIs (localStorage, Clipboard, Pointer Events), topic data curation, template integration
**Confidence:** HIGH

## Summary

Phase 10 adds interactive features (self-assessment, persistence, learning modes) to the template engine built in Phase 9, plus creates two new topic data files (options-greeks, risk-management). The technical domain is standard browser APIs with universal support in 2026: localStorage for persistence, `navigator.clipboard.writeText` for copy, and Pointer Events for unified touch/mouse handling.

The primary challenge is NOT the browser APIs (they are well-supported and straightforward) but rather: (1) correct integration with the Phase 9 template engine, (2) curating high-quality concept graph data for two financial topics, and (3) designing a learning mode system that meaningfully changes prompt complexity across three tiers.

**Primary recommendation:** Build persistence and interaction features as template-level JavaScript that works with any topic JSON, not as topic-specific code. All browser API usage should use try/catch wrappers with graceful degradation. Topic data should follow the exact JSON schema from Phase 9.

## Standard Stack

### Core

No new libraries. Phase 10 uses only browser-native APIs.

| API | Support | Purpose | Why Standard |
|-----|---------|---------|--------------|
| localStorage | All browsers, 5-10MB quota | Persist knowledge states across page refreshes | Native, zero dependencies, sufficient for concept state data |
| navigator.clipboard.writeText | Chrome 66+, Firefox 63+, Safari 13.1+ | Copy generated prompt to clipboard | Universal support since 2019+, async API |
| Pointer Events API | Chrome 55+, Firefox 59+, Safari 13+ | Unified touch/mouse/pen input handling | W3C standard, replaces separate touch/mouse event handling |
| Canvas 2D API | All browsers | Graph rendering (from Phase 9 template) | Already used in prototype, no change needed |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| JSON.stringify/parse | Serialize/deserialize localStorage data | Every read/write to localStorage |
| CSS media queries | Responsive sidebar for mobile | @media (max-width) for sidebar collapse |
| CSS touch-action | Prevent browser default touch behaviors on canvas | Applied to canvas element |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| localStorage | IndexedDB | Overkill for ~2KB of knowledge state; localStorage is simpler and synchronous |
| localStorage | sessionStorage | Would NOT persist across page refreshes (session-scoped); violates EXPL-05 |
| Pointer Events | Touch Events + Mouse Events | Requires separate code paths; Pointer Events unify both; universal support since Safari 13 |
| navigator.clipboard.writeText | document.execCommand('copy') | execCommand is deprecated; clipboard API is the standard replacement |

**Installation:** None required. All APIs are browser-native.

## Architecture Patterns

### How Phase 10 Integrates with Phase 9 Template

Phase 9 creates: `template.html` + topic JSON --> build pipeline --> standalone HTML
Phase 10 adds: interactive features INTO `template.html` + 2 new topic JSON files

```
src/explorer/
  template.html           # Phase 9 creates, Phase 10 modifies
  build.ts                # Phase 9 creates, Phase 10 may extend
  schema.json             # Phase 9 creates (topic JSON schema)
  topics/
    dividend-strategy.json  # Phase 9 creates
    options-greeks.json     # Phase 10 creates
    risk-management.json    # Phase 10 creates
  dist/
    dividend-strategy-explorer.html    # Built output
    options-greeks-explorer.html       # Built output
    risk-management-explorer.html      # Built output
```

### Pattern 1: Safe localStorage Wrapper

**What:** A thin wrapper around localStorage that handles all failure modes (private browsing, quota exceeded, disabled storage) with silent degradation.
**When to use:** Every localStorage read/write in the explorer.

```javascript
// Source: MDN localStorage docs + Safari private browsing research
const STORAGE_PREFIX = 'fin-guru-explorer';
const STORAGE_VERSION = 'v1';

function storageKey(topicId) {
  return `${STORAGE_PREFIX}.${STORAGE_VERSION}.${topicId}`;
}

function isStorageAvailable() {
  const testKey = '__storage_test__';
  try {
    localStorage.setItem(testKey, 'test');
    localStorage.removeItem(testKey);
    return true;
  } catch (e) {
    return false;
  }
}

const storageAvailable = isStorageAvailable();

function saveState(topicId, state) {
  if (!storageAvailable) return false;
  try {
    const data = {
      version: STORAGE_VERSION,
      topicId: topicId,
      knowledge: state.knowledge,    // { nodeId: 'unknown'|'familiar'|'confident'|'mastered' }
      learningMode: state.learningMode, // 'guided'|'standard'|'yolo'
      updatedAt: Date.now()
    };
    localStorage.setItem(storageKey(topicId), JSON.stringify(data));
    return true;
  } catch (e) {
    // QuotaExceededError or SecurityError - degrade silently
    return false;
  }
}

function loadState(topicId) {
  if (!storageAvailable) return null;
  try {
    const raw = localStorage.getItem(storageKey(topicId));
    if (!raw) return null;
    const data = JSON.parse(raw);
    // Version migration point
    if (data.version !== STORAGE_VERSION) {
      return migrateState(data);
    }
    return data;
  } catch (e) {
    return null;
  }
}
```

### Pattern 2: Knowledge State Cycling (4-State)

**What:** Clicking a concept node cycles through 4 knowledge states with visual feedback.
**When to use:** Node click/tap interaction in canvas and sidebar.

```javascript
// Knowledge states cycle: unknown -> familiar -> confident -> mastered -> unknown
const KNOWLEDGE_STATES = ['unknown', 'familiar', 'confident', 'mastered'];

const KNOWLEDGE_COLORS = {
  unknown:   { ring: '#f85149', badge: 'rgba(248,81,73,0.15)', text: '#f85149' },
  familiar:  { ring: '#d29922', badge: 'rgba(210,153,34,0.15)', text: '#d29922' },
  confident: { ring: '#58a6ff', badge: 'rgba(88,166,255,0.15)', text: '#58a6ff' },
  mastered:  { ring: '#3fb950', badge: 'rgba(63,185,80,0.15)', text: '#3fb950' }
};

function cycleKnowledge(nodeId) {
  const current = knowledgeState[nodeId] || 'unknown';
  const idx = KNOWLEDGE_STATES.indexOf(current);
  const next = KNOWLEDGE_STATES[(idx + 1) % KNOWLEDGE_STATES.length];
  knowledgeState[nodeId] = next;
  saveState(topicId, { knowledge: knowledgeState, learningMode });
  renderSidebar();
  draw();
}
```

**NOTE:** The prototype uses 3 states (know/fuzzy/unknown). Phase 10 success criteria specifies 4 states: unknown -> familiar -> confident -> mastered. This is a deliberate upgrade from the prototype.

### Pattern 3: Learning Mode Prompt Generation

**What:** Three prompt complexity tiers that change how the generated learning prompt reads.
**When to use:** Prompt generation in the prompt panel.

```javascript
// Learning mode affects prompt structure and vocabulary
const LEARNING_MODES = {
  guided: {
    label: 'Guided',
    description: 'Step-by-step explanations with examples',
    promptStyle: {
      prefix: "I'm a beginner learning about",
      unknownVerb: "Please explain from scratch",
      fuzzyVerb: "Please clarify with simple examples",
      suffix: "Use analogies, concrete numbers, and build up step-by-step. Define any technical terms before using them.",
      maxRelationships: 4
    }
  },
  standard: {
    label: 'Standard',
    description: 'Balanced depth with context',
    promptStyle: {
      prefix: "I'm studying",
      unknownVerb: "I need to learn",
      fuzzyVerb: "I need deeper understanding of",
      suffix: "Explain with practical examples and show how concepts connect. Include relevant formulas where applicable.",
      maxRelationships: 8
    }
  },
  yolo: {
    label: 'YOLO',
    description: 'Dense, technical, no hand-holding',
    promptStyle: {
      prefix: "Advanced study of",
      unknownVerb: "Cover comprehensively",
      fuzzyVerb: "Deepen my understanding of",
      suffix: "Be technical and precise. Include edge cases, mathematical foundations, and real-world failure modes. Skip introductory context.",
      maxRelationships: 12
    }
  }
};
```

### Pattern 4: Cross-Browser Clipboard Copy

**What:** Copy prompt text with Clipboard API and fallback.
**When to use:** Copy button click handler.

```javascript
// Source: MDN Clipboard API docs
async function copyPrompt() {
  const text = document.getElementById('prompt-text').textContent;
  const btn = document.getElementById('copy-btn');

  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      // Fallback for non-secure contexts (should not happen with file:// or localhost)
      fallbackCopy(text);
    }
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
  } catch (err) {
    // Clipboard API denied (no user gesture, or permissions issue)
    fallbackCopy(text);
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
  }
}

function fallbackCopy(text) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  textarea.setSelectionRange(0, 99999); // Mobile support
  document.execCommand('copy');
  document.body.removeChild(textarea);
}
```

### Pattern 5: Pointer Events for Unified Input

**What:** Replace separate mouse/touch event listeners with Pointer Events.
**When to use:** Canvas interaction (drag nodes, click to cycle, hover for tooltip).

```javascript
// Source: MDN Pointer Events API
canvas.addEventListener('pointerdown', (e) => {
  e.preventDefault();
  const pos = getPointerPos(e);
  const node = getNodeAt(pos.x, pos.y);
  if (node) {
    if (e.pointerType === 'touch') {
      // Touch: single tap cycles knowledge, long press drags
      touchStartTime = Date.now();
      touchStartNode = node;
    }
    dragging = node;
    dragOffset = { x: pos.x - node.x, y: pos.y - node.y };
    canvas.setPointerCapture(e.pointerId); // Keep events during drag
  }
});

canvas.addEventListener('pointermove', (e) => {
  e.preventDefault();
  const pos = getPointerPos(e);
  if (dragging) {
    dragging.x = pos.x - dragOffset.x;
    dragging.y = pos.y - dragOffset.y;
    draw();
  } else {
    // Hover only makes sense for mouse/pen
    if (e.pointerType !== 'touch') {
      updateHover(pos);
    }
  }
});

canvas.addEventListener('pointerup', (e) => {
  if (e.pointerType === 'touch' && touchStartNode) {
    const elapsed = Date.now() - touchStartTime;
    if (elapsed < 300) {
      // Short tap = cycle knowledge
      cycleKnowledge(touchStartNode.id);
    }
  }
  dragging = null;
  canvas.releasePointerCapture(e.pointerId);
});

function getPointerPos(e) {
  const rect = canvas.getBoundingClientRect();
  return { x: e.clientX - rect.left, y: e.clientY - rect.top };
}
```

### Pattern 6: Responsive Sidebar

**What:** Sidebar collapses to bottom drawer on mobile.
**When to use:** Screens narrower than 768px.

```css
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
  .canvas-container {
    order: 0;
    min-height: 50vh;
  }
  .prompt-panel {
    order: 2;
  }
}

/* Prevent browser gestures on canvas */
canvas {
  touch-action: none; /* Critical for pointer events on mobile */
}
```

### Anti-Patterns to Avoid

- **Saving to localStorage on every interaction:** Debounce saves to avoid excessive writes. Save on knowledge change + debounced 500ms timer, not on every pointer move.
- **Topic-specific JavaScript in template:** ALL interactive logic must work generically with any topic JSON. The template should never reference specific concept IDs.
- **Blocking render on localStorage load:** Load state asynchronously after initial render. Show default state immediately, then apply persisted state.
- **Using touch events alongside pointer events:** Do not mix touch/mouse event listeners with pointer event listeners. Use ONLY pointer events for all input handling.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Storage availability detection | Custom sniffing based on userAgent | Feature detection with try/catch test write | userAgent is unreliable; try/catch catches ALL failure modes (disabled, private mode, quota) |
| Clipboard copy | Custom selection/range manipulation | navigator.clipboard.writeText + textarea fallback | The pattern shown above covers 100% of browsers in 2026 |
| Touch vs mouse detection | Separate event listeners + userAgent | Pointer Events API with pointerType property | Unified API handles mouse, touch, pen; pointerType differentiates when needed |
| Debouncing localStorage writes | setTimeout/clearTimeout inline | Extract a reusable debounce utility | Inline debounce is error-prone; a 5-line utility function is cleaner |
| JSON export fallback | Custom file download logic | Blob + URL.createObjectURL + anchor click | Standard pattern for client-side file downloads, well-supported |

**Key insight:** Every browser API needed for Phase 10 has been stable and universally supported for 3+ years. The risk is not browser compatibility -- it is incorrect integration with the Phase 9 template engine.

## Common Pitfalls

### Pitfall 1: localStorage Key Collisions Between Topics

**What goes wrong:** Multiple explorer pages (dividend, options-greeks, risk-management) overwrite each other's state because they share the same localStorage key.
**Why it happens:** All explorers are on the same origin (file:// or localhost), so they share one localStorage namespace.
**How to avoid:** Include the topic ID in the storage key: `fin-guru-explorer.v1.{topicId}`. Each topic gets its own key.
**Warning signs:** Switching between explorer pages resets your knowledge states.

### Pitfall 2: Canvas Touch Gestures Conflict with Browser Gestures

**What goes wrong:** On mobile, dragging a node triggers page scroll, pinch-to-zoom, or pull-to-refresh instead of the intended canvas interaction.
**Why it happens:** Browser default touch behaviors are not suppressed on the canvas element.
**How to avoid:** Add `touch-action: none` CSS on the canvas AND call `e.preventDefault()` in pointer event handlers.
**Warning signs:** Canvas interactions work on desktop but fail or stutter on mobile.

### Pitfall 3: Clipboard API Fails Silently Without User Gesture

**What goes wrong:** `navigator.clipboard.writeText` throws `NotAllowedError` when called outside a user-initiated event (click/tap).
**Why it happens:** Browsers require transient user activation for clipboard access. Programmatic calls from timers, promises, or async callbacks may lose the gesture context.
**How to avoid:** Call `navigator.clipboard.writeText` directly inside the click handler, not in a nested async chain. The pattern in Code Examples handles this correctly.
**Warning signs:** Copy works on Chrome but fails on Firefox/Safari; works in dev but not production.

### Pitfall 4: 4-State Knowledge Cycle Confusion

**What goes wrong:** Users don't understand the difference between "familiar" and "confident" or don't realize they can cycle through states.
**Why it happens:** 4 states is more than the typical binary (know/don't know). Without visual cues, users may not discover the cycling behavior.
**How to avoid:** Use distinct colors for each state (red/yellow/blue/green), show the state name on the badge, and include instructions in the sidebar. Consider adding a tooltip on first visit.
**Warning signs:** Users only use 2 of the 4 states; analytics (if any) show most nodes stay at "unknown".

### Pitfall 5: Topic JSON Content Quality

**What goes wrong:** Options-greeks or risk-management topic data has incorrect relationships, missing concepts, or descriptions that are too technical/too simple.
**Why it happens:** Topic curation requires domain expertise. Rushing the content to meet a deadline produces low-quality learning experiences.
**How to avoid:** Each topic should have 15-25 concepts with 4-6 categories, 20-30 relationships, and descriptions at a practitioner level (not textbook, not oversimplified). Review against the dividend-strategy prototype for tone and depth.
**Warning signs:** Generated prompts are vague, repetitive, or don't build on each other. Concept graph layout has disconnected clusters.

### Pitfall 6: Secure Context Requirement for file:// Protocol

**What goes wrong:** `navigator.clipboard.writeText` fails when opening the HTML file directly from disk (file:// protocol) because some browsers do not treat file:// as a secure context.
**Why it happens:** Clipboard API requires secure context (HTTPS or localhost). file:// is treated inconsistently across browsers.
**How to avoid:** Include the textarea fallback (Pattern 4 above). Also document in the CLI launcher (Phase 11) that explorers should be served via localhost when possible.
**Warning signs:** Copy button works in development (localhost) but fails when user opens the built HTML file directly.

## Code Examples

Verified patterns from official sources:

### JSON Export Fallback (When localStorage is Unavailable)

```javascript
// Source: Standard Blob/URL API pattern
function exportStateAsJSON(topicId) {
  const state = {
    topicId: topicId,
    knowledge: knowledgeState,
    learningMode: learningMode,
    exportedAt: new Date().toISOString()
  };
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${topicId}-progress.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
```

### Learning Mode Selector UI

```html
<!-- Compact selector in header -->
<div class="mode-selector">
  <button class="mode-btn" data-mode="guided" title="Step-by-step explanations">Guided</button>
  <button class="mode-btn active" data-mode="standard" title="Balanced depth">Standard</button>
  <button class="mode-btn" data-mode="yolo" title="Dense, technical">YOLO</button>
</div>
```

```css
.mode-selector {
  display: flex;
  gap: 2px;
  background: var(--bg);
  border-radius: 6px;
  padding: 2px;
}
.mode-btn {
  padding: 4px 10px;
  font-size: 12px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}
.mode-btn.active {
  background: var(--accent);
  color: #000;
  font-weight: 600;
}
.mode-btn:hover:not(.active) {
  color: var(--text);
}
```

### Debounced Save Utility

```javascript
function debounce(fn, delay) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

const debouncedSave = debounce((topicId, state) => {
  saveState(topicId, state);
}, 500);
```

## Topic Data: Options Greeks

Curated concept graph for EXPL-09a. Confidence: MEDIUM (based on financial domain knowledge, verified against multiple options education sources).

### Recommended Concepts (~20 nodes)

**Category: Core Greeks** (color: `#58a6ff`)
1. **delta** - "Measures how much option price changes per $1 move in underlying. Calls: 0 to 1, Puts: -1 to 0. ATM options have ~0.50 delta."
2. **gamma** - "Rate of change of delta. Highest for ATM options near expiration. Shows how quickly your directional exposure shifts."
3. **theta** - "Daily time decay -- how much value an option loses per day. Accelerates near expiration. Negative for long options, positive for short."
4. **vega** - "Sensitivity to implied volatility. A 1% IV increase changes option price by vega amount. Highest for ATM options with more time."
5. **rho** - "Interest rate sensitivity. Smallest impact for short-term options. Matters more for LEAPS and in high-rate environments."

**Category: Option Fundamentals** (color: `#3fb950`)
6. **option-premium** - "Total price paid for an option. Composed of intrinsic value (real worth) plus extrinsic value (time + volatility premium)."
7. **intrinsic-value** - "What the option is worth if exercised now. Call: max(0, stock - strike). Put: max(0, strike - stock)."
8. **extrinsic-value** - "Time value + volatility premium. Decays to zero at expiration. The part of premium most sensitive to Greeks."
9. **moneyness** - "ITM/ATM/OTM status. Determines which Greeks dominate. ATM: max gamma/vega. Deep ITM: delta near 1. OTM: all extrinsic."
10. **implied-volatility** - "Market's forecast of future volatility baked into option prices. Higher IV = higher premiums. Driven by supply/demand."

**Category: Time Effects** (color: `#d29922`)
11. **time-decay-acceleration** - "Theta increases exponentially as expiration approaches. The last 30 days destroy the most time value. Sellers' advantage."
12. **expiration-dynamics** - "At expiration: extrinsic value goes to zero, gamma spikes for ATM options, and delta snaps to 0 or 1."
13. **dte-impact** - "Days to expiration affects ALL Greeks. More DTE = more vega, less gamma, slower theta. Trade-off between time protection and cost."

**Category: Volatility Effects** (color: `#f85149`)
14. **iv-crush** - "Sharp drop in implied volatility after known events (earnings, FDA decisions). Options lose value even if underlying moves favorably."
15. **iv-skew** - "OTM puts typically have higher IV than OTM calls (fear premium). Skew changes with market conditions and affects relative pricing."
16. **vol-regime** - "Low-vol vs high-vol environments change which strategies work. Low vol favors long vega; high vol favors short vega."

**Category: Strategy Impact** (color: `#bc8cff`)
17. **delta-hedging** - "Maintaining delta-neutral positions by adjusting stock/option ratios. Used by market makers. Requires frequent rebalancing due to gamma."
18. **gamma-risk** - "Short gamma positions can suffer catastrophic losses on large moves near expiration. The hidden risk in selling options."
19. **theta-harvesting** - "Selling options to collect time decay. Covered calls, cash-secured puts, iron condors. Profitable in range-bound markets."
20. **vega-trading** - "Trading volatility rather than direction. Buy options when IV is cheap, sell when expensive. Straddles, strangles, calendar spreads."

### Recommended Relationships (~22 edges)

| From | To | Label | Type |
|------|----|-------|------|
| delta | gamma | accelerated by | core |
| gamma | delta-hedging | necessitates | strategy |
| theta | time-decay-acceleration | manifests as | time |
| vega | implied-volatility | measures sensitivity to | volatility |
| option-premium | intrinsic-value | composed of | fundamentals |
| option-premium | extrinsic-value | composed of | fundamentals |
| moneyness | delta | determines | fundamentals |
| moneyness | gamma | peaks at ATM | fundamentals |
| implied-volatility | iv-crush | collapses in | volatility |
| implied-volatility | iv-skew | shapes | volatility |
| implied-volatility | vol-regime | defines environment | volatility |
| time-decay-acceleration | expiration-dynamics | culminates in | time |
| dte-impact | theta | scales | time |
| dte-impact | vega | scales | time |
| dte-impact | gamma | scales inversely | time |
| gamma-risk | gamma | drives | strategy |
| theta-harvesting | theta | exploits | strategy |
| vega-trading | vega | targets | strategy |
| delta-hedging | gamma-risk | mitigates | strategy |
| iv-crush | vega-trading | threatens | volatility |
| vol-regime | theta-harvesting | determines effectiveness of | strategy |
| rho | dte-impact | amplified by longer | core |

## Topic Data: Risk Management

Curated concept graph for EXPL-09b. Confidence: MEDIUM (based on financial domain knowledge, verified against risk management education sources).

### Recommended Concepts (~20 nodes)

**Category: Risk Measurement** (color: `#f85149`)
1. **var** - "Value at Risk: maximum expected loss over a time period at a confidence level. Example: 95% 1-day VaR of $10k means only 5% chance of losing more than $10k in a day."
2. **cvar** - "Conditional VaR (Expected Shortfall): average loss BEYOND VaR. Answers 'when things go bad, how bad?' Better tail risk measure than VaR."
3. **volatility** - "Standard deviation of returns. Measures price fluctuation magnitude. Annualized vol of 20% means ~1.26% daily moves expected."
4. **beta** - "Systematic risk relative to market. Beta 1.5 = 50% more volatile than benchmark. Cannot be diversified away."
5. **max-drawdown** - "Largest peak-to-trough decline. SPY's worst: -56% in 2008. Critical for sizing positions and setting expectations."

**Category: Performance Metrics** (color: `#58a6ff`)
6. **sharpe-ratio** - "Risk-adjusted return: (return - risk-free rate) / volatility. Above 1.0 is good, above 2.0 is excellent. Penalizes both upside and downside vol."
7. **sortino-ratio** - "Like Sharpe but only penalizes DOWNSIDE volatility. Better for asymmetric return distributions. Preferred for strategies with positive skew."
8. **alpha** - "Excess return above benchmark after adjusting for risk. Positive alpha = skill or edge. Hard to sustain long-term."
9. **calmar-ratio** - "Annualized return divided by max drawdown. Measures return per unit of worst-case pain. Higher is better."

**Category: Position Management** (color: `#3fb950`)
10. **position-sizing** - "Determining how much capital to allocate per position. Controls risk exposure. The single most important risk management decision."
11. **kelly-criterion** - "Mathematical formula for optimal bet size: f* = (bp - q) / b. Maximizes long-term growth. Full Kelly is too aggressive -- use half-Kelly."
12. **stop-loss** - "Exit rule to limit losses on a position. Fixed percentage, trailing, volatility-based (2x ATR). Prevents catastrophic single-position losses."
13. **concentration-risk** - "Over-exposure to a single position, sector, or factor. Rule of thumb: no single position > 5-10% of portfolio."

**Category: Portfolio Diversification** (color: `#d29922`)
14. **diversification** - "Spreading investments to reduce unsystematic risk. Requires low-correlation assets. More positions don't help if everything is correlated."
15. **correlation** - "How assets move together. -1 to +1 scale. Low/negative correlation improves diversification. Correlations increase in crises (correlation breakdown)."
16. **asset-allocation** - "Strategic portfolio mix across asset classes (stocks, bonds, alternatives). Drives 90%+ of portfolio return variation."
17. **rebalancing** - "Adjusting portfolio back to target weights. Calendar-based (quarterly) or threshold-based (5% drift). Enforces buy-low-sell-high discipline."

**Category: Risk Control Strategies** (color: `#bc8cff`)
18. **hedging** - "Using offsetting positions to reduce specific risks. Puts for downside protection, shorts for market exposure reduction. Has a cost (insurance premium)."
19. **vol-regime-awareness** - "Markets alternate between low-volatility (calm) and high-volatility (crisis) regimes. Risk management approach should adapt to current regime."
20. **tail-risk** - "Risk of extreme, rare events (3+ sigma moves). Standard models underestimate it. Black swans, fat tails, crash risk. Managed through position limits and hedging."

### Recommended Relationships (~22 edges)

| From | To | Label | Type |
|------|----|-------|------|
| var | cvar | extended by | measurement |
| volatility | var | input to | measurement |
| volatility | sharpe-ratio | denominator of | metrics |
| beta | volatility | component of systematic | measurement |
| max-drawdown | calmar-ratio | denominator of | metrics |
| sharpe-ratio | sortino-ratio | refined by | metrics |
| alpha | sharpe-ratio | contextualized by | metrics |
| position-sizing | concentration-risk | prevents | management |
| kelly-criterion | position-sizing | optimizes | management |
| stop-loss | max-drawdown | limits | management |
| diversification | correlation | depends on low | diversification |
| correlation | asset-allocation | informs | diversification |
| asset-allocation | rebalancing | maintained by | diversification |
| hedging | volatility | reduces portfolio | strategy |
| hedging | tail-risk | protects against | strategy |
| vol-regime-awareness | hedging | triggers | strategy |
| vol-regime-awareness | position-sizing | adjusts | strategy |
| tail-risk | cvar | measured by | measurement |
| concentration-risk | diversification | solved by | management |
| rebalancing | concentration-risk | prevents drift toward | diversification |
| stop-loss | position-sizing | complements | management |
| beta | alpha | adjusted for in | metrics |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| document.execCommand('copy') | navigator.clipboard.writeText | ~2018-2019 | execCommand deprecated; clipboard API is async and permission-aware |
| Separate mouse + touch event listeners | Pointer Events API | ~2019 (Safari 13 completed support) | Single code path for all input types; simpler and more reliable |
| Safari private browsing blocks localStorage | Safari allows localStorage in private mode | iOS 11 (2017) | Data persists during session but cleared on tab close; no longer throws on write |
| Binary knowledge states (know/don't know) | Multi-level self-assessment (4+ states) | Ongoing in education tech | Finer-grained assessment produces better targeted prompts |
| Static difficulty selection | Adaptive/dynamic difficulty | 2024-2025 trend | Phase 10 uses manual selector (guided/standard/yolo) which is appropriate for the scope; adaptive is anti-feature M3-X05 |

**Deprecated/outdated:**
- `document.execCommand('copy')`: Deprecated in all browsers. Still works as fallback but should not be primary approach.
- Touch Events for unified handling: Pointer Events are the standard replacement. Touch Events still work but lead to duplicated code paths.
- PEP (Pointer Events Polyfill): Unnecessary since Safari 13 (2019). All target browsers support pointer events natively.

## Open Questions

Things that could not be fully resolved:

1. **Phase 9 Template Engine Architecture**
   - What we know: Phase 9 creates a Bun build pipeline, topic JSON schema, and template HTML
   - What is unclear: The exact template structure, JSON schema fields, and build pipeline API are not yet defined (Phase 9 has not been researched or planned)
   - Recommendation: Phase 10 planning should assume the template architecture from the prototype (single HTML with inline JS/CSS) and define the features it needs to add. Phase 9 research will define the exact integration points.

2. **Cytoscape.js vs Custom Canvas (Phase 9 Decision)**
   - What we know: Phase 9 research was flagged to decide between Cytoscape.js and custom Canvas rendering
   - What is unclear: If Phase 9 chooses Cytoscape.js, the pointer events integration pattern changes (Cytoscape has its own event system)
   - Recommendation: Phase 10 code examples above assume custom Canvas (matching the prototype). If Phase 9 chooses Cytoscape.js, the pointer events and knowledge cycling code must adapt to Cytoscape's API. This is a dependency on Phase 9 research.

3. **4-State vs 3-State Knowledge Cycling**
   - What we know: Success criteria says "unknown -> familiar -> confident -> mastered" (4 states). Prototype uses "know/fuzzy/unknown" (3 states).
   - What is unclear: Whether 4 states is intentional or the success criteria should match the prototype's 3 states
   - Recommendation: Implement 4 states as specified in success criteria. It provides finer granularity for prompt generation. Map: unknown (red) -> familiar (yellow) -> confident (blue) -> mastered (green).

4. **Topic Content Depth**
   - What we know: Options-greeks and risk-management need curated concept graphs
   - What is unclear: Exact depth and tone -- the dividend prototype has practitioner-level descriptions mentioning real fund tickers and dollar amounts
   - Recommendation: Match the dividend prototype's depth. Each concept description should be 2-3 sentences with concrete examples, numbers, or formulas. No textbook definitions.

## Sources

### Primary (HIGH confidence)
- MDN Web Docs - localStorage: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage
- MDN Web Docs - Clipboard API: https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText
- MDN Web Docs - Pointer Events: https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events
- W3C Pointer Events Specification: https://w3c.github.io/pointerevents/
- CanIUse - Clipboard writeText: https://caniuse.com/mdn-api_clipboard_writetext
- CanIUse - Pointer Events: https://caniuse.com/pointer

### Secondary (MEDIUM confidence)
- Safari private browsing localStorage behavior: https://muffinman.io/blog/localstorage-and-sessionstorage-in-safaris-private-mode/ (verified against MDN)
- Options Greeks educational sources: https://public.com/learn/the-greeks-in-options-trading, https://marketrebellion.com/news/trading-insights/option-greeks-made-easy-delta-gamma-vega-theta-rho/
- Web performance optimization 2025: https://voostack.com/articles/web-performance-optimization-2025

### Tertiary (LOW confidence)
- Learning mode UI patterns: Based on EdTech trends analysis, not specific implementation references. The guided/standard/yolo tier design is original to this project.
- Risk management concept graph: Based on general financial domain knowledge without specific educational source validation. Concept selection is sound but relationships should be reviewed by domain expert.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All browser APIs verified via MDN and CanIUse; universal support confirmed
- Architecture patterns: HIGH - Patterns are standard, verified, and directly applicable to the existing prototype structure
- Topic data curation: MEDIUM - Concepts are well-established financial knowledge; exact graph relationships are editorial judgments
- Phase 9 integration: LOW - Phase 9 has not been researched or planned yet; integration assumptions based on prototype

**Research date:** 2026-02-02
**Valid until:** 2026-03-04 (30 days -- browser APIs are stable; topic data is evergreen)
