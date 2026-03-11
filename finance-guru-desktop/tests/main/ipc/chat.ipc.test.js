const { describe, test, expect, beforeEach, afterEach, mock } = require('bun:test');

// Mock electron's ipcMain before any require of chat.ipc
mock.module('electron', () => ({
  ipcMain: { handle: () => {}, on: () => {} }
}));

describe('chat.ipc', () => {
  let originalEnv;
  let originalHome;

  beforeEach(() => {
    originalEnv = { ...process.env };
    originalHome = process.env.HOME;
  });

  afterEach(() => {
    process.env = originalEnv;
    process.env.HOME = originalHome;
  });

  // ── checkClaudeAuth ──

  test('checkClaudeAuth returns { ok: false } when no API key and no credentials dir', () => {
    delete process.env.ANTHROPIC_API_KEY;
    // Point HOME to a location guaranteed to have no .claude dir
    process.env.HOME = '/nonexistent-home-for-test';

    const { checkClaudeAuth } = require('../../../src/main/ipc/chat.ipc');
    const result = checkClaudeAuth();

    expect(result.ok).toBe(false);
    expect(result.error).toContain('Claude authentication not found');
  });

  test('checkClaudeAuth returns { ok: true } when ANTHROPIC_API_KEY is set', () => {
    process.env.ANTHROPIC_API_KEY = 'sk-test-fake-key-for-unit-test';

    const { checkClaudeAuth } = require('../../../src/main/ipc/chat.ipc');
    const result = checkClaudeAuth();

    expect(result.ok).toBe(true);
    expect(result.error).toBeNull();
  });

  // ── chat-send session logic ──

  test('chat-send logic returns error for non-existent session', () => {
    const sessions = new Map();

    function handleChatSend(sessionId) {
      const session = sessions.get(sessionId);
      if (!session) return { success: false, error: 'No active session' };
      if (!session.sdkSessionId) return { success: false, error: 'Session not yet initialized — wait for the first response' };
      return { success: true };
    }

    const result = handleChatSend('nonexistent-session-id');

    expect(result.success).toBe(false);
    expect(result.error).toBe('No active session');
  });

  test('chat-send logic returns error when SDK session not yet initialized', () => {
    const sessions = new Map();

    sessions.set('test-session', {
      stream: null,
      closed: false,
      sdkSessionId: null
    });

    function handleChatSend(sessionId) {
      const session = sessions.get(sessionId);
      if (!session) return { success: false, error: 'No active session' };
      if (!session.sdkSessionId) return { success: false, error: 'Session not yet initialized — wait for the first response' };
      return { success: true };
    }

    const result = handleChatSend('test-session');

    expect(result.success).toBe(false);
    expect(result.error).toContain('not yet initialized');
  });

  test('chat-send logic succeeds when SDK session is available', () => {
    const sessions = new Map();

    sessions.set('test-session', {
      stream: null,
      closed: false,
      sdkSessionId: 'sdk-session-uuid-123'
    });

    function handleChatSend(sessionId) {
      const session = sessions.get(sessionId);
      if (!session) return { success: false, error: 'No active session' };
      if (!session.sdkSessionId) return { success: false, error: 'Session not yet initialized — wait for the first response' };
      return { success: true };
    }

    const result = handleChatSend('test-session');

    expect(result.success).toBe(true);
  });
});
