const { ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');

const FAMILY_OFFICE = path.resolve(__dirname, '..', '..', '..', '..');
const sessions = new Map();
let sdk = null;
const CHAT_START_TIMEOUT_MS = 30000;

function checkClaudeAuth() {
  // Check ANTHROPIC_API_KEY first
  if (process.env.ANTHROPIC_API_KEY) return { ok: true, error: null };

  // Check for local Claude credentials
  const claudeConfigDir = path.join(process.env.HOME || '', '.claude');
  if (fs.existsSync(claudeConfigDir)) {
    const credentialFiles = ['.credentials.json', 'credentials.json', 'config.json'];
    const hasCredentials = credentialFiles.some(f =>
      fs.existsSync(path.join(claudeConfigDir, f))
    );
    if (hasCredentials) return { ok: true, error: null };
  }

  return {
    ok: false,
    error: 'Claude authentication not found. Run `claude` in your terminal to authenticate, or set ANTHROPIC_API_KEY.'
  };
}

// Lazy-load Agent SDK
async function getSDK() {
  if (!sdk) {
    sdk = await import('@anthropic-ai/claude-agent-sdk');
  }
  return sdk;
}

function baseOptions(model) {
  return {
    cwd: FAMILY_OFFICE,
    model: model || 'claude-sonnet-4-6',
    permissionMode: 'bypassPermissions',
    allowDangerouslySkipPermissions: true,
    maxTurns: 50
  };
}

// Start a query and wire up the message forwarding loop.
// Returns the Query (AsyncGenerator) object.
function startStreamLoop(stream, sessionId, event) {
  const startTimeout = setTimeout(() => {
    const session = sessions.get(sessionId);
    if (!session || session.closed || session.messageDelivered) return;
    event.sender.send('chat-error', {
      sessionId,
      error: 'Chat session timed out before the first response. Check Claude auth/permissions or SDK connectivity.'
    });
    sessions.delete(sessionId);
    if (typeof stream.close === 'function') {
      stream.close();
    }
  }, CHAT_START_TIMEOUT_MS);

  const session = sessions.get(sessionId);
  session.startTimeout = startTimeout;

  (async () => {
    try {
      for await (const message of stream) {
        const s = sessions.get(sessionId);
        if (!s || s.closed) break;

        if (!s.messageDelivered) {
          s.messageDelivered = true;
          if (s.startTimeout) {
            clearTimeout(s.startTimeout);
            s.startTimeout = null;
          }
        }

        // Capture the SDK session ID from the init message for resume support
        if (message.type === 'system' && message.subtype === 'init' && message.session_id) {
          s.sdkSessionId = message.session_id;
        }

        event.sender.send('chat-message', { sessionId, message });
      }
    } catch (err) {
      if (!sessions.get(sessionId)?.closed) {
        event.sender.send('chat-error', { sessionId, error: err.message });
      }
    } finally {
      const s = sessions.get(sessionId);
      if (s?.startTimeout) {
        clearTimeout(s.startTimeout);
      }
      // Mark the stream loop as done but keep the session alive for follow-ups
      if (s && !s.closed) {
        s.stream = null;
        s.messageDelivered = false;
      }
      event.sender.send('chat-done', { sessionId });
    }
  })();
}

function registerChatHandlers() {
  ipcMain.handle('chat-start', async (event, { prompt, model, skill }) => {
    try {
      const auth = checkClaudeAuth();
      if (!auth.ok) {
        return { success: false, error: auth.error, needsAuth: true };
      }

      const { query } = await getSDK();
      const sessionId = `chat-${Date.now()}`;
      const fullPrompt = skill ? `/${skill} ${prompt}` : prompt;

      const stream = query({
        prompt: fullPrompt,
        options: baseOptions(model)
      });

      sessions.set(sessionId, {
        stream,
        model,
        closed: false,
        messageDelivered: false,
        sdkSessionId: null,
        startTimeout: null
      });

      startStreamLoop(stream, sessionId, event);

      return { success: true, sessionId };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  ipcMain.handle('chat-send', async (event, { sessionId, text }) => {
    const session = sessions.get(sessionId);
    if (!session) return { success: false, error: 'No active session' };
    if (!session.sdkSessionId) return { success: false, error: 'Session not yet initialized — wait for the first response' };

    try {
      const { query } = await getSDK();

      // Resume the existing SDK session with a new prompt
      const stream = query({
        prompt: text,
        options: {
          ...baseOptions(session.model),
          resume: session.sdkSessionId
        }
      });

      session.stream = stream;
      session.messageDelivered = false;
      startStreamLoop(stream, sessionId, event);

      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  ipcMain.handle('chat-close', async (event, { sessionId }) => {
    const session = sessions.get(sessionId);
    if (session) {
      session.closed = true;
      if (session.startTimeout) {
        clearTimeout(session.startTimeout);
      }
      if (typeof session.stream?.close === 'function') {
        session.stream.close();
      }
      sessions.delete(sessionId);
    }
    return { success: true };
  });

  ipcMain.on('chat-interrupt', (event, { sessionId }) => {
    const session = sessions.get(sessionId);
    if (session?.stream?.interrupt) {
      session.stream.interrupt();
    }
  });
}

module.exports = { registerChatHandlers, checkClaudeAuth };
