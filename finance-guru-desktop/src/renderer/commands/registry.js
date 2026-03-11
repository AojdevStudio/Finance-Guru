const COMMANDS = {
  analysis: [
    {
      id: 'total-return',
      label: 'Total Return',
      icon: '\u{1F4C8}',
      description: 'Price + dividend return with DRIP analysis',
      command: 'analysis.total_return_cli',
      args: [
        { name: 'tickers', type: 'ticker-multi', required: true, placeholder: 'SCHD, VYM, JEPI' },
        { name: '--days', type: 'number', default: 252, label: 'Days' },
        { name: '--realtime', type: 'toggle', default: false, label: 'Real-time pricing' },
        { name: '--force', type: 'toggle', default: false, label: 'Force (ignore warnings)' }
      ],
      outputType: 'chart+table'
    },
    {
      id: 'risk-metrics',
      label: 'Risk Metrics',
      icon: '\u{1F4C9}',
      description: 'VaR, Sharpe, Sortino, drawdown, volatility',
      command: 'analysis.risk_metrics_cli',
      args: [
        { name: 'ticker', type: 'ticker', required: true, placeholder: 'TSLA' },
        { name: '--days', type: 'number', default: 252, label: 'Days' },
        { name: '--benchmark', type: 'ticker', default: '', placeholder: 'SPY', label: 'Benchmark' },
        { name: '--confidence', type: 'select', options: ['0.95', '0.99'], default: '0.95', label: 'Confidence' },
        { name: '--var-method', type: 'select', options: ['historical', 'parametric'], default: 'historical', label: 'VaR Method' },
        { name: '--realtime', type: 'toggle', default: false, label: 'Real-time pricing' }
      ],
      outputType: 'gauges'
    },
    {
      id: 'correlation',
      label: 'Correlation',
      icon: '\u{1F517}',
      description: 'Cross-correlation matrix between tickers',
      command: 'analysis.correlation_cli',
      args: [
        { name: 'tickers', type: 'ticker-multi', required: true, min: 2, placeholder: 'TSLA, PLTR, NVDA' },
        { name: '--days', type: 'number', default: 90, label: 'Days' },
        { name: '--method', type: 'select', options: ['pearson', 'spearman'], default: 'pearson', label: 'Method' }
      ],
      outputType: 'heatmap'
    },
    {
      id: 'options-chain',
      label: 'Options Chain',
      icon: '\u{26D3}',
      description: 'Scan options chains with OTM filters',
      command: 'analysis.options_chain_cli',
      args: [
        { name: 'ticker', type: 'ticker', required: true, placeholder: 'QQQ' },
        { name: '--type', type: 'select', options: ['put', 'call'], default: 'put', label: 'Type' },
        { name: '--otm-min', type: 'number', default: 10, label: 'Min OTM %' },
        { name: '--otm-max', type: 'number', default: 20, label: 'Max OTM %' },
        { name: '--days-min', type: 'number', default: 30, label: 'Min DTE' },
        { name: '--days-max', type: 'number', default: 90, label: 'Max DTE' }
      ],
      outputType: 'table'
    }
  ],

  skills: [
    { id: 'quant-analysis', label: 'Quant Analysis', icon: '\u{1F9EE}', skill: 'fin-guru-quant-analysis', description: 'Risk metrics, momentum, volatility, correlation, backtesting' },
    { id: 'research', label: 'Market Research', icon: '\u{1F52C}', skill: 'fin-guru-research', description: 'Intelligence, sector, competitive research workflows' },
    { id: 'orchestrator-chat', label: 'Finance Orchestrator', icon: '\u{1F3AF}', skill: 'finance-orchestrator', description: 'Start a chat routed through the master orchestrator' }
  ],

  agents: [
    { id: 'orchestrator', label: 'Cassandra Holt', icon: '\u{1F3AF}', agent: 'finance-orchestrator', description: 'Master orchestrator — routes to all specialists' }
  ]
};

const ALLOWED_ANALYSIS_COMMANDS = new Set(COMMANDS.analysis.map(cmd => cmd.command));

module.exports = { COMMANDS, ALLOWED_ANALYSIS_COMMANDS };
