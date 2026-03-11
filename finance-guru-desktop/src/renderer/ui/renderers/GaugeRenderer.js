function renderGauges(el, data) {
  const metrics = extractMetrics(data);
  if (!metrics.length) {
    el.innerHTML = '<p class="empty-state">No metrics to display.</p>';
    return;
  }

  el.innerHTML = metrics.map(m => {
    const pct = Math.min((Math.abs(m.value) / m.max) * 100, 100);
    const color = pct > 70 ? 'var(--danger)' : pct > 40 ? 'var(--warning)' : 'var(--success)';

    return `
      <div class="risk-gauge">
        <div class="risk-label">${m.label}</div>
        <div class="risk-bar-track">
          <div class="risk-bar-fill" data-bar-width="${pct}%"
               style="width: 0; background: ${color}"></div>
        </div>
        <div class="risk-value">${m.format(m.value)}</div>
      </div>`;
  }).join('');

  setTimeout(() => {
    el.querySelectorAll('[data-bar-width]').forEach(bar => {
      bar.style.transition = 'width 500ms cubic-bezier(0.22, 1, 0.36, 1)';
      bar.style.width = bar.dataset.barWidth;
    });
  }, 300);
}

function extractMetrics(data) {
  const pct = v => `${(v * 100).toFixed(2)}%`;
  const num = v => v.toFixed(3);

  const known = [
    { key: 'sharpe_ratio', label: 'Sharpe Ratio', max: 3, format: num },
    { key: 'sortino_ratio', label: 'Sortino Ratio', max: 3, format: num },
    { key: 'max_drawdown', label: 'Max Drawdown', max: 0.5, format: pct },
    { key: 'var_95', label: 'VaR 95%', max: 0.1, format: pct },
    { key: 'var_99', label: 'VaR 99%', max: 0.15, format: pct },
    { key: 'annual_volatility', label: 'Volatility', max: 0.6, format: pct },
    { key: 'beta', label: 'Beta', max: 2, format: num },
    { key: 'alpha', label: 'Alpha', max: 0.3, format: pct },
    { key: 'calmar_ratio', label: 'Calmar Ratio', max: 3, format: num }
  ];

  return known
    .filter(m => data[m.key] !== undefined && data[m.key] !== null)
    .map(m => ({ ...m, value: data[m.key] }));
}

module.exports = { renderGauges };
