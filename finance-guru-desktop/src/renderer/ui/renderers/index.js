const { renderReturnChart, renderGenericChart, renderCorrelationHeatmap } = require('./ChartRenderer');
const { renderGauges } = require('./GaugeRenderer');
const { renderTable } = require('./TableRenderer');

function renderByType(outputType, data, el) {
  switch (outputType) {
    case 'chart+table':
      renderReturnChart(el, data);
      break;
    case 'gauges':
      renderGauges(el, data);
      break;
    case 'heatmap':
      renderCorrelationHeatmap(el, data);
      break;
    case 'table':
      renderTable(el, data);
      break;
    default:
      renderGenericChart(el, data, 'Result');
  }
}

module.exports = { renderByType, renderReturnChart, renderGauges, renderTable };
