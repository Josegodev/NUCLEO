const form = document.getElementById('agent-form');
const statusPill = document.getElementById('status-pill');
const responseStatus = document.getElementById('response-status');
const responseOutput = document.getElementById('response-output');
const proposalOutput = document.getElementById('proposal-output');
const rawOutput = document.getElementById('raw-output');
const messageLine = document.getElementById('message-line');
const runButton = document.getElementById('run-button');

const fields = {
  apiBase: document.getElementById('api-base'),
  apiKey: document.getElementById('api-key'),
  backend: document.getElementById('backend'),
  modelId: document.getElementById('model-id'),
  message: document.getElementById('message'),
  backendUsed: document.getElementById('backend-used'),
  modelUsed: document.getElementById('model-used'),
  latencyMs: document.getElementById('latency-ms'),
};

function setPill(element, text, state = '') {
  element.className = `pill ${state}`.trim();
  element.textContent = text;
}

function pretty(value) {
  return JSON.stringify(value ?? {}, null, 2);
}

function endpoint() {
  return `${fields.apiBase.value.replace(/\/+$/, '')}/agent/run`;
}

function requestPayload() {
  return {
    input: fields.message.value,
    context: {},
    options: {
      backend: fields.backend.value,
      model_id: fields.modelId.value,
      agent_mode: 'proposal_only',
      dry_run: true,
    },
  };
}

function persistForm() {
  localStorage.setItem('agent_console.api_base', fields.apiBase.value);
  localStorage.setItem('agent_console.api_key', fields.apiKey.value);
  localStorage.setItem('agent_console.backend', fields.backend.value);
  localStorage.setItem('agent_console.model_id', fields.modelId.value);
}

function restoreForm() {
  fields.apiBase.value = localStorage.getItem('agent_console.api_base') || fields.apiBase.value;
  fields.apiKey.value = localStorage.getItem('agent_console.api_key') || fields.apiKey.value;
  fields.backend.value = localStorage.getItem('agent_console.backend') || fields.backend.value;
  fields.modelId.value = localStorage.getItem('agent_console.model_id') || fields.modelId.value;
}

function renderResult(result) {
  const body = result.result || {};
  const state = result.status === 'success' ? 'success' : result.status;
  setPill(statusPill, result.status || 'unknown', state);
  setPill(responseStatus, result.status || 'unknown', state);

  responseOutput.textContent = body.model_output || pretty({
    executed: body.executed,
    tool: body.tool,
    payload: body.payload,
  });
  proposalOutput.textContent = pretty(body.proposal || {});
  rawOutput.textContent = pretty(result);
  fields.backendUsed.textContent = body.backend_used || '-';
  fields.modelUsed.textContent = body.model_used || '-';
  fields.latencyMs.textContent = body.latency_ms ?? '-';
}

function renderError(error) {
  setPill(statusPill, 'error', 'error');
  setPill(responseStatus, 'error', 'error');
  responseOutput.textContent = error.message;
  proposalOutput.textContent = '{}';
  rawOutput.textContent = '';
  fields.backendUsed.textContent = '-';
  fields.modelUsed.textContent = '-';
  fields.latencyMs.textContent = '-';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  persistForm();
  runButton.disabled = true;
  messageLine.textContent = 'Running...';
  setPill(statusPill, 'running');
  setPill(responseStatus, 'pending');

  try {
    const response = await fetch(endpoint(), {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${fields.apiKey.value}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestPayload()),
    });
    const text = await response.text();
    const body = text ? JSON.parse(text) : {};
    if (!response.ok) {
      throw new Error(body.detail || text || `HTTP ${response.status}`);
    }
    renderResult(body);
    messageLine.textContent = `trace_id: ${body.trace_id || '-'}`;
  } catch (error) {
    renderError(error);
    messageLine.textContent = error.message;
  } finally {
    runButton.disabled = false;
  }
});

restoreForm();
