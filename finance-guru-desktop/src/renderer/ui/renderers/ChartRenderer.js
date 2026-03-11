const Plotly = require('plotly.js-dist-min');
const { getPlotlyLayout, CHART_COLORS } = require('../../utils/plotlyTheme');

function renderReturnChart(el, data) {
  const results = data.total_return_analysis || [data];
  if (results.length === 1) {
    renderSingleReturn(el, results[0]);
  } else {
    renderMultiReturn(el, results);
  }
}

function renderSingleReturn(el, result) {
  const labels = ['Price Return', 'Dividend Return', 'Total Return', 'DRIP Return'];
  const values = [
    result.price_return * 100,
    result.dividend_return * 100,
    result.total_return * 100,
    (result.drip_total_return || result.total_return) * 100
  ];

  const trace = {
    x: labels,
    y: values,
    type: 'bar',
    marker: {
      color: [CHART_COLORS.secondary, CHART_COLORS.accent, CHART_COLORS.tertiary, CHART_COLORS.profit]
    },
    text: values.map(v => `${v.toFixed(2)}%`),
    textposition: 'outside'
  };

  Plotly.newPlot(el, [trace], getPlotlyLayout({
    title: `${result.ticker} — Total Return Breakdown`
  }), { responsive: true, displaylogo: false });
}

function renderMultiReturn(el, results) {
  const traces = results.map((r, i) => ({
    name: r.ticker,
    x: ['Price', 'Dividend', 'Total'],
    y: [r.price_return * 100, r.dividend_return * 100, r.total_return * 100],
    type: 'bar'
  }));

  Plotly.newPlot(el, traces, getPlotlyLayout({
    title: 'Total Return Comparison',
    barmode: 'group'
  }), { responsive: true, displaylogo: false });
}

function renderGenericChart(el, data, title) {
  el.innerHTML = `<pre style="color: var(--text-primary); padding: 16px; overflow: auto; font-size: var(--font-sm);">${JSON.stringify(data, null, 2)}</pre>`;
}

function renderCorrelationHeatmap(el, data) {
  const matrix = data.correlation_matrix?.correlation_matrix || data.matrix;
  const labels = data.correlation_matrix?.tickers || data.tickers || Object.keys(matrix || {});
  if (!matrix || !labels.length) {
    el.innerHTML = '<div class="error-state">Unsupported correlation payload.</div>';
    return;
  }

  const z = labels.map(row => labels.map(col => matrix[row]?.[col] ?? 0));
  Plotly.newPlot(el, [{
    z,
    x: labels,
    y: labels,
    type: 'heatmap',
    zmin: -1,
    zmax: 1,
    colorscale: 'RdBu'
  }], getPlotlyLayout({ title: 'Correlation Matrix' }), { responsive: true, displaylogo: false });
}

module.exports = { renderReturnChart, renderGenericChart, renderCorrelationHeatmap };
