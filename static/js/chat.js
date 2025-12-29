function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {
  const feed = document.getElementById('chat-feed');
  const form = document.getElementById('chat-form');
  if (!feed || !form) return;

  const conversationId = feed.dataset.conversationId;
  const partnerId = feed.dataset.partnerId;
  const csrfToken = getCookie('csrftoken');
  const wsScheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl = `${wsScheme}://${window.location.host}/ws/chat/${conversationId}/`;
  let socket;
  let pollInterval;
  const partnerDot = document.getElementById('partner-status-dot');
  const listDots = document.querySelectorAll('[data-user-dot]');

  const toggleDots = (userId, online) => {
    listDots.forEach((dot) => {
      if (dot.dataset.userId === String(userId)) {
        dot.classList.toggle('hidden', !online);
      }
    });
    if (partnerId && String(userId) === String(partnerId) && partnerDot) {
      partnerDot.classList.toggle('hidden', !online);
    }
  };

  const appendMessage = (msg) => {
    const wrapper = document.createElement('div');
    wrapper.className = `flex ${msg.sent_by_me ? 'justify-end' : ''}`;
    const bubble = document.createElement('div');
    bubble.className = `rounded-2xl px-4 py-2 max-w-xl text-sm ${
      msg.sent_by_me ? 'bg-teal-500 text-white' : 'bg-slate-100 text-slate-800'
    }`;
    bubble.innerHTML = `<p>${msg.body}</p><p class="text-[10px] opacity-70 mt-1">${msg.timestamp}</p>`;
    wrapper.appendChild(bubble);
    feed.appendChild(wrapper);
    feed.scrollTop = feed.scrollHeight;
  };

  const renderMessages = (messages) => {
    feed.innerHTML = '';
    messages.forEach(appendMessage);
  };

  const poll = async () => {
    try {
      const res = await fetch(`/api/messages/${conversationId}/`);
      if (!res.ok) return;
      const data = await res.json();
      renderMessages(data.messages);
    } catch (err) {
      console.error(err);
    }
  };

  const startSocket = () => {
    socket = new WebSocket(wsUrl);
    socket.onopen = () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
      poll(); // load history once on connect
    };
    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.message_type === 'presence') {
          toggleDots(msg.user_id, msg.online);
          return;
        }
        appendMessage(msg);
      } catch (err) {
        console.error(err);
      }
    };
    socket.onclose = () => {
      // fallback to polling if socket closes
      if (!pollInterval) {
        pollInterval = setInterval(poll, 5000);
      }
    };
    socket.onerror = () => {
      if (!pollInterval) {
        pollInterval = setInterval(poll, 5000);
      }
    };
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = form.querySelector('input[name="body"]');
    if (!input.value.trim()) return;
    const body = input.value.trim();
    const sendViaSocket = socket && socket.readyState === WebSocket.OPEN;
    if (sendViaSocket) {
      socket.send(JSON.stringify({ body }));
      input.value = '';
      return;
    }
    // fallback to POST if socket unavailable
    const formData = new FormData();
    formData.append('body', body);
    fetch(`/api/messages/${conversationId}/send/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      body: formData,
    })
      .then(() => {
        input.value = '';
        poll();
      })
      .catch(console.error);
  });

  startSocket();
});
