import React, { useCallback, useEffect, useMemo, useRef, useState } from "https://esm.sh/react@18";
import { createRoot } from "https://esm.sh/react-dom@18/client";
import htm from "https://esm.sh/htm@3.1.1?deps=react@18";
import {
  MainContainer,
  Sidebar,
  ConversationList,
  Conversation,
  ChatContainer,
  MessageList,
  Message,
  MessageInput,
  TypingIndicator,
  ConversationHeader,
} from "https://esm.sh/@chatscope/chat-ui-kit-react@1.3.0?deps=react@18";

const html = htm.bind(React.createElement);

const CLIENT_ID_STORAGE_KEY = "a2rchi_client_id";
const ACTIVE_CONVERSATION_STORAGE_KEY = "a2rchi_active_conversation_id";
const STREAM_ENDPOINT = "/api/get_chat_response_stream";

const generateClientId = () => {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

const getStoredClientId = () => {
  let existingId = localStorage.getItem(CLIENT_ID_STORAGE_KEY);
  if (!existingId) {
    existingId = generateClientId();
    localStorage.setItem(CLIENT_ID_STORAGE_KEY, existingId);
  }
  return existingId;
};

const getStoredConversationId = () => {
  const stored = localStorage.getItem(ACTIVE_CONVERSATION_STORAGE_KEY);
  if (!stored) return null;
  const parsed = Number(stored);
  return Number.isFinite(parsed) ? parsed : null;
};

const setStoredConversationId = (value) => {
  if (value === null || value === undefined) {
    localStorage.removeItem(ACTIVE_CONVERSATION_STORAGE_KEY);
  } else {
    localStorage.setItem(ACTIVE_CONVERSATION_STORAGE_KEY, String(value));
  }
};

const escapeHtml = (value) =>
  String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");

const renderMarkdown = (markdownText) => {
  if (markdownText === null || markdownText === undefined) return "";
  if (typeof marked !== "undefined") {
    try {
      return marked.parse(markdownText);
    } catch (error) {
      console.error("Markdown render error:", error);
    }
  }
  return escapeHtml(markdownText);
};

if (typeof marked !== "undefined") {
  marked.setOptions({
    breaks: true,
    gfm: true,
    highlight: function (code, lang) {
      if (typeof hljs !== "undefined") {
        try {
          if (lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, { language: lang }).value;
          }
          return hljs.highlightAuto(code).value;
        } catch (e) {
          console.error("Highlight error:", e);
          return code;
        }
      }
      return code;
    },
  });
}

const normalizeStreamChunk = (chunk) => {
  if (chunk === null || chunk === undefined) return "";
  return typeof chunk === "string" ? chunk : String(chunk);
};

const mergeStreamChunk = (current, next) => {
  const nextText = normalizeStreamChunk(next);
  if (!current) return nextText;
  if (!nextText) return current;
  if (nextText.startsWith(current)) return nextText;
  if (current.startsWith(nextText)) return current;
  return current + nextText;
};

const formatDateLabel = (iso) => {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const now = new Date();
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
};

const fetchJson = async (url, options = {}) => {
  const response = await fetch(url, options);
  if (response.status === 401) {
    window.location.href = "/";
    return null;
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.error || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return data;
};

const fetchStreamResponse = async (url, options = {}) => {
  const response = await fetch(url, options);
  if (response.status === 401) {
    window.location.href = "/";
    return null;
  }
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }
  return response;
};

function ChatApp() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(getStoredConversationId());
  const [messages, setMessages] = useState([]);
  const [configs, setConfigs] = useState([]);
  const [configA, setConfigA] = useState("");
  const [configB, setConfigB] = useState("");
  const [abEnabled, setAbEnabled] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const clientIdRef = useRef(getStoredClientId());
  const historyRef = useRef([]);

  const setConversationId = useCallback((value) => {
    setActiveConversationId(value ?? null);
    setStoredConversationId(value ?? null);
  }, []);

  const loadConfigs = useCallback(async () => {
    const data = await fetchJson("/api/get_configs");
    if (!data) return;
    const options = data.options || [];
    setConfigs(options);
    if (!configA && options.length) {
      setConfigA(options[0].name);
    }
    if (!configB && options.length > 1) {
      setConfigB(options[1].name);
    } else if (!configB && options.length === 1) {
      setConfigB(options[0].name);
    }
  }, [configA, configB]);

  const loadConversations = useCallback(async () => {
    const url = `/api/list_conversations?limit=100&client_id=${encodeURIComponent(clientIdRef.current)}`;
    const data = await fetchJson(url);
    if (!data) return;
    setConversations(data.conversations || []);
  }, []);

  const loadConversation = useCallback(async (conversationId) => {
    const data = await fetchJson("/api/load_conversation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        conversation_id: conversationId,
        client_id: clientIdRef.current,
      }),
    });
    if (!data) return;
    const loadedMessages = (data.messages || []).map((msg, idx) => {
      const isUser = msg.sender === "User";
      return {
        id: `${msg.message_id || idx}-${isUser ? "u" : "a"}`,
        sender: msg.sender,
        direction: isUser ? "outgoing" : "incoming",
        markdown: msg.content,
        html: isUser ? escapeHtml(msg.content) : renderMarkdown(msg.content),
      };
    });
    historyRef.current = (data.messages || []).map((msg) => [msg.sender, msg.content]);
    setMessages(loadedMessages);
    setConversationId(conversationId);
  }, [setConversationId]);

  const startNewConversation = useCallback(async () => {
    await fetchJson("/api/new_conversation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_id: clientIdRef.current }),
    });
    historyRef.current = [];
    setMessages([]);
    setConversationId(null);
    loadConversations();
  }, [loadConversations, setConversationId]);

  const addMessage = useCallback((message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const updateMessage = useCallback((messageId, updater) => {
    setMessages((prev) =>
      prev.map((msg) => (msg.id === messageId ? { ...msg, ...updater } : msg))
    );
  }, []);

  const finalizeMarkdown = useCallback(() => {
    if (typeof hljs !== "undefined") {
      setTimeout(() => hljs.highlightAll(), 0);
    }
  }, []);

  const streamResponse = useCallback(
    async ({ configName, label, messageId }) => {
      let streamedText = "";
      try {
        const response = await fetchStreamResponse(STREAM_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            last_message: historyRef.current.slice(-1),
            conversation_id: activeConversationId,
            config_name: configName,
            client_sent_msg_ts: Date.now(),
            client_timeout: 300000,
            client_id: clientIdRef.current,
            include_agent_steps: false,
            include_tool_steps: false,
          }),
        });

        if (!response || !response.body) {
          throw new Error("Streaming response body not available");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop();
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;
            let event;
            try {
              event = JSON.parse(trimmed);
            } catch (error) {
              console.error("Failed to parse stream event:", error);
              continue;
            }
            if (event.type === "chunk" || (event.type === "step" && event.step_type === "agent")) {
              streamedText = mergeStreamChunk(streamedText, event.content);
              updateMessage(messageId, {
                markdown: streamedText,
                html: renderMarkdown(streamedText),
                streaming: true,
              });
            } else if (event.type === "final") {
              const finalText = event.response || streamedText;
              updateMessage(messageId, {
                markdown: finalText,
                html: renderMarkdown(finalText),
                streaming: false,
              });
              if (event.conversation_id !== undefined && event.conversation_id !== null) {
                setConversationId(event.conversation_id);
              }
              historyRef.current.push(["A2rchi", finalText]);
              finalizeMarkdown();
              return;
            } else if (event.type === "error") {
              updateMessage(messageId, {
                markdown: event.message || "Streaming error",
                html: escapeHtml(event.message || "Streaming error"),
                streaming: false,
              });
              finalizeMarkdown();
              return;
            }
          }
        }
      } catch (error) {
        console.error("Streaming failed:", error);
        const message = error && error.message ? error.message : "Streaming failed";
        updateMessage(messageId, {
          markdown: message,
          html: escapeHtml(message),
          streaming: false,
        });
        finalizeMarkdown();
      }
    },
    [activeConversationId, finalizeMarkdown, setConversationId, updateMessage]
  );

  const handleSend = useCallback(
    async (text) => {
      if (!text.trim() || isStreaming) return;
      const userMessage = {
        id: `${Date.now()}-user`,
        sender: "User",
        direction: "outgoing",
        markdown: text,
        html: escapeHtml(text),
      };
      historyRef.current.push(["User", text]);
      addMessage(userMessage);
      setIsStreaming(true);

      const tasks = [];
      const assistantAId = `${Date.now()}-assistant-a`;
      addMessage({
        id: assistantAId,
        sender: "A2rchi",
        direction: "incoming",
        markdown: "",
        html: "",
        label: abEnabled ? `Model A: ${configA}` : null,
      });
      tasks.push(
        streamResponse({
          configName: configA,
          label: "A",
          messageId: assistantAId,
        })
      );

      if (abEnabled && configB) {
        const assistantBId = `${Date.now()}-assistant-b`;
        addMessage({
          id: assistantBId,
          sender: "A2rchi",
          direction: "incoming",
          markdown: "",
          html: "",
          label: `Model B: ${configB}`,
        });
        tasks.push(
          streamResponse({
            configName: configB,
            label: "B",
            messageId: assistantBId,
          })
        );
      }

      try {
        await Promise.all(tasks);
      } catch (error) {
        console.error("Streaming error:", error);
      } finally {
        setIsStreaming(false);
        loadConversations();
      }
    },
    [abEnabled, addMessage, configA, configB, isStreaming, loadConversations, streamResponse]
  );

  useEffect(() => {
    loadConfigs();
    loadConversations();
  }, [loadConfigs, loadConversations]);

  useEffect(() => {
    if (typeof hljs !== "undefined") {
      hljs.highlightAll();
    }
  }, [messages]);

  const conversationItems = useMemo(() => {
    return conversations.map((conv) => html`
      <${Conversation}
        key=${conv.conversation_id}
        name=${conv.title || `Conversation ${conv.conversation_id}`}
        info=${formatDateLabel(conv.last_message_at)}
        active=${conv.conversation_id === activeConversationId}
        onClick=${() => loadConversation(conv.conversation_id)}
      />
    `);
  }, [activeConversationId, conversations, loadConversation]);

  return html`
    <div className="a2rchi-app">
      <${MainContainer}>
        <${Sidebar} position="left" className="a2rchi-sidebar">
          <div className="a2rchi-header">
            <div className="a2rchi-header-title">A2rchi</div>
            <button className="a2rchi-new-chat" onClick=${startNewConversation}>New chat</button>
          </div>
          <${ConversationList}>
            ${conversationItems.length
              ? conversationItems
              : html`<div className="a2rchi-empty">No conversations yet</div>`}
          </${ConversationList}>
        </${Sidebar}>
        <${ChatContainer} className="a2rchi-main">
          <${ConversationHeader}>
            <${ConversationHeader.Content}>
              <div className="a2rchi-header-title">Chat</div>
            </${ConversationHeader.Content}>
          </${ConversationHeader}>
          <div className="a2rchi-header">
            <div className="a2rchi-controls">
              <select className="a2rchi-select" value=${configA} onChange=${(e) => setConfigA(e.target.value)}>
                ${configs.map(
                  (option) => html`<option key=${option.name} value=${option.name}>${option.name}</option>`
                )}
              </select>
              <label className="a2rchi-toggle">
                <input
                  type="checkbox"
                  checked=${abEnabled}
                  onChange=${(e) => setAbEnabled(e.target.checked)}
                />
                A/B testing
              </label>
              ${abEnabled
                ? html`<select className="a2rchi-select" value=${configB} onChange=${(e) => setConfigB(e.target.value)}>
                    ${configs.map(
                      (option) => html`<option key=${option.name} value=${option.name}>${option.name}</option>`
                    )}
                  </select>`
                : null}
            </div>
          </div>
          <${MessageList} typingIndicator=${isStreaming ? html`<${TypingIndicator} content="A2rchi is typing" />` : null}>
            ${messages.map((msg) => html`
              <${Message} key=${msg.id} model=${{ direction: msg.direction, position: "single" }}>
                <${Message.HtmlContent} html=${
                  (msg.label ? `<div class="a2rchi-ab-label"><span class="a2rchi-ab-pill">${escapeHtml(msg.label)}</span></div>` : "") +
                  `<div class="a2rchi-message">${msg.html || ""}</div>`
                } />
              </${Message}>
            `)}
          </${MessageList}>
          <${MessageInput} placeholder="Ask A2rchi..." onSend=${handleSend} attachButton=${false} disabled=${isStreaming} />
        </${ChatContainer}>
      </${MainContainer}>
    </div>
  `;
}

const root = createRoot(document.getElementById("root"));
root.render(html`<${ChatApp} />`);
