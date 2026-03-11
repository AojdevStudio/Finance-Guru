const { ipcMain } = require('electron');
const { validateRuntime } = require('../config/validateRuntime');

// Cache the runtime result so it's consistent and available for both
// the push event (did-finish-load) and the pull IPC (app-runtime-status)
let cachedRuntimeResult = null;

function getCachedRuntimeResult() {
  if (!cachedRuntimeResult) {
    cachedRuntimeResult = validateRuntime();
  }
  return cachedRuntimeResult;
}

function registerAllHandlers() {
  // ── App status (always available) ──
  ipcMain.handle('app-runtime-status', async () => {
    return getCachedRuntimeResult();
  });

  // Populated by analysis.ipc.js, csv.ipc.js, chat.ipc.js in subsequent tasks
}

module.exports = { registerAllHandlers, getCachedRuntimeResult };
