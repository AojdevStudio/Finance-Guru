const { describe, test, expect, mock, beforeEach } = require('bun:test');

// Mock Plotly before any renderer modules are loaded
mock.module('plotly.js-dist-min', () => ({
  newPlot: mock(() => {})
}));

const Plotly = require('plotly.js-dist-min');

const totalReturnFixture = require('../../fixtures/analysis/total-return.json');
const riskMetricsFixture = require('../../fixtures/analysis/risk-metrics.json');
const correlationFixture = require('../../fixtures/analysis/correlation.json');
const optionsChainFixture = require('../../fixtures/analysis/options-chain.json');

const { renderGauges } = require('../../../src/renderer/ui/renderers/GaugeRenderer');
const { renderTable } = require('../../../src/renderer/ui/renderers/TableRenderer');
const { renderByType, renderReturnChart } = require('../../../src/renderer/ui/renderers/index');

function makeEl() {
  const el = document.createElement('div');
  document.body.appendChild(el);
  return el;
}

// ── GaugeRenderer ─────────────────────────────────────────────────────────────

describe('GaugeRenderer', () => {
  test('renders gauge HTML for each known metric from risk_metrics fixture', () => {
    const el = makeEl();
    renderGauges(el, riskMetricsFixture);

    const gauges = el.querySelectorAll('.risk-gauge');
    // Fixture has: sharpe_ratio, sortino_ratio, max_drawdown, calmar_ratio,
    //              annual_volatility, beta, alpha, var_95
    expect(gauges.length).toBeGreaterThanOrEqual(7);

    // Check Sharpe is present
    const labels = [...el.querySelectorAll('.risk-label')].map(n => n.textContent.trim());
    expect(labels).toContain('Sharpe Ratio');
    expect(labels).toContain('Volatility');
    expect(labels).toContain('Beta');
  });

  test('renders bar fill elements with data-bar-width attribute', () => {
    const el = makeEl();
    renderGauges(el, riskMetricsFixture);

    const bars = el.querySelectorAll('[data-bar-width]');
    expect(bars.length).toBeGreaterThan(0);

    bars.forEach(bar => {
      const w = bar.dataset.barWidth;
      expect(w).toMatch(/^\d+(\.\d+)?%$/);
    });
  });

  test('renders empty state when no known metrics present', () => {
    const el = makeEl();
    renderGauges(el, { ticker: 'FAKE', calculation_date: '2026-01-01' });

    expect(el.querySelector('.empty-state')).toBeTruthy();
    expect(el.querySelector('.risk-gauge')).toBeFalsy();
  });
});

// ── TableRenderer ─────────────────────────────────────────────────────────────

describe('TableRenderer — options chain fixture', () => {
  test('renders table rows from options_chain contracts array', () => {
    const el = makeEl();
    renderTable(el, optionsChainFixture);

    const table = el.querySelector('table');
    expect(table).toBeTruthy();

    const rows = el.querySelectorAll('tbody tr');
    // The fixture has 77 contracts
    expect(rows.length).toBe(optionsChainFixture.contracts.length);
  });

  test('contract_symbol column renders as text (not mangled as number)', () => {
    const el = makeEl();
    renderTable(el, optionsChainFixture);

    const firstRow = el.querySelector('tbody tr');
    const cells = [...firstRow.querySelectorAll('td')];
    const headers = [...el.querySelectorAll('thead th')].map(h => h.textContent.trim());
    const symbolIdx = headers.indexOf('contract_symbol');

    expect(symbolIdx).toBeGreaterThanOrEqual(0);
    // Should be the actual symbol string, not NaN or a number
    const symbolText = cells[symbolIdx].textContent.trim();
    expect(symbolText).toMatch(/^QQQ/);
  });

  test('strike and numeric fields are formatted as numbers', () => {
    const el = makeEl();
    renderTable(el, optionsChainFixture);

    const headers = [...el.querySelectorAll('thead th')];
    const strikeHeader = headers.find(h => h.textContent.trim() === 'strike');
    expect(strikeHeader).toBeTruthy();
    expect(strikeHeader.classList.contains('num')).toBe(true);
  });
});

describe('TableRenderer — total return fixture', () => {
  test('renders period_breakdown rows from total_return fixture', () => {
    const el = makeEl();
    // The total_return fixture has total_return_analysis array
    // TableRenderer.normalizeToRows will find the first array key
    renderTable(el, totalReturnFixture);

    const rows = el.querySelectorAll('tbody tr');
    // Should render the total_return_analysis array (1 row per ticker)
    expect(rows.length).toBeGreaterThan(0);
  });
});

// ── renderByType routing ───────────────────────────────────────────────────────

describe('renderByType routing', () => {
  beforeEach(() => {
    Plotly.newPlot.mockClear();
  });

  test('chart+table routes to renderReturnChart and calls Plotly.newPlot', () => {
    const el = makeEl();
    renderByType('chart+table', totalReturnFixture, el);

    expect(Plotly.newPlot).toHaveBeenCalledTimes(1);
    const [elArg, traces, layout] = Plotly.newPlot.mock.calls[0];
    expect(traces[0].type).toBe('bar');
    expect(layout.title).toContain('SCHD');
  });

  test('heatmap routes to renderCorrelationHeatmap and calls Plotly.newPlot with heatmap type', () => {
    const el = makeEl();
    renderByType('heatmap', correlationFixture, el);

    expect(Plotly.newPlot).toHaveBeenCalledTimes(1);
    const [elArg, traces] = Plotly.newPlot.mock.calls[0];
    expect(traces[0].type).toBe('heatmap');
  });

  test('heatmap uses nested correlation_matrix.correlation_matrix contract', () => {
    const el = makeEl();
    renderByType('heatmap', correlationFixture, el);

    const [elArg, traces] = Plotly.newPlot.mock.calls[0];
    const labels = traces[0].x;
    expect(labels).toContain('TSLA');
    expect(labels).toContain('PLTR');
    expect(labels).toContain('NVDA');
    // Diagonal should be 1
    const tslaIdx = labels.indexOf('TSLA');
    expect(traces[0].z[tslaIdx][tslaIdx]).toBe(1.0);
  });

  test('gauges routes to renderGauges and renders gauge HTML', () => {
    const el = makeEl();
    renderByType('gauges', riskMetricsFixture, el);

    expect(el.querySelectorAll('.risk-gauge').length).toBeGreaterThan(0);
    expect(Plotly.newPlot).not.toHaveBeenCalled();
  });

  test('table routes to renderTable and renders a table element', () => {
    const el = makeEl();
    renderByType('table', optionsChainFixture, el);

    expect(el.querySelector('table')).toBeTruthy();
    expect(Plotly.newPlot).not.toHaveBeenCalled();
  });

  test('unknown outputType falls back to renderGenericChart (pre-formatted JSON)', () => {
    const el = makeEl();
    renderByType('unknown-type', { foo: 'bar' }, el);

    expect(el.querySelector('pre')).toBeTruthy();
    expect(Plotly.newPlot).not.toHaveBeenCalled();
  });
});

// ── Malformed payload handling ────────────────────────────────────────────────

describe('malformed payload handling', () => {
  test('renderCorrelationHeatmap shows error-state on missing matrix', () => {
    const { renderCorrelationHeatmap } = require('../../../src/renderer/ui/renderers/ChartRenderer');
    const el = makeEl();
    renderCorrelationHeatmap(el, { bad: 'data' });

    expect(el.querySelector('.error-state')).toBeTruthy();
    expect(Plotly.newPlot).not.toHaveBeenCalled();
  });

  test('renderGauges shows empty-state on empty object', () => {
    const el = makeEl();
    renderGauges(el, {});
    expect(el.querySelector('.empty-state')).toBeTruthy();
  });

  test('renderTable shows empty-state on empty array', () => {
    const el = makeEl();
    renderTable(el, []);
    expect(el.querySelector('.empty-state')).toBeTruthy();
  });
});
