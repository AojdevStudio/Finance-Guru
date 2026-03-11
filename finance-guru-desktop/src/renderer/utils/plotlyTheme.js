function getPlotlyLayout(overrides = {}) {
  const style = getComputedStyle(document.body);
  const get = (v) => style.getPropertyValue(v).trim();

  return {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {
      color: get('--text-primary') || '#e0e0e0',
      family: 'SF Mono, Fira Code, monospace',
      size: 12
    },
    xaxis: {
      gridcolor: get('--border-color') || '#2d2d2d',
      zerolinecolor: get('--text-muted') || '#555',
      tickfont: { color: get('--text-secondary') || '#888' }
    },
    yaxis: {
      gridcolor: get('--border-color') || '#2d2d2d',
      zerolinecolor: get('--text-muted') || '#555',
      tickfont: { color: get('--text-secondary') || '#888' }
    },
    margin: { t: 40, b: 40, l: 60, r: 20 },
    ...overrides
  };
}

const CHART_COLORS = {
  profit: '#22c55e',
  loss: '#ef4444',
  accent: '#22c55e',
  secondary: '#3b82f6',
  tertiary: '#f59e0b',
  muted: '#555'
};

module.exports = { getPlotlyLayout, CHART_COLORS };
