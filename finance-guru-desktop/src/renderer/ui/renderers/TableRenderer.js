function renderTable(el, data) {
  const rows = normalizeToRows(data);
  if (!rows.length) {
    el.innerHTML = '<p class="empty-state">No data to display.</p>';
    return;
  }

  const headers = Object.keys(rows[0]);

  el.innerHTML = `
    <table>
      <thead>
        <tr>${headers.map(h => `<th class="${isNumericCol(rows, h) ? 'num' : ''}">${h}</th>`).join('')}</tr>
      </thead>
      <tbody>
        ${rows.map(row => `
          <tr>${headers.map(h => {
            const val = row[h];
            const cls = isNumericCol(rows, h) ? 'num' : '';
            return `<td class="${cls}">${formatCell(val)}</td>`;
          }).join('')}</tr>
        `).join('')}
      </tbody>
    </table>`;
}

function normalizeToRows(data) {
  if (Array.isArray(data)) return data;
  // Prefer well-known named array keys before falling back to first array found
  for (const preferred of ['rows', 'data', 'items', 'contracts', 'options', 'results']) {
    if (Array.isArray(data[preferred]) && data[preferred].length > 0) {
      return data[preferred];
    }
  }
  for (const key of Object.keys(data)) {
    if (Array.isArray(data[key]) && data[key].length > 0) return data[key];
  }
  return Object.entries(data).map(([k, v]) => ({ field: k, value: v }));
}

function isNumericCol(rows, key) {
  return rows.slice(0, 5).every(r => typeof r[key] === 'number' || !isNaN(Number(r[key])));
}

function formatCell(val) {
  if (val === null || val === undefined) return '-';
  if (typeof val === 'number') {
    return val.toLocaleString(undefined, { maximumFractionDigits: 4 });
  }
  return String(val);
}

module.exports = { renderTable };
