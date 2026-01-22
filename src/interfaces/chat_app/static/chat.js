/* =============================================================================
   A2rchi Chat UI - Professional AI Assistant Interface
   Version: 2.0.0
   
   Modular vanilla JavaScript chat application.
   No framework dependencies - just clean, readable code.
   ============================================================================= */

// =============================================================================
// Constants & Configuration
// =============================================================================

const CONFIG = {
  STORAGE_KEYS: {
    CLIENT_ID: 'a2rchi_client_id',
    ACTIVE_CONVERSATION: 'a2rchi_active_conversation_id',
  },
  ENDPOINTS: {
    STREAM: '/api/get_chat_response_stream',
    CONFIGS: '/api/get_configs',
    CONVERSATIONS: '/api/list_conversations',
    LOAD_CONVERSATION: '/api/load_conversation',
    NEW_CONVERSATION: '/api/new_conversation',
    DELETE_CONVERSATION: '/api/delete_conversation',
  },
  STREAMING: {
    TIMEOUT: 300000, // 5 minutes
  },
};

// =============================================================================
// Utility Functions
// =============================================================================

const Utils = {
  /**
   * Generate a UUID v4
   */
  generateId() {
    if (crypto?.randomUUID) {
      return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  },

  /**
   * Escape HTML to prevent XSS
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  },

  /**
   * Format a date for display
   */
  formatDate(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return '';
    
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  },

  /**
   * Group conversations by date
   */
  groupByDate(conversations) {
    const groups = { Today: [], Yesterday: [], 'Previous 7 Days': [], Older: [] };
    const now = new Date();
    
    conversations.forEach((conv) => {
      const date = new Date(conv.last_message_at || conv.created_at);
      const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) groups['Today'].push(conv);
      else if (diffDays === 1) groups['Yesterday'].push(conv);
      else if (diffDays < 7) groups['Previous 7 Days'].push(conv);
      else groups['Older'].push(conv);
    });
    
    return groups;
  },

  /**
   * Debounce function calls
   */
  debounce(fn, delay) {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn(...args), delay);
    };
  },
};

// =============================================================================
// Storage Manager
// =============================================================================

const Storage = {
  getClientId() {
    let id = localStorage.getItem(CONFIG.STORAGE_KEYS.CLIENT_ID);
    if (!id) {
      id = Utils.generateId();
      localStorage.setItem(CONFIG.STORAGE_KEYS.CLIENT_ID, id);
    }
    return id;
  },

  getActiveConversationId() {
    const stored = localStorage.getItem(CONFIG.STORAGE_KEYS.ACTIVE_CONVERSATION);
    return stored ? Number(stored) : null;
  },

  setActiveConversationId(id) {
    if (id === null || id === undefined) {
      localStorage.removeItem(CONFIG.STORAGE_KEYS.ACTIVE_CONVERSATION);
    } else {
      localStorage.setItem(CONFIG.STORAGE_KEYS.ACTIVE_CONVERSATION, String(id));
    }
  },
};

// =============================================================================
// API Client
// =============================================================================

const API = {
  clientId: Storage.getClientId(),

  async fetchJson(url, options = {}) {
    const response = await fetch(url, options);
    
    if (response.status === 401) {
      window.location.href = '/';
      return null;
    }
    
    const data = await response.json().catch(() => null);
    
    if (!response.ok) {
      throw new Error(data?.error || `Request failed (${response.status})`);
    }
    
    return data;
  },

  async getConfigs() {
    return this.fetchJson(CONFIG.ENDPOINTS.CONFIGS);
  },

  async getConversations(limit = 100) {
    const url = `${CONFIG.ENDPOINTS.CONVERSATIONS}?limit=${limit}&client_id=${encodeURIComponent(this.clientId)}`;
    return this.fetchJson(url);
  },

  async loadConversation(conversationId) {
    return this.fetchJson(CONFIG.ENDPOINTS.LOAD_CONVERSATION, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: conversationId,
        client_id: this.clientId,
      }),
    });
  },

  async newConversation() {
    return this.fetchJson(CONFIG.ENDPOINTS.NEW_CONVERSATION, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ client_id: this.clientId }),
    });
  },

  async deleteConversation(conversationId) {
    return this.fetchJson(CONFIG.ENDPOINTS.DELETE_CONVERSATION, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: conversationId,
        client_id: this.clientId,
      }),
    });
  },

  async *streamResponse(history, conversationId, configName) {
    const response = await fetch(CONFIG.ENDPOINTS.STREAM, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        last_message: history.slice(-1),
        conversation_id: conversationId,
        config_name: configName,
        client_sent_msg_ts: Date.now(),
        client_timeout: CONFIG.STREAMING.TIMEOUT,
        client_id: this.clientId,
        include_agent_steps: true,  // Required for streaming chunks
        include_tool_steps: false,
      }),
    });

    if (response.status === 401) {
      window.location.href = '/';
      return;
    }

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed (${response.status})`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();
      
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        
        try {
          yield JSON.parse(trimmed);
        } catch (e) {
          console.error('Failed to parse stream event:', e);
        }
      }
    }
  },
};

// =============================================================================
// Markdown Renderer
// =============================================================================

const Markdown = {
  init() {
    if (typeof marked !== 'undefined') {
      marked.setOptions({
        breaks: true,
        gfm: true,
        highlight: (code, lang) => this.highlightCode(code, lang),
      });
    }
  },

  highlightCode(code, lang) {
    if (typeof hljs !== 'undefined') {
      try {
        if (lang && hljs.getLanguage(lang)) {
          return hljs.highlight(code, { language: lang }).value;
        }
        return hljs.highlightAuto(code).value;
      } catch (e) {
        console.error('Highlight error:', e);
      }
    }
    return Utils.escapeHtml(code);
  },

  render(text) {
    if (!text) return '';
    
    if (typeof marked !== 'undefined') {
      try {
        let html = marked.parse(text);
        // Add copy buttons to code blocks
        html = this.addCodeBlockHeaders(html);
        return html;
      } catch (e) {
        console.error('Markdown render error:', e);
      }
    }
    
    return Utils.escapeHtml(text);
  },

  addCodeBlockHeaders(html) {
    // Match <pre><code class="language-xxx"> blocks
    return html.replace(
      /<pre><code class="language-(\w+)">/g,
      (match, lang) => `
        <pre>
          <div class="code-block-header">
            <span class="code-block-lang">${lang}</span>
            <button class="code-block-copy" onclick="Markdown.copyCode(this)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>Copy</span>
            </button>
          </div>
          <code class="language-${lang}">`
    ).replace(
      /<pre><code>/g,
      `<pre>
        <div class="code-block-header">
          <span class="code-block-lang">code</span>
          <button class="code-block-copy" onclick="Markdown.copyCode(this)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
            <span>Copy</span>
          </button>
        </div>
        <code>`
    );
  },

  copyCode(button) {
    const pre = button.closest('pre');
    const code = pre.querySelector('code');
    const text = code.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
      button.classList.add('copied');
      button.querySelector('span').textContent = 'Copied!';
      
      setTimeout(() => {
        button.classList.remove('copied');
        button.querySelector('span').textContent = 'Copy';
      }, 2000);
    });
  },
};

// Make copyCode globally accessible for onclick handlers
window.Markdown = Markdown;

// =============================================================================
// UI Components
// =============================================================================

const UI = {
  elements: {},

  init() {
    this.elements = {
      app: document.querySelector('.app'),
      sidebar: document.querySelector('.sidebar'),
      sidebarToggle: document.querySelector('.sidebar-toggle'),
      conversationList: document.querySelector('.conversation-list'),
      newChatBtn: document.querySelector('.new-chat-btn'),
      messagesContainer: document.querySelector('.messages'),
      messagesInner: document.querySelector('.messages-inner'),
      inputField: document.querySelector('.input-field'),
      sendBtn: document.querySelector('.send-btn'),
      modelSelectA: document.querySelector('.model-select-a'),
      modelSelectB: document.querySelector('.model-select-b'),
      settingsBtn: document.querySelector('.settings-btn'),
      settingsModal: document.querySelector('.settings-modal'),
      settingsBackdrop: document.querySelector('.settings-backdrop'),
      settingsClose: document.querySelector('.settings-close'),
      abCheckbox: document.querySelector('.ab-checkbox'),
      abModelGroup: document.querySelector('.ab-model-group'),
    };

    this.bindEvents();
  },

  bindEvents() {
    // Sidebar toggle
    this.elements.sidebarToggle?.addEventListener('click', () => this.toggleSidebar());
    
    // New chat
    this.elements.newChatBtn?.addEventListener('click', () => Chat.newConversation());
    
    // Send message
    this.elements.sendBtn?.addEventListener('click', () => Chat.sendMessage());
    this.elements.inputField?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        Chat.sendMessage();
      }
    });
    
    // Auto-resize textarea
    this.elements.inputField?.addEventListener('input', () => this.autoResizeInput());
    
    // Settings modal
    this.elements.settingsBtn?.addEventListener('click', () => this.openSettings());
    this.elements.settingsBackdrop?.addEventListener('click', () => this.closeSettings());
    this.elements.settingsClose?.addEventListener('click', () => this.closeSettings());
    
    // A/B toggle in settings
    this.elements.abCheckbox?.addEventListener('change', (e) => {
      const isEnabled = e.target.checked;
      if (this.elements.abModelGroup) {
        this.elements.abModelGroup.style.display = isEnabled ? 'block' : 'none';
      }
    });
    
    // Close modal on Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.elements.settingsModal?.style.display !== 'none') {
        this.closeSettings();
      }
    });
  },

  openSettings() {
    if (this.elements.settingsModal) {
      this.elements.settingsModal.style.display = 'flex';
    }
  },

  closeSettings() {
    if (this.elements.settingsModal) {
      this.elements.settingsModal.style.display = 'none';
    }
  },

  toggleSidebar() {
    this.elements.app?.classList.toggle('sidebar-collapsed');
  },

  isABEnabled() {
    return this.elements.abCheckbox?.checked ?? false;
  },

  autoResizeInput() {
    const field = this.elements.inputField;
    if (!field) return;
    field.style.height = 'auto';
    field.style.height = Math.min(field.scrollHeight, 200) + 'px';
  },

  getInputValue() {
    return this.elements.inputField?.value.trim() ?? '';
  },

  clearInput() {
    if (this.elements.inputField) {
      this.elements.inputField.value = '';
      this.elements.inputField.style.height = 'auto';
    }
  },

  setInputDisabled(disabled) {
    if (this.elements.inputField) this.elements.inputField.disabled = disabled;
    if (this.elements.sendBtn) this.elements.sendBtn.disabled = disabled;
  },

  getSelectedConfig(which = 'A') {
    const select = which === 'A' ? this.elements.modelSelectA : this.elements.modelSelectB;
    return select?.value ?? '';
  },

  renderConfigs(configs) {
    [this.elements.modelSelectA, this.elements.modelSelectB].forEach((select) => {
      if (!select) return;
      select.innerHTML = configs
        .map((c) => `<option value="${Utils.escapeHtml(c.name)}">${Utils.escapeHtml(c.name)}</option>`)
        .join('');
    });
  },

  renderConversations(conversations, activeId) {
    const list = this.elements.conversationList;
    if (!list) return;

    if (!conversations.length) {
      list.innerHTML = `
        <div class="conversation-item" style="color: var(--text-tertiary); cursor: default;">
          No conversations yet
        </div>`;
      return;
    }

    const groups = Utils.groupByDate(conversations);
    let html = '';

    for (const [label, items] of Object.entries(groups)) {
      if (!items.length) continue;
      
      html += `<div class="conversation-group">
        <div class="conversation-group-label">${label}</div>`;
      
      for (const conv of items) {
        const isActive = conv.conversation_id === activeId;
        const title = Utils.escapeHtml(conv.title || `Conversation ${conv.conversation_id}`);
        
        html += `
          <div class="conversation-item ${isActive ? 'active' : ''}" 
               data-id="${conv.conversation_id}">
            <svg class="conversation-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="conversation-item-title">${title}</span>
            <button class="conversation-item-delete" data-id="${conv.conversation_id}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          </div>`;
      }
      
      html += '</div>';
    }

    list.innerHTML = html;

    // Bind click events
    list.querySelectorAll('.conversation-item').forEach((item) => {
      item.addEventListener('click', (e) => {
        if (e.target.closest('.conversation-item-delete')) return;
        const id = Number(item.dataset.id);
        Chat.loadConversation(id);
      });
    });

    list.querySelectorAll('.conversation-item-delete').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const id = Number(btn.dataset.id);
        Chat.deleteConversation(id);
      });
    });
  },

  renderMessages(messages) {
    const container = this.elements.messagesInner;
    if (!container) return;

    if (!messages.length) {
      container.innerHTML = `
        <div class="messages-empty">
          <svg class="messages-empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
          </svg>
          <h2 class="messages-empty-title">How can I help you today?</h2>
          <p class="messages-empty-subtitle">Ask me anything about CMS Computing Operations. I'm here to assist you.</p>
        </div>`;
      return;
    }

    container.innerHTML = messages.map((msg) => this.createMessageHTML(msg)).join('');
    this.scrollToBottom();
  },

  createMessageHTML(msg) {
    const isUser = msg.sender === 'User';
    const avatar = isUser ? '👤' : '✦';
    const senderName = isUser ? 'You' : 'A2rchi';
    const roleClass = isUser ? 'user' : 'assistant';
    
    let labelHtml = '';
    if (msg.label) {
      labelHtml = `<span class="message-label">${Utils.escapeHtml(msg.label)}</span>`;
    }

    return `
      <div class="message ${roleClass}" data-id="${msg.id || ''}">
        <div class="message-inner">
          <div class="message-header">
            <div class="message-avatar">${avatar}</div>
            <span class="message-sender">${senderName}</span>
            ${labelHtml}
          </div>
          <div class="message-content">${msg.html || ''}</div>
        </div>
      </div>`;
  },

  addMessage(msg) {
    // Remove empty state if present
    const empty = this.elements.messagesInner?.querySelector('.messages-empty');
    if (empty) empty.remove();

    const html = this.createMessageHTML(msg);
    this.elements.messagesInner?.insertAdjacentHTML('beforeend', html);
    this.scrollToBottom();
  },

  updateMessage(id, updates) {
    const msgEl = this.elements.messagesInner?.querySelector(`[data-id="${id}"]`);
    if (!msgEl) return;

    const contentEl = msgEl.querySelector('.message-content');
    if (contentEl && updates.html !== undefined) {
      contentEl.innerHTML = updates.html;
      if (updates.streaming) {
        contentEl.innerHTML += '<span class="streaming-cursor"></span>';
      }
    }

    this.scrollToBottom();
  },

  showTypingIndicator() {
    const html = `
      <div class="typing-indicator">
        <div class="typing-indicator-inner">
          <div class="typing-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>`;
    this.elements.messagesInner?.insertAdjacentHTML('beforeend', html);
    this.scrollToBottom();
  },

  hideTypingIndicator() {
    this.elements.messagesInner?.querySelector('.typing-indicator')?.remove();
  },

  scrollToBottom() {
    const container = this.elements.messagesContainer;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  },
};

// =============================================================================
// Chat Controller
// =============================================================================

const Chat = {
  state: {
    conversationId: null,
    messages: [],
    history: [], // [sender, content] pairs for API
    isStreaming: false,
    configs: [],
  },

  async init() {
    Markdown.init();
    UI.init();

    // Load initial data
    await Promise.all([
      this.loadConfigs(),
      this.loadConversations(),
    ]);

    // Load active conversation if any
    const activeId = Storage.getActiveConversationId();
    if (activeId) {
      await this.loadConversation(activeId);
    }
  },

  async loadConfigs() {
    try {
      const data = await API.getConfigs();
      this.state.configs = data?.options || [];
      UI.renderConfigs(this.state.configs);
    } catch (e) {
      console.error('Failed to load configs:', e);
    }
  },

  async loadConversations() {
    try {
      const data = await API.getConversations();
      UI.renderConversations(data?.conversations || [], this.state.conversationId);
    } catch (e) {
      console.error('Failed to load conversations:', e);
    }
  },

  async loadConversation(conversationId) {
    try {
      const data = await API.loadConversation(conversationId);
      if (!data) return;

      this.state.conversationId = conversationId;
      Storage.setActiveConversationId(conversationId);

      // Convert messages to display format
      this.state.messages = (data.messages || []).map((msg, idx) => {
        const isUser = msg.sender === 'User';
        return {
          id: `${msg.message_id || idx}-${isUser ? 'u' : 'a'}`,
          sender: msg.sender,
          html: isUser ? Utils.escapeHtml(msg.content) : Markdown.render(msg.content),
        };
      });

      // Build history for API
      this.state.history = (data.messages || []).map((msg) => [msg.sender, msg.content]);

      UI.renderMessages(this.state.messages);
      await this.loadConversations(); // Refresh list to show active state
    } catch (e) {
      console.error('Failed to load conversation:', e);
    }
  },

  async newConversation() {
    try {
      await API.newConversation();
      this.state.conversationId = null;
      this.state.messages = [];
      this.state.history = [];
      Storage.setActiveConversationId(null);
      
      UI.renderMessages([]);
      await this.loadConversations();
    } catch (e) {
      console.error('Failed to create conversation:', e);
    }
  },

  async deleteConversation(conversationId) {
    if (!confirm('Delete this conversation?')) return;
    
    try {
      await API.deleteConversation(conversationId);
      
      if (this.state.conversationId === conversationId) {
        this.state.conversationId = null;
        this.state.messages = [];
        this.state.history = [];
        Storage.setActiveConversationId(null);
        UI.renderMessages([]);
      }
      
      await this.loadConversations();
    } catch (e) {
      console.error('Failed to delete conversation:', e);
    }
  },

  async sendMessage() {
    const text = UI.getInputValue();
    if (!text || this.state.isStreaming) return;

    // Add user message
    const userMsg = {
      id: `${Date.now()}-user`,
      sender: 'User',
      html: Utils.escapeHtml(text),
    };
    this.state.messages.push(userMsg);
    this.state.history.push(['User', text]);
    UI.addMessage(userMsg);

    UI.clearInput();
    UI.setInputDisabled(true);
    this.state.isStreaming = true;

    // Determine which configs to use
    const configA = UI.getSelectedConfig('A');
    const configB = UI.getSelectedConfig('B');
    const isAB = UI.isABEnabled();

    // Stream responses
    const tasks = [];

    // Config A response
    const msgIdA = `${Date.now()}-assistant-a`;
    const assistantMsgA = {
      id: msgIdA,
      sender: 'A2rchi',
      html: '',
      label: isAB ? `Model A: ${configA}` : null,
    };
    this.state.messages.push(assistantMsgA);
    UI.addMessage(assistantMsgA);
    tasks.push(this.streamResponse(msgIdA, configA));

    // Config B response (if A/B enabled)
    if (isAB && configB) {
      const msgIdB = `${Date.now()}-assistant-b`;
      const assistantMsgB = {
        id: msgIdB,
        sender: 'A2rchi',
        html: '',
        label: `Model B: ${configB}`,
      };
      this.state.messages.push(assistantMsgB);
      UI.addMessage(assistantMsgB);
      tasks.push(this.streamResponse(msgIdB, configB));
    }

    try {
      await Promise.all(tasks);
    } catch (e) {
      console.error('Streaming error:', e);
    } finally {
      this.state.isStreaming = false;
      UI.setInputDisabled(false);
      UI.elements.inputField?.focus();
      await this.loadConversations();
    }
  },

  async streamResponse(messageId, configName) {
    let streamedText = '';

    try {
      for await (const event of API.streamResponse(this.state.history, this.state.conversationId, configName)) {
        if (event.type === 'chunk') {
          // Chunks are individual tokens - concatenate them
          streamedText += event.content || '';
          UI.updateMessage(messageId, {
            html: Markdown.render(streamedText),
            streaming: true,
          });
        } else if (event.type === 'step' && event.step_type === 'agent') {
          // Agent steps may contain full accumulated content
          const content = event.content || '';
          if (content) {
            streamedText = content;
            UI.updateMessage(messageId, {
              html: Markdown.render(streamedText),
              streaming: true,
            });
          }
        } else if (event.type === 'final') {
          const finalText = event.response || streamedText;
          UI.updateMessage(messageId, {
            html: Markdown.render(finalText),
            streaming: false,
          });
          
          if (event.conversation_id != null) {
            this.state.conversationId = event.conversation_id;
            Storage.setActiveConversationId(event.conversation_id);
          }
          
          this.state.history.push(['A2rchi', finalText]);
          
          // Re-highlight code blocks
          if (typeof hljs !== 'undefined') {
            setTimeout(() => hljs.highlightAll(), 0);
          }
          return;
        } else if (event.type === 'error') {
          UI.updateMessage(messageId, {
            html: `<p style="color: var(--error-text);">${Utils.escapeHtml(event.message || 'An error occurred')}</p>`,
            streaming: false,
          });
          return;
        }
      }
    } catch (e) {
      console.error('Stream error:', e);
      UI.updateMessage(messageId, {
        html: `<p style="color: var(--error-text);">${Utils.escapeHtml(e.message || 'Streaming failed')}</p>`,
        streaming: false,
      });
    }
  },
};

// =============================================================================
// Initialize on DOM ready
// =============================================================================

document.addEventListener('DOMContentLoaded', () => Chat.init());
