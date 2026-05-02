const API_URL = 'http://127.0.0.1:8000/agent/run';
const API_KEY_STORAGE_KEY = 'nucleo_runtime_audit.api_key';

let selectedModel = null;
let dryRun = true;
let input = '';
let apiKey = '';

const nodes = {
  input: document.getElementById('input'),
  apiKey: document.getElementById('apiKey'),
  rememberApiKey: document.getElementById('rememberApiKey'),
  dryRun: document.getElementById('dryRun'),
  runButton: document.getElementById('runButton'),
  modelTabs: Array.from(document.querySelectorAll('.model-tab')),
  statusPill: document.getElementById('status-pill'),
  statusLog: document.getElementById('statusLog'),
  payloadPreview: document.getElementById('payloadPreview'),
  errorPanel: document.getElementById('errorPanel'),
  errorOutput: document.getElementById('errorOutput'),
  augmentationPanel: document.getElementById('augmentationPanel'),
  augmentationBadge: document.getElementById('augmentationBadge'),
  selectedModelOutput: document.getElementById('selectedModelOutput'),
  augmentationModel: document.getElementById('augmentationModel'),
  augmentationModelUsed: document.getElementById('augmentationModelUsed'),
  augmentationFallback: document.getElementById('augmentationFallback'),
  augmentationFallbackReason: document.getElementById('augmentationFallbackReason'),
  augmentationProposal: document.getElementById('augmentationProposal'),
  plannerOutput: document.getElementById('plannerOutput'),
  policyBadge: document.getElementById('policyBadge'),
  policyDecision: document.getElementById('policyDecision'),
  policyOutput: document.getElementById('policyOutput'),
  executionPanel: document.getElementById('executionPanel'),
  executionBadge: document.getElementById('executionBadge'),
  executionExecuted: document.getElementById('executionExecuted'),
  executionDryRun: document.getElementById('executionDryRun'),
  executionTool: document.getElementById('executionTool'),
  executionOutput: document.getElementById('executionOutput'),
  rawOutput: document.getElementById('rawOutput'),
};

function setModel(modelId) {
  selectedModel = modelId || null;

  nodes.modelTabs.forEach((button) => {
    const isActive = (button.dataset.model || null) === selectedModel;
    button.classList.toggle('active', isActive);
    button.setAttribute('aria-selected', String(isActive));
  });

  updatePayloadPreview();
}

function syncState() {
  input = nodes.input.value.trim();
  apiKey = nodes.apiKey.value.trim();
  dryRun = nodes.dryRun.checked;
}

function buildPayload() {
  syncState();

  return {
    input,
    agent_mode: 'proposal_only',
    dry_run: dryRun,
    augmentation: selectedModel ? { model_id: selectedModel } : undefined,
  };
}

function buildHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  const authorization = normalizeAuthorization(apiKey);

  if (authorization) {
    headers.Authorization = authorization;
  }

  return headers;
}

function normalizeAuthorization(value) {
  const token = value.trim();

  if (!token) {
    return null;
  }

  if (token.toLowerCase().startsWith('bearer ')) {
    return `Bearer ${token.slice(7).trim()}`;
  }

  return `Bearer ${token}`;
}

async function run() {
  const payload = buildPayload();
  updatePayloadPreview();
  persistApiKeyPreference();
  resetError();
  resetRender();

  if (!payload.input) {
    showError('invalid_input', 'input must not be empty');
    return;
  }

  nodes.runButton.disabled = true;
  setStatus('running', 'status-running');
  logStatus(`POST ${API_URL}`);

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(payload),
    });

    const text = await response.text();
    let data;

    try {
      data = text ? JSON.parse(text) : null;
    } catch (error) {
      showError('invalid_json', {
        status: response.status,
        statusText: response.statusText,
        body: text,
        parserError: error.message,
      });
      return;
    }

    render(data);

    if (!response.ok) {
      if (response.status === 401) {
        showError('unauthorized', 'Unauthorized: missing or invalid API key');
        return;
      }

      showError('http_error', {
        status: response.status,
        statusText: response.statusText,
        response: data,
      });
      return;
    }

    setStatus('ok', 'status-ok');
    logStatus(`HTTP ${response.status} ${response.statusText || 'OK'}`);
  } catch (error) {
    showError('backend_unreachable', error.message || String(error));
  } finally {
    nodes.runButton.disabled = false;
  }
}

function render(data) {
  const sections = extractSections(data);

  renderAugmentation(sections.augmentation);
  renderPlanner(sections.planner);
  renderPolicy(sections.policy);
  renderExecution(sections.execution);
  setJson(nodes.rawOutput, data);
}

function extractSections(data) {
  const result = objectOrEmpty(data?.result);
  const metadata = objectOrEmpty(result.metadata);
  const proposal = metadata.proposal || result.proposal || null;

  return {
    augmentation: {
      selected_model: selectedModel || 'default',
      model_id: metadata.model_id || result.model_id || selectedModel || null,
      model_used: metadata.model_used || result.model_used || null,
      backend_used: metadata.backend_used || result.backend_used || metadata.backend || null,
      fallback_used: metadata.fallback_used ?? result.fallback_used ?? null,
      fallback_reason: metadata.fallback_reason ?? result.fallback_reason ?? null,
      validation_errors: metadata.validation_errors || result.validation_errors || [],
      proposal,
      model_output: metadata.model_output || result.model_output || null,
    },
    planner:
      data?.planned_action ||
      result.planned_action ||
      metadata.planned_action ||
      buildPlannerSummary(result, proposal),
    policy:
      data?.policy_decision ||
      result.policy_decision ||
      result.policy_decision_initial ||
      metadata.policy_decision ||
      null,
    execution: {
      status: data?.status || null,
      executed: result.executed ?? null,
      dry_run: result.dry_run ?? dryRun,
      execution_allowed: result.execution_allowed ?? null,
      execution_state: result.execution_state || null,
      tool: result.tool || null,
      payload: result.payload || null,
      result,
      errors: data?.errors || [],
    },
  };
}

function buildPlannerSummary(result, proposal) {
  if (!result.tool && !result.payload && !proposal) {
    return null;
  }

  return {
    tool_name: result.tool || proposal?.suggested_action || null,
    payload: result.payload || proposal?.arguments || null,
    proposal,
  };
}

function renderAugmentation(augmentation) {
  const fallbackUsed = Boolean(augmentation.fallback_used);

  nodes.augmentationPanel.classList.toggle('panel-fallback', fallbackUsed);
  setBadge(
    nodes.augmentationBadge,
    fallbackUsed ? 'fallback' : 'ready',
    fallbackUsed ? 'pill-red' : 'pill-yellow',
  );

  setText(nodes.selectedModelOutput, augmentation.selected_model);
  setText(nodes.augmentationModel, augmentation.model_id);
  setText(nodes.augmentationModelUsed, augmentation.model_used || augmentation.backend_used);
  setText(nodes.augmentationFallback, augmentation.fallback_used);
  setText(nodes.augmentationFallbackReason, augmentation.fallback_reason);
  setJson(nodes.augmentationProposal, {
    proposal: augmentation.proposal,
    model_output: augmentation.model_output,
    validation_errors: augmentation.validation_errors,
  });
}

function renderPlanner(planner) {
  setJson(nodes.plannerOutput, planner);
}

function renderPolicy(policy) {
  const rawDecision = policy?.decision;
  const decision = typeof rawDecision === 'string' ? rawDecision.toUpperCase() : null;

  setText(nodes.policyDecision, decision);
  setJson(nodes.policyOutput, policy);

  if (decision === 'ALLOW') {
    setBadge(nodes.policyBadge, 'ALLOW', 'pill-green');
  } else if (decision === 'DENY') {
    setBadge(nodes.policyBadge, 'DENY', 'pill-red');
  } else {
    setBadge(nodes.policyBadge, 'unknown', 'pill-neutral');
  }
}

function renderExecution(execution) {
  const executed = Boolean(execution.executed);
  const isDryRun = Boolean(execution.dry_run);

  nodes.executionPanel.classList.toggle('panel-execution', executed);
  nodes.executionPanel.classList.toggle('panel-dry-run', !executed && isDryRun);

  setText(nodes.executionExecuted, execution.executed);
  setText(nodes.executionDryRun, execution.dry_run);
  setText(nodes.executionTool, execution.tool);
  setJson(nodes.executionOutput, {
    status: execution.status,
    execution_allowed: execution.execution_allowed,
    execution_state: execution.execution_state,
    payload: execution.payload,
    result: execution.result,
    errors: execution.errors,
  });

  if (executed) {
    setBadge(nodes.executionBadge, 'executed', 'pill-green');
  } else if (isDryRun) {
    setBadge(nodes.executionBadge, 'dry_run', 'pill-blue');
  } else {
    setBadge(nodes.executionBadge, 'not executed', 'pill-neutral');
  }
}

function resetRender() {
  nodes.augmentationPanel.classList.remove('panel-fallback');
  nodes.executionPanel.classList.remove('panel-execution', 'panel-dry-run');
  setBadge(nodes.augmentationBadge, 'pending', 'pill-yellow');
  setText(nodes.selectedModelOutput, selectedModel || 'default');
  setText(nodes.augmentationModel, '-');
  setText(nodes.augmentationModelUsed, '-');
  setText(nodes.augmentationFallback, '-');
  setText(nodes.augmentationFallbackReason, '-');
  setJson(nodes.augmentationProposal, null);
  setJson(nodes.plannerOutput, null);
  setBadge(nodes.policyBadge, 'unknown', 'pill-neutral');
  setText(nodes.policyDecision, '-');
  setJson(nodes.policyOutput, null);
  setBadge(nodes.executionBadge, 'unknown', 'pill-neutral');
  setText(nodes.executionExecuted, '-');
  setText(nodes.executionDryRun, '-');
  setText(nodes.executionTool, '-');
  setJson(nodes.executionOutput, null);
  setJson(nodes.rawOutput, null);
}

function resetError() {
  nodes.errorPanel.classList.add('hidden');
  nodes.errorOutput.textContent = '';
}

function showError(kind, detail) {
  nodes.errorPanel.classList.remove('hidden');
  nodes.errorOutput.textContent = stringify({ kind, detail });
  setStatus('error', 'status-error');
  logStatus(`ERROR ${kind}`);
}

function updatePayloadPreview() {
  nodes.payloadPreview.textContent = stringify(buildPayload());
}

function persistApiKeyPreference() {
  apiKey = nodes.apiKey.value.trim();

  try {
    if (nodes.rememberApiKey.checked) {
      if (apiKey) {
        localStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
      } else {
        localStorage.removeItem(API_KEY_STORAGE_KEY);
      }
      return;
    }

    localStorage.removeItem(API_KEY_STORAGE_KEY);
  } catch (error) {
    logStatus('localStorage unavailable');
  }
}

function restoreApiKeyPreference() {
  let storedApiKey;

  try {
    storedApiKey = localStorage.getItem(API_KEY_STORAGE_KEY);
  } catch (error) {
    return;
  }

  if (!storedApiKey) {
    return;
  }

  nodes.apiKey.value = storedApiKey;
  nodes.rememberApiKey.checked = true;
}

function logStatus(message) {
  const time = new Date().toLocaleTimeString();
  nodes.statusLog.textContent = `${nodes.statusLog.textContent}[${time}] ${message}\n`;
  nodes.statusLog.scrollTop = nodes.statusLog.scrollHeight;
}

function setStatus(label, className) {
  nodes.statusPill.className = `status ${className}`;
  nodes.statusPill.textContent = label;
}

function setBadge(node, label, className) {
  node.className = `pill ${className}`;
  node.textContent = label;
}

function setText(node, value) {
  node.textContent = value === null || value === undefined || value === '' ? '-' : String(value);
}

function setJson(node, value) {
  node.textContent = value === null || value === undefined ? '-' : stringify(value);
}

function stringify(value) {
  return JSON.stringify(value, null, 2);
}

function objectOrEmpty(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
}

nodes.runButton.addEventListener('click', run);
nodes.input.addEventListener('input', updatePayloadPreview);
nodes.apiKey.addEventListener('input', () => {
  syncState();
  persistApiKeyPreference();
});
nodes.rememberApiKey.addEventListener('change', persistApiKeyPreference);
nodes.dryRun.addEventListener('change', updatePayloadPreview);
nodes.modelTabs.forEach((button) => {
  button.addEventListener('click', () => setModel(button.dataset.model));
});

restoreApiKeyPreference();
setModel(null);
resetRender();
logStatus('idle');
