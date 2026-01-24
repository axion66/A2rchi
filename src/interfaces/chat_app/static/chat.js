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
    AB_WARNING_DISMISSED: 'a2rchi_ab_warning_dismissed',
    TRACE_VERBOSE_MODE: 'a2rchi_trace_verbose_mode',
  },
  ENDPOINTS: {
    STREAM: '/api/get_chat_response_stream',
    CONFIGS: '/api/get_configs',
    CONVERSATIONS: '/api/list_conversations',
    LOAD_CONVERSATION: '/api/load_conversation',
    NEW_CONVERSATION: '/api/new_conversation',
    DELETE_CONVERSATION: '/api/delete_conversation',
    AB_CREATE: '/api/ab/create',
    AB_PREFERENCE: '/api/ab/preference',
    AB_PENDING: '/api/ab/pending',
    TRACE_GET: '/api/trace',
    CANCEL_STREAM: '/api/cancel_stream',
  },
  STREAMING: {
    TIMEOUT: 300000, // 5 minutes
  },
  TRACE: {
    MAX_TOOL_OUTPUT_PREVIEW: 500,
    AUTO_COLLAPSE_TOOL_COUNT: 5,
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

  async *streamResponse(history, conversationId, configName, signal = null) {
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
        include_tool_steps: true,   // Enable tool step events for trace
      }),
      signal: signal,
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

    try {
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
    } finally {
      reader.releaseLock();
    }
  },

  // A/B Testing API methods
  async createABComparison(data) {
    return this.fetchJson(CONFIG.ENDPOINTS.AB_CREATE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...data,
        client_id: this.clientId,
      }),
    });
  },

  async submitABPreference(comparisonId, preference) {
    return this.fetchJson(CONFIG.ENDPOINTS.AB_PREFERENCE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        comparison_id: comparisonId,
        preference: preference,
        client_id: this.clientId,
      }),
    });
  },

  async getPendingABComparison(conversationId) {
    const url = `${CONFIG.ENDPOINTS.AB_PENDING}?conversation_id=${conversationId}&client_id=${encodeURIComponent(this.clientId)}`;
    return this.fetchJson(url);
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
      sidebarOverlay: document.querySelector('.sidebar-overlay'),
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
      traceVerboseOptions: document.querySelector('.trace-verbose-options'),
    };

    this.bindEvents();
    this.initTraceVerboseMode();
  },

  initTraceVerboseMode() {
    // Set the initial radio button based on stored preference
    const storedMode = localStorage.getItem(CONFIG.STORAGE_KEYS.TRACE_VERBOSE_MODE) || 'normal';
    const radio = document.querySelector(`input[name="trace-verbose"][value="${storedMode}"]`);
    if (radio) {
      radio.checked = true;
    }
  },

  bindEvents() {
    // Sidebar toggle
    this.elements.sidebarToggle?.addEventListener('click', () => this.toggleSidebar());
    
    // Sidebar overlay click to close (mobile)
    this.elements.sidebarOverlay?.addEventListener('click', () => this.closeSidebar());
    
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
      if (isEnabled) {
        // Show warning modal before enabling
        const dismissed = sessionStorage.getItem(CONFIG.STORAGE_KEYS.AB_WARNING_DISMISSED);
        if (!dismissed) {
          e.target.checked = false; // Reset checkbox
          this.showABWarningModal(
            () => {
              // On confirm
              e.target.checked = true;
              if (this.elements.abModelGroup) {
                this.elements.abModelGroup.style.display = 'block';
              }
              sessionStorage.setItem(CONFIG.STORAGE_KEYS.AB_WARNING_DISMISSED, 'true');
            },
            () => {
              // On cancel
              e.target.checked = false;
            }
          );
          return;
        }
      }
      if (this.elements.abModelGroup) {
        this.elements.abModelGroup.style.display = isEnabled ? 'block' : 'none';
      }
      // If disabling A/B mode while vote is pending, re-enable input
      if (!isEnabled && Chat.state.abVotePending) {
        Chat.cancelPendingABComparison();
      }
    });

    // Trace verbose mode radio buttons
    this.elements.traceVerboseOptions?.addEventListener('change', (e) => {
      if (e.target.name === 'trace-verbose') {
        Chat.setTraceVerboseMode(e.target.value);
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
    const isMobile = window.innerWidth <= 768;
    if (isMobile) {
      // On mobile, toggle sidebar-open to show/hide the overlay sidebar
      this.elements.app?.classList.toggle('sidebar-open');
    } else {
      // On desktop, toggle sidebar-collapsed to collapse the sidebar
      this.elements.app?.classList.toggle('sidebar-collapsed');
    }
    // Update aria-expanded state
    const toggle = this.elements.sidebarToggle;
    if (toggle) {
      const isOpen = isMobile 
        ? this.elements.app?.classList.contains('sidebar-open')
        : !this.elements.app?.classList.contains('sidebar-collapsed');
      toggle.setAttribute('aria-expanded', isOpen);
    }
  },

  closeSidebar() {
    // Close the sidebar on mobile (called by overlay click)
    this.elements.app?.classList.remove('sidebar-open');
    const toggle = this.elements.sidebarToggle;
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'false');
    }
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
            <svg class="conversation-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span class="conversation-item-title">${title}</span>
            <button class="conversation-item-delete" data-id="${conv.conversation_id}" aria-label="Delete conversation" title="Delete conversation">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
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
    const avatar = isUser 
      ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L9.19 8.63 2 9.24l5.46 4.73L5.82 21 12 17.27 18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2z"/></svg>';
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

  // =========================================================================
  // A/B Testing UI Methods
  // =========================================================================

  showABWarningModal(onConfirm, onCancel) {
    // Prevent duplicate modals
    if (document.getElementById('ab-warning-modal')) {
      return;
    }
    
    const modalHtml = `
      <div class="ab-warning-modal-overlay" id="ab-warning-modal">
        <div class="ab-warning-modal">
          <div class="ab-warning-modal-header">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            <h3>Enable A/B Testing Mode</h3>
          </div>
          <div class="ab-warning-modal-body">
            <p>This will compare two AI responses for each message.</p>
            <ul>
              <li><strong>2× API usage</strong> - Each message generates two responses</li>
              <li><strong>Voting required</strong> - You must choose the better response before continuing</li>
              <li>You can disable A/B mode at any time to skip voting</li>
            </ul>
          </div>
          <div class="ab-warning-modal-actions">
            <button class="ab-warning-btn ab-warning-btn-cancel">Cancel</button>
            <button class="ab-warning-btn ab-warning-btn-confirm">Enable A/B Mode</button>
          </div>
        </div>
      </div>`;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = document.getElementById('ab-warning-modal');

    const closeModal = () => modal?.remove();

    modal.querySelector('.ab-warning-btn-cancel').addEventListener('click', () => {
      closeModal();
      onCancel?.();
    });

    modal.querySelector('.ab-warning-btn-confirm').addEventListener('click', () => {
      closeModal();
      onConfirm?.();
    });

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeModal();
        onCancel?.();
      }
    });
  },

  showToast(message, duration = 3000) {
    // Remove existing toast
    document.querySelector('.toast')?.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },

  addABComparisonContainer(msgIdA, msgIdB) {
    // Remove empty state if present
    const empty = this.elements.messagesInner?.querySelector('.messages-empty');
    if (empty) empty.remove();

    const showTrace = Chat.state.traceVerboseMode !== 'minimal';
    const traceIconSvg = `<svg class="trace-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`;
    const traceHtml = (id) => showTrace ? `
          <div class="trace-container ab-trace-container" data-message-id="${id}">
            <div class="trace-header" onclick="UI.toggleTraceExpanded('${id}')">
              ${traceIconSvg}
              <span class="trace-label">Agent Activity</span>
              <span class="toggle-icon">▼</span>
            </div>
            <div class="trace-content"></div>
          </div>` : '';

    const html = `
      <div class="ab-comparison" id="ab-comparison-active">
        <div class="ab-response ab-response-a" data-id="${msgIdA}">
          <div class="ab-response-header">
            <span class="ab-response-label">Model A</span>
          </div>
          ${traceHtml(msgIdA)}
          <div class="ab-response-content message-content"></div>
        </div>
        <div class="ab-response ab-response-b" data-id="${msgIdB}">
          <div class="ab-response-header">
            <span class="ab-response-label">Model B</span>
          </div>
          ${traceHtml(msgIdB)}
          <div class="ab-response-content message-content"></div>
        </div>
      </div>`;

    this.elements.messagesInner?.insertAdjacentHTML('beforeend', html);
    this.scrollToBottom();
  },

  updateABResponse(responseId, html, streaming = false) {
    const container = document.querySelector(`.ab-response[data-id="${responseId}"]`);
    if (!container) return;

    const contentEl = container.querySelector('.ab-response-content');
    if (contentEl) {
      contentEl.innerHTML = html;
      if (streaming) {
        contentEl.innerHTML += '<span class="streaming-cursor"></span>';
      }
    }
    this.scrollToBottom();
  },

  showABVoteButtons(comparisonId) {
    const comparison = document.getElementById('ab-comparison-active');
    if (!comparison) return;

    const voteHtml = `
      <div class="ab-vote-container" data-comparison-id="${comparisonId}">
        <div class="ab-vote-prompt">Which response was better?</div>
        <div class="ab-vote-buttons">
          <button class="ab-vote-btn ab-vote-btn-a" data-vote="a">
            <span class="ab-vote-icon">👍</span>
            <span>Model A</span>
          </button>
          <button class="ab-vote-btn ab-vote-btn-b" data-vote="b">
            <span class="ab-vote-icon">👍</span>
            <span>Model B</span>
          </button>
        </div>
      </div>`;

    comparison.insertAdjacentHTML('afterend', voteHtml);

    // Bind vote button events
    document.querySelectorAll('.ab-vote-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const vote = btn.dataset.vote;
        Chat.submitABPreference(vote);
      });
    });

    this.scrollToBottom();
  },

  hideABVoteButtons() {
    document.querySelector('.ab-vote-container')?.remove();
  },

  markABWinner(preference) {
    const comparison = document.getElementById('ab-comparison-active');
    if (!comparison) return;

    const responseA = comparison.querySelector('.ab-response-a');
    const responseB = comparison.querySelector('.ab-response-b');

    let winnerContent = '';
    let winnerTrace = '';
    if (preference === 'a') {
      winnerContent = responseA?.querySelector('.ab-response-content')?.innerHTML || '';
      winnerTrace = responseA?.querySelector('.trace-container')?.outerHTML || '';
    } else if (preference === 'b') {
      winnerContent = responseB?.querySelector('.ab-response-content')?.innerHTML || '';
      winnerTrace = responseB?.querySelector('.trace-container')?.outerHTML || '';
    } else {
      // Tie - keep both visible but mark them
      responseA?.classList.add('ab-response-tie');
      responseB?.classList.add('ab-response-tie');
      comparison.removeAttribute('id');
      return;
    }

    // Replace the entire comparison with a normal A2rchi message (matching createMessageHTML format)
    // Include the trace container from the winning response
    const normalMessage = `
      <div class="message assistant" data-id="ab-winner-${Date.now()}">
        <div class="message-inner">
          <div class="message-header">
            <div class="message-avatar">✦</div>
            <span class="message-sender">A2rchi</span>
          </div>
          ${winnerTrace}
          <div class="message-content">${winnerContent}</div>
        </div>
      </div>`;

    comparison.outerHTML = normalMessage;
  },

  removeABComparisonContainer() {
    document.getElementById('ab-comparison-active')?.remove();
    this.hideABVoteButtons();
  },

  showABError(message) {
    this.removeABComparisonContainer();
    const errorHtml = `
      <div class="message assistant ab-error-message">
        <div class="message-inner">
          <div class="message-header">
            <div class="message-avatar">⚠️</div>
            <span class="message-sender">A/B Comparison Failed</span>
          </div>
          <div class="message-content">
            <p style="color: var(--error-text);">${Utils.escapeHtml(message)}</p>
            <p>Continuing in single-response mode.</p>
          </div>
        </div>
      </div>`;
    this.elements.messagesInner?.insertAdjacentHTML('beforeend', errorHtml);
    this.scrollToBottom();
  },

  // =========================================================================
  // Agent Trace Rendering
  // =========================================================================

  createTraceContainer(messageId) {
    const msgEl = this.elements.messagesInner?.querySelector(`[data-id="${messageId}"]`);
    if (!msgEl) return;

    // Insert trace container before message content
    const inner = msgEl.querySelector('.message-inner');
    if (!inner) return;

    const existingTrace = inner.querySelector('.trace-container');
    if (existingTrace) return;

    const traceIconSvg = `<svg class="trace-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>`;
    const traceHtml = `
      <div class="trace-container" data-message-id="${messageId}">
        <div class="trace-header">
          ${traceIconSvg}
          <span class="trace-label">Agent Activity</span>
          <button class="trace-toggle" aria-label="Toggle agent activity details" title="Toggle agent activity" onclick="UI.toggleTraceExpanded('${messageId}')">
            <span class="toggle-icon" aria-hidden="true">▼</span>
          </button>
        </div>
        <div class="trace-content"></div>
      </div>`;

    inner.insertAdjacentHTML('afterbegin', traceHtml);
  },

  toggleTraceExpanded(messageId) {
    const container = document.querySelector(`.trace-container[data-message-id="${messageId}"]`);
    if (!container) return;

    container.classList.toggle('collapsed');
    const toggleIcon = container.querySelector('.toggle-icon');
    if (toggleIcon) {
      toggleIcon.textContent = container.classList.contains('collapsed') ? '▶' : '▼';
    }
  },

  renderToolStart(messageId, event) {
    const traceContent = document.querySelector(`.trace-container[data-message-id="${messageId}"] .trace-content`);
    if (!traceContent) return;

    const toolHtml = `
      <div class="tool-block tool-running" data-tool-call-id="${event.tool_call_id}">
        <div class="tool-header" onclick="UI.toggleToolExpanded('${event.tool_call_id}')">
          <span class="tool-icon">🔧</span>
          <span class="tool-name">${Utils.escapeHtml(event.tool_name)}</span>
          <span class="tool-status">
            <span class="spinner"></span> Running...
          </span>
        </div>
        <div class="tool-details">
          <div class="tool-args">
            <div class="tool-section-label">Arguments</div>
            <pre><code>${this.formatToolArgs(event.tool_args)}</code></pre>
          </div>
          <div class="tool-output-section" style="display: none;">
            <div class="tool-section-label">Output</div>
            <pre><code class="tool-output-content"></code></pre>
          </div>
        </div>
      </div>`;

    traceContent.insertAdjacentHTML('beforeend', toolHtml);
    this.scrollToBottom();

    // Auto-expand if verbose mode
    if (Chat.state.traceVerboseMode === 'verbose') {
      const toolBlock = traceContent.querySelector(`[data-tool-call-id="${event.tool_call_id}"]`);
      toolBlock?.classList.add('expanded');
    }
  },

  renderToolOutput(messageId, event) {
    const toolBlock = document.querySelector(`.tool-block[data-tool-call-id="${event.tool_call_id}"]`);
    if (!toolBlock) return;

    const outputSection = toolBlock.querySelector('.tool-output-section');
    const outputContent = toolBlock.querySelector('.tool-output-content');
    
    if (outputSection) {
      outputSection.style.display = 'block';
    }
    
    if (outputContent) {
      let displayText = event.output || '';
      if (displayText.length > CONFIG.TRACE.MAX_TOOL_OUTPUT_PREVIEW) {
        displayText = displayText.slice(0, CONFIG.TRACE.MAX_TOOL_OUTPUT_PREVIEW) + '...';
      }
      outputContent.textContent = displayText;
      
      if (event.truncated && event.full_length) {
        const notice = document.createElement('div');
        notice.className = 'truncation-notice';
        notice.textContent = `Showing ${CONFIG.TRACE.MAX_TOOL_OUTPUT_PREVIEW} of ${event.full_length} chars`;
        outputSection.appendChild(notice);
      }
    }

    this.scrollToBottom();
  },

  renderToolEnd(messageId, event) {
    const toolBlock = document.querySelector(`.tool-block[data-tool-call-id="${event.tool_call_id}"]`);
    if (!toolBlock) return;

    toolBlock.classList.remove('tool-running');
    toolBlock.classList.add(event.status === 'success' ? 'tool-success' : 'tool-error');

    const statusEl = toolBlock.querySelector('.tool-status');
    if (statusEl) {
      if (event.status === 'success') {
        const durationText = event.duration_ms ? ` ${event.duration_ms}ms` : '';
        statusEl.innerHTML = `<span class="checkmark">✓</span>${durationText}`;
      } else {
        statusEl.innerHTML = `<span class="error-icon">✗</span> Error`;
      }
    }

    // Auto-collapse if many tools
    const toolCount = document.querySelectorAll('.tool-block').length;
    if (Chat.state.traceVerboseMode === 'normal' && toolCount > CONFIG.TRACE.AUTO_COLLAPSE_TOOL_COUNT) {
      toolBlock.classList.remove('expanded');
    }
  },

  toggleToolExpanded(toolCallId) {
    const toolBlock = document.querySelector(`.tool-block[data-tool-call-id="${toolCallId}"]`);
    if (toolBlock) {
      toolBlock.classList.toggle('expanded');
    }
  },

  finalizeTrace(messageId, trace) {
    const container = document.querySelector(`.trace-container[data-message-id="${messageId}"]`);
    if (!container) return;

    const toolCount = trace.toolCalls.size;
    const label = container.querySelector('.trace-label');
    if (label && toolCount > 0) {
      label.textContent = `Agent Activity (${toolCount} tool${toolCount === 1 ? '' : 's'})`;
    }

    // Auto-collapse in normal mode
    if (Chat.state.traceVerboseMode === 'normal') {
      container.classList.add('collapsed');
      const toggleIcon = container.querySelector('.toggle-icon');
      if (toggleIcon) toggleIcon.textContent = '▶';
    }
  },

  formatToolArgs(args) {
    if (!args) return '';
    try {
      if (typeof args === 'string') {
        return Utils.escapeHtml(args);
      }
      return Utils.escapeHtml(JSON.stringify(args, null, 2));
    } catch {
      return Utils.escapeHtml(String(args));
    }
  },

  showCancelButton(messageId) {
    const msgEl = this.elements.messagesInner?.querySelector(`[data-id="${messageId}"]`);
    if (!msgEl) return;

    const existing = msgEl.querySelector('.cancel-stream-btn');
    if (existing) return;

    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'cancel-stream-btn';
    cancelBtn.innerHTML = '⏹ Stop';
    cancelBtn.onclick = () => Chat.cancelStream();

    msgEl.querySelector('.message-inner')?.appendChild(cancelBtn);
  },

  hideCancelButton(messageId) {
    const msgEl = this.elements.messagesInner?.querySelector(`[data-id="${messageId}"]`);
    msgEl?.querySelector('.cancel-stream-btn')?.remove();
  },
};

// Make UI globally accessible for onclick handlers
window.UI = UI;

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
    // A/B Testing state
    activeABComparison: null,  // { comparisonId, responseAId, responseBId, configAId, configBId, userPromptMid }
    abVotePending: false,      // true when waiting for user vote
    // Trace state
    activeTrace: null,         // { traceId, events: [], toolCalls: Map<toolCallId, toolData> }
    traceVerboseMode: localStorage.getItem(CONFIG.STORAGE_KEYS.TRACE_VERBOSE_MODE) || 'normal', // 'minimal' | 'normal' | 'verbose'
    abortController: null,     // AbortController for cancellation
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

    // Block if A/B vote is pending
    if (this.state.abVotePending) {
      UI.showToast('Please vote on the current comparison first, or disable A/B mode');
      return;
    }

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
    const isAB = UI.isABEnabled() && configB;

    if (isAB) {
      await this.sendABMessage(text, configA, configB);
    } else {
      await this.sendSingleMessage(configA);
    }
  },

  async sendSingleMessage(configName) {
    const msgId = `${Date.now()}-assistant`;
    const assistantMsg = {
      id: msgId,
      sender: 'A2rchi',
      html: '',
    };
    this.state.messages.push(assistantMsg);
    UI.addMessage(assistantMsg);

    try {
      UI.showCancelButton(msgId);
      await this.streamResponse(msgId, configName);
    } catch (e) {
      console.error('Streaming error:', e);
    } finally {
      UI.hideCancelButton(msgId);
      this.state.isStreaming = false;
      UI.setInputDisabled(false);
      UI.elements.inputField?.focus();
      await this.loadConversations();
    }
  },

  async sendABMessage(userText, configA, configB) {
    // Randomize which config gets A vs B
    const shuffled = Math.random() < 0.5;
    const [actualConfigA, actualConfigB] = shuffled ? [configB, configA] : [configA, configB];

    const msgIdA = `${Date.now()}-ab-a`;
    const msgIdB = `${Date.now()}-ab-b`;

    // Create side-by-side container
    UI.addABComparisonContainer(msgIdA, msgIdB);

    // Track streaming results
    const results = {
      a: { text: '', messageId: null, configId: null, error: null },
      b: { text: '', messageId: null, configId: null, error: null },
    };

    try {
      // Stream both responses in parallel
      await Promise.all([
        this.streamABResponse(msgIdA, actualConfigA, results.a),
        this.streamABResponse(msgIdB, actualConfigB, results.b),
      ]);

      // Check for errors
      if (results.a.error || results.b.error) {
        const errorMsg = results.a.error || results.b.error;
        UI.showABError(errorMsg);
        this.state.isStreaming = false;
        UI.setInputDisabled(false);
        await this.loadConversations();
        return;
      }

      // Get config IDs
      const configAId = this.getConfigId(actualConfigA);
      const configBId = this.getConfigId(actualConfigB);

      // Create A/B comparison record
      const response = await API.createABComparison({
        conversation_id: this.state.conversationId,
        user_prompt_mid: results.a.userPromptMid || results.b.userPromptMid,
        response_a_mid: results.a.messageId,
        response_b_mid: results.b.messageId,
        config_a_id: configAId,
        config_b_id: configBId,
        is_config_a_first: !shuffled,
      });

      if (response?.comparison_id) {
        this.state.activeABComparison = {
          comparisonId: response.comparison_id,
          responseAId: results.a.messageId,
          responseBId: results.b.messageId,
          responseAText: results.a.text,
          responseBText: results.b.text,
          configAId: configAId,
          configBId: configBId,
        };
        this.state.abVotePending = true;

        // Show vote buttons
        UI.showABVoteButtons(response.comparison_id);
      }

    } catch (e) {
      console.error('A/B comparison error:', e);
      UI.showABError(e.message || 'Failed to create comparison');
      this.state.isStreaming = false;
      UI.setInputDisabled(false);
      await this.loadConversations();
      return;
    }

    this.state.isStreaming = false;
    // Keep input disabled until vote
    await this.loadConversations();
  },

  async streamABResponse(elementId, configName, result) {
    let streamedText = '';
    const showTrace = this.state.traceVerboseMode !== 'minimal';
    const toolCalls = new Map(); // Track tool calls for this response

    try {
      for await (const event of API.streamResponse(this.state.history, this.state.conversationId, configName)) {
        // Handle trace events
        if (event.type === 'tool_start') {
          toolCalls.set(event.tool_call_id, {
            name: event.tool_name,
            args: event.tool_args,
            status: 'running',
            output: null,
            duration: null,
          });
          if (showTrace) {
            UI.renderToolStart(elementId, event);
          }
        } else if (event.type === 'tool_output') {
          const toolData = toolCalls.get(event.tool_call_id);
          if (toolData) {
            toolData.output = event.output;
          }
          if (showTrace) {
            UI.renderToolOutput(elementId, event);
          }
        } else if (event.type === 'tool_end') {
          const toolData = toolCalls.get(event.tool_call_id);
          if (toolData) {
            toolData.status = event.status;
            toolData.duration = event.duration_ms;
          }
          if (showTrace) {
            UI.renderToolEnd(elementId, event);
          }
        } else if (event.type === 'chunk') {
          streamedText += event.content || '';
          UI.updateABResponse(elementId, Markdown.render(streamedText), true);
        } else if (event.type === 'step' && event.step_type === 'agent') {
          const content = event.content || '';
          if (content) {
            streamedText = content;
            UI.updateABResponse(elementId, Markdown.render(streamedText), true);
          }
        } else if (event.type === 'final') {
          const finalText = event.response || streamedText;
          
          // Finalize trace display
          if (showTrace) {
            UI.finalizeTrace(elementId, { toolCalls });
          }
          
          UI.updateABResponse(elementId, Markdown.render(finalText), false);

          if (event.conversation_id != null) {
            this.state.conversationId = event.conversation_id;
            Storage.setActiveConversationId(event.conversation_id);
          }

          result.text = finalText;
          result.messageId = event.message_id;
          result.userPromptMid = event.user_message_id;

          // Re-highlight code blocks
          if (typeof hljs !== 'undefined') {
            setTimeout(() => hljs.highlightAll(), 0);
          }
          return;
        } else if (event.type === 'error') {
          result.error = event.message || 'Stream error';
          UI.updateABResponse(
            elementId,
            `<p style="color: var(--error-text);">${Utils.escapeHtml(result.error)}</p>`,
            false
          );
          return;
        }
      }
    } catch (e) {
      console.error('A/B stream error:', e);
      result.error = e.message || 'Streaming failed';
      UI.updateABResponse(
        elementId,
        `<p style="color: var(--error-text);">${Utils.escapeHtml(result.error)}</p>`,
        false
      );
    }
  },

  getConfigId(configName) {
    const config = this.state.configs.find((c) => c.name === configName);
    return config?.id || null;
  },

  async submitABPreference(preference) {
    if (!this.state.activeABComparison) return;

    try {
      await API.submitABPreference(this.state.activeABComparison.comparisonId, preference);

      // Update UI to show result
      UI.markABWinner(preference);
      UI.hideABVoteButtons();

      // Add the winning response to history for context
      const winningText =
        preference === 'b'
          ? this.state.activeABComparison.responseBText
          : this.state.activeABComparison.responseAText;
      this.state.history.push(['A2rchi', winningText]);

      // Clear A/B state
      this.state.activeABComparison = null;
      this.state.abVotePending = false;
      UI.setInputDisabled(false);
      UI.elements.inputField?.focus();
    } catch (e) {
      console.error('Failed to submit preference:', e);
      UI.showToast('Failed to submit preference. Please try again.');
    }
  },

  cancelPendingABComparison() {
    // Called when user disables A/B mode while vote is pending
    if (!this.state.abVotePending) return;

    // Add response A to history as default
    if (this.state.activeABComparison?.responseAText) {
      this.state.history.push(['A2rchi', this.state.activeABComparison.responseAText]);
    }

    // Mark as tie/skipped visually
    UI.markABWinner('tie');
    UI.hideABVoteButtons();

    // Clear state
    this.state.activeABComparison = null;
    this.state.abVotePending = false;
    UI.setInputDisabled(false);
    UI.showToast('A/B comparison skipped');
  },

  async streamResponse(messageId, configName) {
    let streamedText = '';
    
    // Initialize trace state for this stream
    this.state.activeTrace = {
      traceId: null,
      events: [],
      toolCalls: new Map(), // Map<toolCallId, { name, args, status, output, duration }>
    };

    // Create abort controller for cancellation
    this.state.abortController = new AbortController();

    // Create trace container if in verbose/normal mode
    const showTrace = this.state.traceVerboseMode !== 'minimal';
    if (showTrace) {
      UI.createTraceContainer(messageId);
    }

    try {
      for await (const event of API.streamResponse(
        this.state.history,
        this.state.conversationId,
        configName,
        this.state.abortController.signal
      )) {
        // Handle trace events
        if (event.type === 'tool_start') {
          this.state.activeTrace.toolCalls.set(event.tool_call_id, {
            name: event.tool_name,
            args: event.tool_args,
            status: 'running',
            output: null,
            duration: null,
          });
          this.state.activeTrace.events.push(event);
          if (showTrace) {
            UI.renderToolStart(messageId, event);
          }
        } else if (event.type === 'tool_output') {
          const toolData = this.state.activeTrace.toolCalls.get(event.tool_call_id);
          if (toolData) {
            toolData.output = event.output;
          }
          this.state.activeTrace.events.push(event);
          if (showTrace) {
            UI.renderToolOutput(messageId, event);
          }
        } else if (event.type === 'tool_end') {
          const toolData = this.state.activeTrace.toolCalls.get(event.tool_call_id);
          if (toolData) {
            toolData.status = event.status;
            toolData.duration = event.duration_ms;
          }
          this.state.activeTrace.events.push(event);
          if (showTrace) {
            UI.renderToolEnd(messageId, event);
          }
        } else if (event.type === 'chunk') {
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
          
          // Store trace ID
          if (event.trace_id) {
            this.state.activeTrace.traceId = event.trace_id;
          }
          
          // Finalize trace display
          if (showTrace) {
            UI.finalizeTrace(messageId, this.state.activeTrace);
          }
          
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
        } else if (event.type === 'cancelled') {
          UI.updateMessage(messageId, {
            html: streamedText 
              ? Markdown.render(streamedText) + '<p class="cancelled-notice"><em>Response cancelled</em></p>'
              : '<p class="cancelled-notice"><em>Response cancelled</em></p>',
            streaming: false,
          });
          return;
        }
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        UI.updateMessage(messageId, {
          html: streamedText 
            ? Markdown.render(streamedText) + '<p class="cancelled-notice"><em>Response cancelled</em></p>'
            : '<p class="cancelled-notice"><em>Response cancelled</em></p>',
          streaming: false,
        });
        return;
      }
      console.error('Stream error:', e);
      UI.updateMessage(messageId, {
        html: `<p style="color: var(--error-text);">${Utils.escapeHtml(e.message || 'Streaming failed')}</p>`,
        streaming: false,
      });
    } finally {
      this.state.abortController = null;
      this.state.activeTrace = null;
    }
  },

  async cancelStream() {
    if (this.state.abortController) {
      this.state.abortController.abort();
      
      // Also notify server
      if (this.state.conversationId) {
        try {
          await fetch(CONFIG.ENDPOINTS.CANCEL_STREAM, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              conversation_id: this.state.conversationId,
              client_id: Storage.getClientId(),
            }),
          });
        } catch (e) {
          console.error('Failed to notify server of cancellation:', e);
        }
      }
    }
  },

  setTraceVerboseMode(mode) {
    if (['minimal', 'normal', 'verbose'].includes(mode)) {
      this.state.traceVerboseMode = mode;
      localStorage.setItem(CONFIG.STORAGE_KEYS.TRACE_VERBOSE_MODE, mode);
    }
  },
};

// =============================================================================
// Initialize on DOM ready
// =============================================================================

document.addEventListener('DOMContentLoaded', () => Chat.init());
