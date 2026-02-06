const API = '';

function el(id) {
  return document.getElementById(id);
}

async function getStatus() {
  const res = await fetch(`${API}/api/status`);
  if (!res.ok) throw new Error('Status failed');
  return res.json();
}

async function getState() {
  const res = await fetch(`${API}/api/state`);
  if (!res.ok) return null;
  const data = await res.json();
  return data;
}

async function simulateIncident() {
  const btn = el('simulateBtn');
  btn.disabled = true;
  btn.textContent = 'Running…';
  try {
    const res = await fetch(`${API}/api/simulate-incident`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    const state = await res.json();
    renderDashboard(state);
    return state;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Simulate incident';
  }
}

function renderDashboard(state) {
  const statusBar = el('statusBar');
  const statusText = el('statusText');
  const verdictCard = el('verdictCard');
  const verdictText = el('verdictText');
  const rcaContent = el('rcaContent');

  const feedList = el('feedList');
  if (!state) {
    statusBar.className = 'status-bar';
    statusText.textContent = 'No investigation yet';
    verdictText.textContent = 'Run an investigation to see the verdict.';
    verdictCard.classList.remove('rollback');
    rcaContent.innerHTML = '<p class="muted">No report yet.</p>';
    feedList.innerHTML = '';
    return;
  }

  statusBar.classList.add('incident');
  statusBar.classList.remove('ok');
  statusText.textContent = 'Incident investigated';

  const rec = state.recommendation || '';
  const isRollback = rec.includes('ROLLBACK');
  verdictCard.classList.toggle('rollback', isRollback);
  verdictText.textContent = rec || 'No recommendation yet.';
  if (state.root_cause) {
    verdictText.textContent += ` Root cause: ${state.root_cause}.`;
  }
  if (state.confidence_score != null) {
    verdictText.textContent += ` Confidence: ${Math.round(state.confidence_score * 100)}%.`;
  }

  if (state.rca_report) {
    rcaContent.textContent = state.rca_report;
  } else {
    rcaContent.innerHTML = '<p class="muted">No report yet.</p>';
  }

  feedList.innerHTML = '';
  (state.agent_messages || []).forEach((msg) => {
    const li = document.createElement('li');
    li.textContent = msg;
    feedList.appendChild(li);
  });
}

async function refreshDashboard() {
  const state = await getState();
  renderDashboard(state);
}

function addChatMessage(role, content) {
  const container = el('chatMessages');
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  div.textContent = content;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

async function sendQuery(message) {
  addChatMessage('user', message);
  const input = el('chatInput');
  input.disabled = true;
  try {
    const res = await fetch(`${API}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      addChatMessage('assistant', `Error: ${err.detail || res.statusText}`);
      return;
    }
    const data = await res.json();
    addChatMessage('assistant', data.response || 'No response.');
    refreshDashboard();
  } finally {
    input.disabled = false;
    input.focus();
  }
}

function init() {
  getStatus().then((s) => {
    const statusBar = el('statusBar');
    const statusText = el('statusText');
    if (s.triggered || s.has_state) {
      statusBar.classList.add('incident');
      statusText.textContent = 'Incident detected / investigated';
    } else {
      statusBar.classList.add('ok');
      statusText.textContent = 'Monitoring (threshold 2000 ms)';
    }
  }).catch(() => {
    el('statusText').textContent = 'Could not reach server';
  });

  refreshDashboard();

  el('simulateBtn').addEventListener('click', () => {
    simulateIncident();
  });

  el('chatForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const input = el('chatInput');
    const msg = input.value.trim();
    if (!msg) return;
    input.value = '';
    sendQuery(msg);
  });
}

init();
