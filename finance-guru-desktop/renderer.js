// Finance Guru Desktop — Renderer Entry Point

const api = window.electron_api;

const { portfolioState } = require('./src/renderer/state/portfolio.state');
const { createCommandPalette } = require('./src/renderer/ui/CommandPalette');
const { showCommandArgs, closeModal } = require('./src/renderer/ui/Modal');
const { renderByType, renderTable } = require('./src/renderer/ui/renderers');
const { parseCsv } = require('./src/renderer/utils/parseCsv');

// ── Pause animations when window hidden ──
document.addEventListener('visibilitychange', () => {
  document.body.classList.toggle('background-paused', document.hidden);
});

// ── Tab switching ──
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(`panel-${tab.dataset.panel}`).classList.add('active');
  });
});

function switchToPanel(panelId) {
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.panel === panelId);
  });
  document.querySelectorAll('.panel').forEach(p => {
    p.classList.toggle('active', p.id === `panel-${panelId}`);
  });
}

// ── Status bar time ──
function updateTime() {
  const now = new Date();
  document.getElementById('status-time').textContent =
    now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }) +
    ' ' + now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}
updateTime();
setInterval(updateTime, 60000);

// ── Runtime status preflight ──
// Stored on the module-level object so later code can read the resolved value.
// Do NOT export runtimeStatus as a primitive — it would capture the initial null.
const appState = { runtimeStatus: null };

// ── ChatView placeholder ──
// Actual ChatView wiring is Task 17. Declare here so skill/agent callbacks don't crash.
let chatView = null;

// ── Loading skeleton helpers ──
function showSkeleton(el) {
  el.innerHTML = `
    <div class="skeleton-block"></div>
    <div class="skeleton-block" style="width: 70%"></div>
    <div class="skeleton-block" style="width: 85%"></div>
  `;
}

function clearSkeleton(el) {
  el.innerHTML = '';
}

// ── Run analysis command ──
async function runCommand(cmd, args) {
  const outputEl = document.getElementById('analysis-output');
  if (!outputEl) return;

  switchToPanel('analysis');
  showSkeleton(outputEl);

  let commandPaletteHandle = null;
  try {
    const result = await api.analysis.run({ command: cmd.command, args });

    if (!result.success) {
      outputEl.innerHTML = `
        <div class="error-state">
          <strong>Error:</strong> ${result.error || 'Analysis failed'}
        </div>`;
      return;
    }

    clearSkeleton(outputEl);
    renderByType(cmd.outputType, result.data, outputEl);
  } catch (err) {
    outputEl.innerHTML = `
      <div class="error-state">
        <strong>Unexpected error:</strong> ${err.message}
      </div>`;
  }
}

// ── Command palette wiring ──
function initCommandPalette() {
  const containerEl = document.getElementById('command-palette');
  if (!containerEl) return;

  createCommandPalette(containerEl, {
    onCommandClick(cmd) {
      if (cmd.args && cmd.args.length > 0) {
        showCommandArgs(cmd, (args) => runCommand(cmd, args));
      } else {
        runCommand(cmd, []);
      }
    },
    onSkillClick(skill) {
      // Skill invocation will route through chatView in Task 17
      if (chatView) {
        chatView.sendMessage(`/skill ${skill.skill}`);
      }
    },
    onAgentClick(agent) {
      // Agent invocation will route through chatView in Task 17
      if (chatView) {
        chatView.sendMessage(`/agent ${agent.agent}`);
      }
    }
  });
}

// ── CSV load button wiring ──
function initCsvLoader() {
  const loadBtn = document.getElementById('csv-load-btn');
  if (!loadBtn) return;

  loadBtn.addEventListener('click', async () => {
    try {
      const result = await api.csv.load();
      if (!result || !result.success) return;

      const rows = parseCsv(result.content);
      portfolioState.setHoldings(rows);

      const outputEl = document.getElementById('csv-output');
      if (outputEl) {
        renderTable(outputEl, rows);
      }
    } catch (err) {
      const outputEl = document.getElementById('csv-output');
      if (outputEl) {
        outputEl.innerHTML = `<div class="error-state">CSV load failed: ${err.message}</div>`;
      }
    }
  });
}

async function init() {
  try {
    appState.runtimeStatus = await api.app.getRuntimeStatus();
  } catch (e) {
    document.getElementById('status-text').textContent = 'Failed to check runtime status';
    return;
  }

  const rs = appState.runtimeStatus;
  if (rs.warnings && rs.warnings.length > 0) {
    document.getElementById('status-text').textContent =
      `Warning: ${rs.warnings[0]}`;
  } else {
    document.getElementById('status-text').textContent = 'Ready';
  }

  // If Claude auth is unavailable, show warning in chat panel
  if (!rs.claudeAuth?.ok) {
    const chatContainer = document.getElementById('chat-container');
    chatContainer.innerHTML = `
      <div class="chat-auth-warning">
        <p>Claude authentication not available.</p>
        <p>Run <code>claude</code> in your terminal to authenticate, or set <code>ANTHROPIC_API_KEY</code>.</p>
        <p>Analysis and CSV tools remain usable.</p>
      </div>`;
  }

  initCommandPalette();
  initCsvLoader();
}

init();

// ── Modal close wiring ──
document.getElementById('modal-close')?.addEventListener('click', () => {
  closeModal();
});
document.getElementById('modal-overlay')?.addEventListener('click', (e) => {
  if (e.target === e.currentTarget) {
    closeModal();
  }
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeModal();
  }
});

// Exports for use by later modules (command palette, renderers, chat).
// appState is a mutable object — readers always see the latest runtimeStatus.
module.exports = { switchToPanel, appState };
