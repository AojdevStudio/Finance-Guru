const { marked } = require('marked');

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function createChatView(containerEl) {
  marked.use({
    renderer: {
      code({ text, lang }) {
        return `<pre><code class="lang-${escapeHtml(lang || 'text')}">${escapeHtml(text)}</code></pre>`;
      }
    },
    breaks: true,
    gfm: true
  });

  const messagesEl = document.createElement('div');
  messagesEl.className = 'chat-messages';

  const inputArea = document.createElement('div');
  inputArea.className = 'chat-input-area';
  inputArea.innerHTML = `
    <textarea id="chat-input" placeholder="Ask about your portfolio..." rows="1"></textarea>
    <button class="btn btn-primary" id="chat-send">Send</button>
  `;

  containerEl.innerHTML = '';
  containerEl.appendChild(messagesEl);
  containerEl.appendChild(inputArea);

  let currentSessionId = null;
  let currentAssistantEl = null;
  let streamBuffer = '';

  const api = window.electron_api;

  const unsubMessage = api.chat.onMessage((data) => {
    if (data.sessionId !== currentSessionId) return;
    const msg = data.message;

    if (msg.type === 'assistant') {
      if (!currentAssistantEl) {
        currentAssistantEl = addMessage('assistant', '');
      }
      for (const block of (msg.content || [])) {
        if (block.type === 'text') {
          streamBuffer += block.text || '';
        } else if (block.type === 'tool_use') {
          addToolCall(block.name, block.input);
        }
      }
      if (streamBuffer) {
        currentAssistantEl.querySelector('.msg-text').innerHTML = marked.parse(streamBuffer);
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }
    } else if (msg.type === 'result') {
      if (msg.result) {
        if (!currentAssistantEl) {
          currentAssistantEl = addMessage('assistant', '');
        }
        streamBuffer += msg.result;
        currentAssistantEl.querySelector('.msg-text').innerHTML = marked.parse(streamBuffer);
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }
    } else if (msg.type === 'system') {
      if (msg.subtype === 'init' && msg.data?.session_id) {
        // Store session metadata if needed
      }
    }
  });

  const unsubDone = api.chat.onDone((data) => {
    if (data.sessionId !== currentSessionId) return;
    currentAssistantEl = null;
    streamBuffer = '';
  });

  async function sendMessage(text) {
    if (!text.trim()) return;
    addMessage('user', text);
    document.getElementById('chat-input').value = '';

    if (!currentSessionId) {
      const result = await api.chat.start({ prompt: text });
      if (result.success) {
        currentSessionId = result.sessionId;
      } else {
        addMessage('system', `Error: ${result.error}`);
      }
    } else {
      await api.chat.send({ sessionId: currentSessionId, text });
    }
  }

  async function startWithSkill(skill, prompt) {
    addMessage('system', `Activating ${skill}...`);
    const result = await api.chat.start({ prompt: prompt || '', skill });
    if (result.success) {
      currentSessionId = result.sessionId;
    }
  }

  function reset() {
    if (currentSessionId) {
      api.chat.close({ sessionId: currentSessionId });
    }
    currentSessionId = null;
    currentAssistantEl = null;
    streamBuffer = '';
    messagesEl.innerHTML = '';
  }

  function addMessage(role, content) {
    const el = document.createElement('div');
    el.className = `chat-msg chat-msg-${role}`;
    el.innerHTML = `<div class="msg-text">${role === 'user' ? escapeHtml(content) : content}</div>`;
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
  }

  function addToolCall(name, input) {
    const el = document.createElement('div');
    el.className = 'chat-tool-call';
    const icon = name === 'Bash' ? '\u{1F4BB}' : name === 'Read' ? '\u{1F4C4}' : '\u{1F527}';
    el.innerHTML = `<span>${icon}</span> <span>${escapeHtml(name)}</span>`;
    messagesEl.appendChild(el);
  }

  document.getElementById('chat-send').addEventListener('click', () => {
    sendMessage(document.getElementById('chat-input').value);
  });

  document.getElementById('chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(e.target.value);
    }
  });

  return { sendMessage, startWithSkill, reset, addMessage };
}

module.exports = { createChatView };
