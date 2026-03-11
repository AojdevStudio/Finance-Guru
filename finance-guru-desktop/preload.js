const { contextBridge, ipcRenderer } = require('electron');

// ── Helper: create listener that returns unsubscribe function ──
function createListener(channel) {
  return (callback) => {
    const subscription = (event, ...args) => callback(...args);
    ipcRenderer.on(channel, subscription);
    return () => ipcRenderer.removeListener(channel, subscription);
  };
}

// ── Expose protected API ──
contextBridge.exposeInMainWorld('electron_api', {
  app: {
    getRuntimeStatus: () => ipcRenderer.invoke('app-runtime-status'),
    onRuntimeStatus: createListener('runtime-status')
  },

  // ── Analysis (direct Python execution) ──
  analysis: {
    run: (params) => ipcRenderer.invoke('analysis-run', params),
    onProgress: createListener('analysis-progress')
  },

  // ── CSV ──
  csv: {
    openAndRead: (params) => ipcRenderer.invoke('csv-open-and-read', params)
  },

  // ── Chat (Claude Agent SDK) ──
  chat: {
    start: (params) => ipcRenderer.invoke('chat-start', params),
    send: (params) => ipcRenderer.invoke('chat-send', params),
    close: (params) => ipcRenderer.invoke('chat-close', params),
    interrupt: (params) => ipcRenderer.send('chat-interrupt', params),
    onMessage: createListener('chat-message'),
    onDone: createListener('chat-done'),
    onError: createListener('chat-error')
  }
});
