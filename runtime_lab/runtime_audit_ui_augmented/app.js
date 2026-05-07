async function run() {
  const input = document.getElementById("input").value;
  const dryRun = document.getElementById("dryRun").checked;

  const payload = {
    input: input,
    agent_mode: "proposal_only",
    dry_run: dryRun
  };

  const res = await fetch("http://127.0.0.1:8000/agent/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await res.json();

  render(data);
}


document.getElementById("augmentation").textContent =
  JSON.stringify({
    model_id: result.augmentation?.model_id,
    ...result.augmentation
  }, null, 2);
const model = document.getElementById("model").value;

const payload = {
  input: input,
  agent_mode: "proposal_only",
  dry_run: dryRun,
  augmentation: model ? { model_id: model } : undefined
};

function render(data) {
  document.getElementById("raw").textContent =
    JSON.stringify(data, null, 2);

  const result = data.result || {};

  // Ajusta estos paths a tu estructura real
  document.getElementById("augmentation").textContent =
    JSON.stringify(result.augmentation || {}, null, 2);

  document.getElementById("planner").textContent =
    JSON.stringify(result.planned_action || {}, null, 2);

  document.getElementById("policy").textContent =
    JSON.stringify(result.policy_decision || {}, null, 2);

  document.getElementById("execution").textContent =
    JSON.stringify(result.execution || {}, null, 2);
}
const API_URL = 'http://127.0.0.1:8000/agent/run';
const REQUEST_TIMEOUT_MS = 15000;

const nodes = {
  userInput: document.getElementById('user-input'),
  dryRun: document.getElementById('dry-run'),
  runButton: document.getElementById('run-button'),
  backendStatus: document.getElementById('backend-status'),
  requestPreview: document.getElementById('request-preview'),
  errorPanel: document.getElementById('error-panel'),
  errorOutput: document.getElementById('error-output'),
  augmentationBadge: document.getElementById('augmentation-badge'),
  augmentationMessage: document.getElementById('augmentation-message'),
  augmentationAction: document.getElementById('augmentation-action'),
  augmentationFallback: document.getElementById('augmentation-fallback'),
  augmentationFallbackReason: document.getElementById('augmentation-fallback-reason'),
  augmentationErrors: document.getElementById('augmentation-errors'),
  plannerOutput: document.getElementById('planner-output'),
  policyBadge: document.getElementById('policy-badge'),
  policyDecision: document.getElementById('policy-decision'),
  policyOutput: document.getElementById('policy-output'),
  executionBadge: document.getElementById('execution-badge'),
  executionExecuted: document.getElementById('execution-executed'),
  executionResult: document.getElementById('execution-result'),
  rawOutput: document.getElementById('raw-output')
};

function buildPayload() {
  return {
    input: nodes.userInput.value.trim(),
    agent_mode: 'proposal_only',
    dry_run: nodes.dryRun.checked
  };
}

function updateRequestPreview() {
  nodes.requestPreview.textContent = stringify(buildPayload());
}

function stringify(value) {
  if (value === undefined) {
    return 'undefined';
  }
  return JSON.stringify(value, null, 2);
}

function setText(node, value) {
  node.textContent = value === null || value === undefined || value === '' ? '-' : String(value);
}

function setJson(node, value) {
  node.textContent = value === undefined ? '-' : stringify(value);
}

function setBadge(node, label, className) {
  node.className = `pill ${className}`;
  node.textContent = label;
}

function setStatus(label, className) {
  nodes.backendStatus.className = `status ${className}`;
  nodes.backendStatus.textContent = label;
}

function resetOutput() {
  nodes.errorPanel.classList.add('hidden');
  nodes.errorOutput.textContent = '';
  setBadge(nodes.augmentationBadge, 'pending', 'pill-yellow');
  setText(nodes.augmentationMessage, '-');
  setJson(nodes.augmentationAction, null);
  setText(nodes.augmentationFallback, '-');
  setText(nodes.augmentationFallbackReason, '-');
  setJson(nodes.augmentationErrors, []);
  setJson(nodes.plannerOutput, null);
  setBadge(nodes.policyBadge, 'unknown', 'pill-neutral');
  setText(nodes.policyDecision, '-');
  setJson(nodes.policyOutput, null);
  setBadge(nodes.executionBadge, 'unknown', 'pill-neutral');
  setText(nodes.executionExecuted, '-');
  setJson(nodes.executionResult, null);
  setJson(nodes.rawOutput, null);
}

function showError(kind, detail) {
  nodes.errorPanel.classList.remove('hidden');
  nodes.errorOutput.textContent = stringify({
    kind,
    detail
  });
  setStatus('error', 'status-error');
}

async function runRequest() {
  const payload = buildPayload();
  updateRequestPreview();
  resetOutput();

  if (!payload.input) {
    showError('invalid_input', 'input must not be empty');
    return;
  }

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  nodes.runButton.disabled = true;
  setStatus('running', 'status-running');

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload),
      signal: controller.signal
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
        parserError: error.message
      });
      return;
    }

    if (!response.ok) {
      renderResponse(data);
      showError('http_error', {
        status: response.status,
        statusText: response.statusText,
        response: data
      });
      return;
    }

    renderResponse(data);
    setStatus('ok', 'status-ok');
  } catch (error) {
    if (error.name === 'AbortError') {
      showError('timeout', `request exceeded ${REQUEST_TIMEOUT_MS}ms`);
      return;
    }

    showError('backend_unreachable', error.message || String(error));
  } finally {
    window.clearTimeout(timeout);
    nodes.runButton.disabled = false;
  }
}

function renderResponse(response) {
  const sections = extractSections(response);
  renderAugmentation(sections.augmentation);
  renderPlanner(sections.plannedAction);
  renderPolicy(sections.policyDecision);
  renderExecution(sections.execution);
  setJson(nodes.rawOutput, response);
}

function extractSections(response) {
  const result = response && typeof response === 'object' ? response.result || {} : {};
  const metadata = result && typeof result === 'object' ? result.metadata || {} : {};

  return {
    augmentation:
      response?.augmentation ||
      result.augmentation ||
      metadata.augmentation ||
      buildAugmentationFromMetadata(result, metadata),
    plannedAction:
      response?.planned_action ||
      result.planned_action ||
      metadata.planned_action ||
      result.plannedAction ||
      null,
    policyDecision:
      response?.policy_decision ||
      result.policy_decision ||
      metadata.policy_decision ||
      null,
    execution:
      response?.execution ||
      result.execution ||
      {
        executed: result.executed,
        dry_run: result.dry_run,
        result
      }
  };
}

function buildAugmentationFromMetadata(result, metadata) {
  const proposal = metadata.proposal || result.proposal || null;

  if (
    !proposal &&
    metadata.fallback_used === undefined &&
    result.fallback_used === undefined
  ) {
    return null;
  }

  return {
    assistant_message: proposal?.intent || null,
    proposed_action: proposal
      ? {
        tool_name: proposal.suggested_action || null,
        arguments: proposal.arguments || {},
        confidence: proposal.confidence
      }
      : null,
    fallback_used: Boolean(metadata.fallback_used ?? result.fallback_used),
    fallback_reason: metadata.fallback_reason ?? result.fallback_reason ?? null,
    validation_errors: metadata.validation_errors || result.validation_errors || []
  };
}

function renderAugmentation(augmentation) {
  if (!augmentation) {
    setBadge(nodes.augmentationBadge, 'missing', 'pill-neutral');
    setText(nodes.augmentationMessage, '-');
    setJson(nodes.augmentationAction, null);
    setText(nodes.augmentationFallback, '-');
    setText(nodes.augmentationFallbackReason, '-');
    setJson(nodes.augmentationErrors, []);
    return;
  }

  const fallbackUsed = Boolean(augmentation.fallback_used);
  setBadge(
    nodes.augmentationBadge,
    fallbackUsed ? 'fallback' : 'accepted',
    fallbackUsed ? 'pill-red' : 'pill-yellow'
  );
  setText(nodes.augmentationMessage, augmentation.assistant_message);
  setJson(nodes.augmentationAction, augmentation.proposed_action);
  setText(nodes.augmentationFallback, fallbackUsed);
  setText(nodes.augmentationFallbackReason, augmentation.fallback_reason);
  setJson(nodes.augmentationErrors, augmentation.validation_errors || []);
}

function renderPlanner(plannedAction) {
  setJson(nodes.plannerOutput, plannedAction);
}

function renderPolicy(policyDecision) {
  const rawDecision = policyDecision?.decision;
  const decision = typeof rawDecision === 'string' ? rawDecision.toUpperCase() : null;

  setText(nodes.policyDecision, decision);
  setJson(nodes.policyOutput, policyDecision);

  if (decision === 'ALLOW') {
    setBadge(nodes.policyBadge, 'ALLOW', 'pill-green');
  } else if (decision === 'DENY') {
    setBadge(nodes.policyBadge, 'DENY', 'pill-red');
  } else {
    setBadge(nodes.policyBadge, 'unknown', 'pill-neutral');
  }
}

function renderExecution(execution) {
  const executed = Boolean(execution?.executed);
  const dryRun = Boolean(execution?.dry_run || execution?.result?.dry_run);

  setText(nodes.executionExecuted, executed);
  setJson(nodes.executionResult, execution?.result ?? execution ?? null);

  if (executed) {
    setBadge(nodes.executionBadge, 'executed', 'pill-green');
  } else if (dryRun) {
    setBadge(nodes.executionBadge, 'dry_run', 'pill-blue');
  } else {
    setBadge(nodes.executionBadge, 'not executed', 'pill-neutral');
  }
}

nodes.runButton.addEventListener('click', runRequest);
nodes.userInput.addEventListener('input', updateRequestPreview);
nodes.dryRun.addEventListener('change', updateRequestPreview);

updateRequestPreview();
resetOutput();

