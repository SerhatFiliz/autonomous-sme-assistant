/**
 * kobi-widget.js — KOBİ-AI Embeddable Chat Widget
 *
 * Drop-in script for any tenant storefront. The host page only needs:
 *   <script src="http://<fastapi-host>/static/kobi-widget.js"
 *           data-api-key="YOUR_KEY" defer></script>
 *
 * The widget:
 *   • Auto-detects its own origin from the script tag's src URL — no hardcoded ports.
 *   • Reads `data-api-key` from its own <script> tag.
 *   • Opens a WebSocket to ws://<detected-host>/api/v1/ws/chat/{api_key}.
 *   • Injects a fully self-contained floating chat UI into the host DOM.
 *   • Streams AI tokens progressively as they arrive.
 *   • Handles reconnection with exponential backoff (1s → 30s max).
 *   • Has zero external dependencies.
 */

(function () {
  "use strict";

  // ---------------------------------------------------------------------------
  // Configuration — resolved dynamically from the script tag's own src attribute.
  // This ensures the widget always connects to the correct FastAPI host/port,
  // regardless of whether it runs on port 8001, 8003, or any discovered port.
  // ---------------------------------------------------------------------------
  const _script = document.currentScript || (function () {
    const scripts = document.getElementsByTagName("script");
    return scripts[scripts.length - 1];
  })();

  const API_KEY = _script.getAttribute("data-api-key") || "demo-tenant-key-123";

  // Dynamically derive the WebSocket host from the script's own src URL.
  // This eliminates ALL hardcoded ports and hostnames.
  let WS_HOST;
  try {
    const srcUrl = new URL(_script.src);
    // Use the same protocol-aware scheme (ws: for http:, wss: for https:)
    const wsScheme = srcUrl.protocol === "https:" ? "wss" : "ws";
    WS_HOST = `${wsScheme}://${srcUrl.host}`;
  } catch (_) {
    // Fallback: honour the explicit data-ws-host attribute, or default.
    const fallback = _script.getAttribute("data-ws-host") || window.location.host;
    WS_HOST = `ws://${fallback}`;
  }

  const WS_URL = `${WS_HOST}/api/v1/ws/chat/${API_KEY}`;

  // ---------------------------------------------------------------------------
  // Inject widget styles into <head>
  // ---------------------------------------------------------------------------
  const STYLES = `
    :root {
      --kobi-primary:     #6C63FF;
      --kobi-primary-dk:  #4B44CC;
      --kobi-accent:      #FF6584;
      --kobi-bg:          #0F0F1A;
      --kobi-surface:     #1A1A2E;
      --kobi-surface2:    #16213E;
      --kobi-border:      rgba(108,99,255,0.25);
      --kobi-text:        #E8E8F0;
      --kobi-muted:       #888AA0;
      --kobi-radius:      16px;
      --kobi-shadow:      0 24px 64px rgba(0,0,0,0.55);
      --kobi-btn-size:    60px;
      --kobi-z:           999999 !important;
    }

    #kobi-toggle-btn {
      position: fixed;
      bottom: 28px;
      right: 28px;
      width: var(--kobi-btn-size);
      height: var(--kobi-btn-size);
      border-radius: 50%;
      background: linear-gradient(135deg, var(--kobi-primary), var(--kobi-accent));
      border: none;
      cursor: pointer;
      z-index: var(--kobi-z) !important;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8px 32px rgba(108,99,255,0.55);
      transition: transform 0.25s cubic-bezier(.34,1.56,.64,1), box-shadow 0.25s;
      outline: none;
    }
    #kobi-toggle-btn:hover {
      transform: scale(1.1);
      box-shadow: 0 12px 40px rgba(108,99,255,0.75);
    }
    #kobi-toggle-btn svg { pointer-events: none; }

    /* Pulsing ring — shows connectivity status */
    #kobi-toggle-btn::before {
      content: '';
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 50%;
      background: var(--kobi-primary);
      opacity: 0;
      animation: kobi-pulse 2.4s ease-out infinite;
    }
    @keyframes kobi-pulse {
      0%   { transform: scale(1);   opacity: 0.6; }
      100% { transform: scale(1.9); opacity: 0;   }
    }

    /* Unread badge */
    #kobi-badge {
      position: absolute;
      top: -4px;
      right: -4px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: var(--kobi-accent);
      color: #fff;
      font-size: 11px;
      font-weight: 700;
      line-height: 20px;
      text-align: center;
      display: none;
      font-family: system-ui, sans-serif;
    }

    /* Chat window */
    #kobi-window {
      position: fixed;
      bottom: 100px;
      right: 28px;
      width: 380px;
      max-width: calc(100vw - 40px);
      height: 560px;
      max-height: calc(100vh - 120px);
      border-radius: var(--kobi-radius);
      background: var(--kobi-bg);
      border: 1px solid var(--kobi-border);
      box-shadow: var(--kobi-shadow);
      display: flex;
      flex-direction: column;
      z-index: var(--kobi-z) !important;
      font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
      transform: translateY(20px) scale(0.95);
      opacity: 0;
      pointer-events: none;
      transition: transform 0.3s cubic-bezier(.34,1.56,.64,1), opacity 0.25s;
      overflow: hidden;
    }
    #kobi-window.kobi-open {
      transform: translateY(0) scale(1);
      opacity: 1;
      pointer-events: all;
    }

    /* Header */
    #kobi-header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px 18px;
      background: linear-gradient(135deg, var(--kobi-surface), var(--kobi-surface2));
      border-bottom: 1px solid var(--kobi-border);
      border-radius: var(--kobi-radius) var(--kobi-radius) 0 0;
      flex-shrink: 0;
    }
    #kobi-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--kobi-primary), var(--kobi-accent));
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    #kobi-header-text { flex: 1; min-width: 0; }
    #kobi-header-title {
      color: var(--kobi-text);
      font-size: 15px;
      font-weight: 700;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    #kobi-status-row {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 2px;
    }
    #kobi-status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #4caf50;
      transition: background 0.3s;
    }
    #kobi-status-dot.kobi-disconnected { background: var(--kobi-accent); }
    #kobi-status-dot.kobi-connecting   { background: #FFC107; }
    #kobi-status-label {
      font-size: 12px;
      color: var(--kobi-muted);
    }
    #kobi-close-btn {
      background: none;
      border: none;
      cursor: pointer;
      color: var(--kobi-muted);
      padding: 4px;
      border-radius: 8px;
      display: flex;
      transition: color 0.2s, background 0.2s;
    }
    #kobi-close-btn:hover { color: var(--kobi-text); background: rgba(255,255,255,0.07); }

    /* Messages area */
    #kobi-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      scrollbar-width: thin;
      scrollbar-color: var(--kobi-border) transparent;
    }
    #kobi-messages::-webkit-scrollbar { width: 4px; }
    #kobi-messages::-webkit-scrollbar-thumb {
      background: var(--kobi-border);
      border-radius: 4px;
    }

    .kobi-msg {
      max-width: 82%;
      padding: 10px 14px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.55;
      word-break: break-word;
      animation: kobi-msg-in 0.25s ease-out;
    }
    @keyframes kobi-msg-in {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0);   }
    }
    .kobi-msg-user {
      align-self: flex-end;
      background: linear-gradient(135deg, var(--kobi-primary), var(--kobi-primary-dk));
      color: #fff;
      border-bottom-right-radius: 4px;
    }
    .kobi-msg-ai {
      align-self: flex-start;
      background: var(--kobi-surface);
      color: var(--kobi-text);
      border: 1px solid var(--kobi-border);
      border-bottom-left-radius: 4px;
    }
    .kobi-msg-ai.kobi-streaming::after {
      content: '\u25cb';
      display: inline-block;
      animation: kobi-blink 0.7s step-end infinite;
      color: var(--kobi-primary);
      margin-left: 2px;
    }
    @keyframes kobi-blink {
      0%, 100% { opacity: 1; }
      50%       { opacity: 0; }
    }

    /* System / error messages */
    .kobi-msg-system {
      align-self: center;
      background: rgba(255,101,132,0.12);
      color: var(--kobi-accent);
      border: 1px solid rgba(255,101,132,0.25);
      font-size: 12px;
      text-align: center;
      padding: 8px 14px;
      border-radius: 10px;
    }

    /* Typing indicator (three dots) */
    #kobi-typing {
      align-self: flex-start;
      display: none;
      gap: 5px;
      padding: 10px 14px;
      background: var(--kobi-surface);
      border: 1px solid var(--kobi-border);
      border-radius: 14px;
      border-bottom-left-radius: 4px;
    }
    #kobi-typing span {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--kobi-primary);
      animation: kobi-bounce 1.2s infinite;
    }
    #kobi-typing span:nth-child(2) { animation-delay: 0.2s; }
    #kobi-typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes kobi-bounce {
      0%, 60%, 100% { transform: translateY(0);   }
      30%            { transform: translateY(-6px); }
    }

    /* Input area */
    #kobi-input-area {
      display: flex;
      align-items: flex-end;
      gap: 10px;
      padding: 14px 16px;
      border-top: 1px solid var(--kobi-border);
      background: var(--kobi-surface2);
      border-radius: 0 0 var(--kobi-radius) var(--kobi-radius);
      flex-shrink: 0;
    }
    #kobi-input {
      flex: 1;
      background: var(--kobi-bg);
      border: 1px solid var(--kobi-border);
      border-radius: 12px;
      color: var(--kobi-text);
      font-size: 14px;
      padding: 10px 14px;
      resize: none;
      outline: none;
      min-height: 42px;
      max-height: 110px;
      overflow-y: auto;
      line-height: 1.4;
      transition: border-color 0.2s;
      font-family: inherit;
    }
    #kobi-input::placeholder { color: var(--kobi-muted); }
    #kobi-input:focus { border-color: var(--kobi-primary); }
    #kobi-send-btn {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--kobi-primary), var(--kobi-primary-dk));
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: transform 0.2s, box-shadow 0.2s;
      box-shadow: 0 4px 16px rgba(108,99,255,0.4);
    }
    #kobi-send-btn:hover:not(:disabled) {
      transform: scale(1.08);
      box-shadow: 0 6px 20px rgba(108,99,255,0.6);
    }
    #kobi-send-btn:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    /* Powered-by footer */
    #kobi-footer {
      padding: 6px 0 2px;
      text-align: center;
      font-size: 10px;
      color: var(--kobi-muted);
      letter-spacing: 0.03em;
      flex-shrink: 0;
      border-top: 1px solid var(--kobi-border);
      background: var(--kobi-surface2);
      border-radius: 0 0 var(--kobi-radius) var(--kobi-radius);
    }
    #kobi-footer a {
      color: var(--kobi-primary);
      text-decoration: none;
    }
  `;

  // ---------------------------------------------------------------------------
  // Inject the style block
  // ---------------------------------------------------------------------------
  const styleEl = document.createElement("style");
  styleEl.id = "kobi-widget-styles";
  styleEl.textContent = STYLES;
  document.head.appendChild(styleEl);

  // ---------------------------------------------------------------------------
  // Build DOM
  // ---------------------------------------------------------------------------

  // Toggle button
  const toggleBtn = document.createElement("button");
  toggleBtn.id = "kobi-toggle-btn";
  toggleBtn.setAttribute("aria-label", "Open AI Assistant");
  toggleBtn.innerHTML = `
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  `;
  const badge = document.createElement("span");
  badge.id = "kobi-badge";
  badge.textContent = "1";
  toggleBtn.appendChild(badge);

  // Chat window
  const chatWindow = document.createElement("div");
  chatWindow.id = "kobi-window";
  chatWindow.setAttribute("role", "dialog");
  chatWindow.setAttribute("aria-label", "KOBI-AI Chat");
  chatWindow.innerHTML = `
    <div id="kobi-header">
      <div id="kobi-avatar">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2"
             stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="8" r="4"/>
          <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
        </svg>
      </div>
      <div id="kobi-header-text">
        <div id="kobi-header-title">KOBI-AI Assistant</div>
        <div id="kobi-status-row">
          <div id="kobi-status-dot" class="kobi-connecting"></div>
          <span id="kobi-status-label">Connecting...</span>
        </div>
      </div>
      <button id="kobi-close-btn" aria-label="Close chat">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2.5" stroke-linecap="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
    <div id="kobi-messages">
      <div class="kobi-msg kobi-msg-ai">
        Hello! I'm <strong>KOBI-AI</strong>, your intelligent shopping assistant.
        Ask me anything about products, orders, or the store!
      </div>
      <div id="kobi-typing">
        <span></span><span></span><span></span>
      </div>
    </div>
    <div id="kobi-input-area">
      <textarea
        id="kobi-input"
        placeholder="Type a message..."
        rows="1"
        aria-label="Chat message input"
      ></textarea>
      <button id="kobi-send-btn" aria-label="Send message">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff"
             stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
      </button>
    </div>
    <div id="kobi-footer">Powered by <a href="#" tabindex="-1">KOBI-AI</a></div>
  `;

  // Append to body once DOM is ready.
  function mountWidget() {
    if (document.getElementById('kobi-ai-widget-container')) return;
    
    const container = document.createElement("div");
    container.id = "kobi-ai-widget-container";
    container.appendChild(toggleBtn);
    container.appendChild(chatWindow);
    document.body.appendChild(container);
    
    initWidget();
  }
  window.initWidget = initWidget;
  window.mountWidget = mountWidget;

  // ---------------------------------------------------------------------------
  // Widget logic
  // ---------------------------------------------------------------------------
  function initWidget() {
    const messagesEl  = document.getElementById("kobi-messages");
    const inputEl     = document.getElementById("kobi-input");
    const sendBtn     = document.getElementById("kobi-send-btn");
    const closeBtn    = document.getElementById("kobi-close-btn");
    const statusDot   = document.getElementById("kobi-status-dot");
    const statusLabel = document.getElementById("kobi-status-label");
    const typingEl    = document.getElementById("kobi-typing");

    let ws             = null;
    let isOpen         = false;
    let isStreaming    = false;
    let currentAiEl   = null;
    let reconnectDelay = 1000;   // Initial backoff: 1 second
    let reconnectTimer = null;

    // --- WebSocket status helper ---
    function setStatus(state) {
      const map = {
        connected:    ["",                  "Online",         false],
        disconnected: ["kobi-disconnected", "Offline",        true],
        connecting:   ["kobi-connecting",   "Connecting...",  true],
      };
      const [cls, label, isDc] = map[state] || map.disconnected;
      statusDot.className = cls ? `kobi-status-dot ${cls}` : "";
      statusDot.id = "kobi-status-dot"; // preserve id after className reset
      statusLabel.textContent = label;
      sendBtn.disabled = isDc;
    }

    // --- Exponential backoff reconnect ---
    function scheduleReconnect() {
      if (reconnectTimer) return; // already scheduled
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        reconnectDelay = Math.min(reconnectDelay * 2, 30000); // cap at 30 s
        connectWS();
      }, reconnectDelay);
    }

    function connectWS() {
      if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) return;
      setStatus("connecting");
      try {
        ws = new WebSocket(WS_URL);
      } catch (err) {
        setStatus("disconnected");
        scheduleReconnect();
        return;
      }

      ws.onopen = () => {
        reconnectDelay = 1000; // reset backoff on successful connection
        setStatus("connected");
      };

      ws.onmessage = (evt) => {
        const data = evt.data;

        if (data === "__END__") {
          // Streaming complete — remove the blinking cursor.
          if (currentAiEl) {
            currentAiEl.classList.remove("kobi-streaming");
            currentAiEl = null;
          }
          isStreaming = false;
          sendBtn.disabled = false;
          typingEl.style.display = "none";
          return;
        }

        if (!currentAiEl) {
          // First chunk — create the AI bubble.
          typingEl.style.display = "none";
          currentAiEl = appendMessage("", "ai", true);
          currentAiEl.dataset.raw = "";
        }
        // Append token to the current bubble and parse simple markdown
        currentAiEl.dataset.raw += data;
        let parsedHTML = currentAiEl.dataset.raw
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="display:inline-block; margin-top:8px; padding:8px 12px; background:var(--kobi-primary); color:#fff; text-decoration:none; border-radius:8px; font-weight:600; text-align:center;">📦 View $1</a><br>');
        currentAiEl.innerHTML = parsedHTML;
        scrollToBottom();
      };

      ws.onclose = () => {
        setStatus("disconnected");
        isStreaming = false;
        sendBtn.disabled = true;
        scheduleReconnect();
      };

      ws.onerror = () => ws.close();
    }

    // --- DOM helpers ---
    function appendMessage(text, type, streaming = false) {
      const msgEl = document.createElement("div");
      msgEl.className = `kobi-msg kobi-msg-${type}`;
      if (streaming) msgEl.classList.add("kobi-streaming");
      msgEl.textContent = text;
      // Insert before the typing indicator to keep order correct.
      messagesEl.insertBefore(msgEl, typingEl);
      scrollToBottom();
      return msgEl;
    }

    function scrollToBottom() {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    // --- Send message ---
    function sendMessage() {
      const text = inputEl.value.trim();
      if (!text || isStreaming || !ws || ws.readyState !== WebSocket.OPEN) return;

      appendMessage(text, "user");
      inputEl.value = "";
      inputEl.style.height = "auto";
      currentAiEl = null;
      isStreaming = true;
      sendBtn.disabled = true;

      // Show typing indicator.
      typingEl.style.display = "flex";
      scrollToBottom();

      ws.send(text);

      // Hide badge when user is actively chatting.
      badge.style.display = "none";
    }

    // --- Auto-resize textarea ---
    inputEl.addEventListener("input", () => {
      inputEl.style.height = "auto";
      inputEl.style.height = Math.min(inputEl.scrollHeight, 110) + "px";
    });

    // --- Event listeners ---
    sendBtn.addEventListener("click", sendMessage);
    inputEl.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    toggleBtn.addEventListener("click", () => {
      isOpen = !isOpen;
      chatWindow.classList.toggle("kobi-open", isOpen);
      toggleBtn.setAttribute("aria-label", isOpen ? "Close AI Assistant" : "Open AI Assistant");
      if (isOpen) {
        badge.style.display = "none";
        inputEl.focus();
      }
    });

    closeBtn.addEventListener("click", () => {
      isOpen = false;
      chatWindow.classList.remove("kobi-open");
      toggleBtn.setAttribute("aria-label", "Open AI Assistant");
    });

    // Start WebSocket connection.
    connectWS();

    // Show unread badge after 3 s if the user has not opened the widget.
    setTimeout(() => {
      if (!isOpen) badge.style.display = "block";
    }, 3000);
  }

  // ---------------------------------------------------------------------------
  // Boot
  // ---------------------------------------------------------------------------
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountWidget);
  } else {
    mountWidget();
  }

  window.onload = () => { 
    if(!document.getElementById('kobi-ai-widget-container')) { 
      mountWidget(); 
    } 
  };
})();
