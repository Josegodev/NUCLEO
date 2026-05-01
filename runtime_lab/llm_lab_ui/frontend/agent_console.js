const form = document.getElementById('agent-form');
const statusPill = document.getElementById('status-pill');
const responseStatus = document.getElementById('response-status');
const responseOutput = document.getElementById('response-output');
const proposalOutput = document.getElementById('proposal-output');
const rawOutput = document.getElementById('raw-output');
const messageLine = document.getElementById('message-line');
const runButton = document.getElementById('run-button');
const approvalActions = document.getElementById('approval-actions');
const approveButton = document.getElementById('approve-button');
const rejectButton = document.getElementById('reject-button');

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

let lastAgentResponse = null;

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

function approvalPayload(approved) {
  return {
    trace_id: lastAgentResponse.trace_id,
    approved,
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
  lastAgentResponse = result;
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
  updateApprovalActions();
}

function renderApproval(result) {
  setPill(statusPill, result.execution_state || result.status || 'unknown', result.status);
  setPill(responseStatus, result.status || 'unknown', result.status);
  responseOutput.textContent = pretty({
    execution_state: result.execution_state,
    executed: result.executed,
    tool: result.tool,
    reason: result.reason,
  });
  rawOutput.textContent = pretty(result);
  approvalActions.classList.add('hidden');
}

function renderError(error) {
  lastAgentResponse = null;
  setPill(statusPill, 'error', 'error');
  setPill(responseStatus, 'error', 'error');
  responseOutput.textContent = error.message;
  proposalOutput.textContent = '{}';
  rawOutput.textContent = '';
  fields.backendUsed.textContent = '-';
  fields.modelUsed.textContent = '-';
  fields.latencyMs.textContent = '-';
  approvalActions.classList.add('hidden');
}

function updateApprovalActions() {
  const body = lastAgentResponse?.result || {};
  const canApprove = Boolean(
    lastAgentResponse?.trace_id
      && body.proposal
      && body.executed === false
      && body.execution_allowed === false,
  );
  approvalActions.classList.toggle('hidden', !canApprove);
}

async function submitApproval(approved) {
  if (!lastAgentResponse?.trace_id) return;

  approveButton.disabled = true;
  rejectButton.disabled = true;
  messageLine.textContent = approved ? 'Approving...' : 'Rejecting...';

  try {
    const response = await fetch(`${fields.apiBase.value.replace(/\/+$/, '')}/agent/approve`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${fields.apiKey.value}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(approvalPayload(approved)),
    });
    const text = await response.text();
    const body = text ? JSON.parse(text) : {};
    if (!response.ok) {
      throw new Error(body.detail || text || `HTTP ${response.status}`);
    }
    renderApproval(body);
    messageLine.textContent = `approval state: ${body.execution_state || '-'}`;
  } catch (error) {
    messageLine.textContent = error.message;
  } finally {
    approveButton.disabled = false;
    rejectButton.disabled = false;
  }
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

approveButton.addEventListener('click', () => submitApproval(true));
rejectButton.addEventListener('click', () => submitApproval(false));

restoreForm();
