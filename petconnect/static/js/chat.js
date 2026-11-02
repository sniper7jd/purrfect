// Conversation page: Ably for live delivery and typing indicators, with an HTTP polling
// fallback so chat keeps working when realtime isn't configured or the connection drops.
(() => {
  const config = JSON.parse(document.getElementById("chat-config").textContent);
  const container = document.getElementById("messages-container");
  const form = document.getElementById("message-form");
  const input = document.getElementById("message-input");
  const typingIndicator = document.getElementById("typing-indicator");
  const readReceipt = document.getElementById("read-receipt");
  const emptyState = document.getElementById("empty-state");
  const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;

  const POLL_INTERVAL_MS = 3000;
  const TYPING_IDLE_MS = 2000;

  const rendered = new Set(
    [...container.querySelectorAll("[data-message-id]")].map((el) => Number(el.dataset.messageId)),
  );
  let lastMessageId = config.lastMessageId;
  let pollTimer = null;
  let typingTimer = null;
  let remoteTypingTimer = null;
  let isTyping = false;
  let typingChannel = null;

  const formatTime = (iso) =>
    new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });

  function scrollToBottom() {
    container.scrollTop = container.scrollHeight;
  }

  function addMessage(message) {
    if (rendered.has(message.id)) return;
    rendered.add(message.id);
    lastMessageId = Math.max(lastMessageId, message.id);
    emptyState?.remove();

    const isOwn = message.sender_id === config.currentUserId;
    const row = document.createElement("div");
    row.className = `flex ${isOwn ? "justify-end" : "justify-start"} animate-fadeIn`;
    row.dataset.messageId = message.id;

    const bubble = document.createElement("div");
    bubble.className = `max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
      isOwn ? "bg-brand text-white" : "bg-gray-100 text-gray-800"
    }`;
    const text = document.createElement("p");
    text.className = "whitespace-pre-wrap break-words";
    text.textContent = message.content;
    const time = document.createElement("p");
    time.className = `text-xs mt-1 ${isOwn ? "text-orange-200" : "text-gray-400"}`;
    time.textContent = formatTime(message.sent_at);

    bubble.append(text, time);
    row.appendChild(bubble);
    container.appendChild(row);
    if (readReceipt) readReceipt.textContent = "";
    scrollToBottom();

    if (!isOwn) markRead();
  }

  async function post(url, data) {
    return fetch(url, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: data,
    });
  }

  function markRead() {
    if (document.visibilityState === "visible") post(config.readUrl).catch(() => {});
  }

  async function fetchNewMessages() {
    const response = await fetch(`${config.messagesUrl}?after=${lastMessageId}`);
    if (!response.ok) return;
    const { messages } = await response.json();
    messages.forEach(addMessage);
  }

  function startPolling() {
    if (pollTimer) return;
    pollTimer = setInterval(() => fetchNewMessages().catch(() => {}), POLL_INTERVAL_MS);
  }

  function stopPolling() {
    clearInterval(pollTimer);
    pollTimer = null;
  }

  function setTyping(active) {
    if (!typingChannel || active === isTyping) return;
    isTyping = active;
    typingChannel.publish("typing", { is_typing: active }).catch(() => {});
  }

  function connectRealtime() {
    const client = new Ably.Realtime({ authUrl: config.tokenUrl, authMethod: "GET" });
    const messages = client.channels.get(config.messageChannel);
    typingChannel = client.channels.get(config.typingChannel);

    messages.subscribe("message", ({ data }) => addMessage(data));
    messages.subscribe("read", ({ data }) => {
      if (data.reader_id !== config.currentUserId && readReceipt) readReceipt.textContent = "Seen";
    });
    typingChannel.subscribe("typing", ({ clientId, data }) => {
      if (clientId === String(config.currentUserId)) return;
      clearTimeout(remoteTypingTimer);
      typingIndicator.textContent = data.is_typing ? `${config.otherUserName} is typing\u2026` : "";
      if (data.is_typing) {
        remoteTypingTimer = setTimeout(() => (typingIndicator.textContent = ""), 5000);
      }
    });

    client.connection.on("connected", () => {
      stopPolling();
      fetchNewMessages().catch(() => {});
    });
    client.connection.on(["disconnected", "suspended", "failed"], startPolling);
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const content = input.value.trim();
    if (!content) return;
    input.value = "";
    setTyping(false);

    const body = new FormData();
    body.set("content", content);
    const response = await post(config.sendUrl, body);
    if (response.ok) {
      const { message } = await response.json();
      addMessage(message);
    } else {
      input.value = content;
      const { error } = await response.json().catch(() => ({}));
      alert(error || "Message failed to send. Please try again.");
    }
  });

  input.addEventListener("input", () => {
    setTyping(input.value.trim().length > 0);
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => setTyping(false), TYPING_IDLE_MS);
  });

  document.addEventListener("visibilitychange", markRead);

  scrollToBottom();
  if (config.realtime && window.Ably) {
    connectRealtime();
  } else {
    startPolling();
  }
})();
