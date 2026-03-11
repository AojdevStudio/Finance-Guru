const { app, BrowserWindow } = require('electron');
const path = require('path');

// ── PATH fix for macOS (apps launched from Dock have minimal PATH) ──
if (process.platform !== 'win32') {
  const { execFile } = require('child_process');
  const shell = process.env.SHELL || '/bin/zsh';
  execFile(shell, ['-lc', 'echo $PATH'], {
    encoding: 'utf8',
    timeout: 5000,
  }, (err, stdout) => {
    if (!err && stdout) {
      const shellPath = stdout.trim();
      if (shellPath) process.env.PATH = shellPath;
    }
  });
}

// ── Dev mode ──
const isDev = process.argv.includes('--dev');

// ── Single instance lock ──
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  console.log('Another instance is already running.');
  app.quit();
} else {
  // Register IPC handlers once per process, before any window creation.
  // This includes app-runtime-status so the renderer can always pull status.
  const { registerAllHandlers, getCachedRuntimeResult } = require('./src/main/ipc');
  registerAllHandlers();
  bootstrap(getCachedRuntimeResult);
}

function createMainWindow() {
  const mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile('index.html');

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => { /* allow GC */ });
  return mainWindow;
}

function bootstrap(getCachedRuntimeResult) {
  let mainWindow;

  app.whenReady().then(() => {
    // Validate runtime — getCachedRuntimeResult runs validation once and caches.
    // The same cached result is served by the app-runtime-status IPC handler,
    // so the renderer never races against a one-shot push event.
    const runtimeResult = getCachedRuntimeResult();
    if (!runtimeResult.ok) {
      console.error('Runtime validation failed:', runtimeResult.errors);
      app.quit();
      return;
    }

    if (runtimeResult.warnings.length > 0) {
      console.warn('Runtime warnings:', runtimeResult.warnings);
    }

    mainWindow = createMainWindow();
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createMainWindow();
    }
  });
}
