# Agent Proposal Evals

## Objective

This eval suite measures contract compliance for local and external models used
by `planner_augmentation`.

It evaluates model proposals only. It does not execute tools, does not call
`/agent/approve`, and does not modify payloads.

## What It Measures

Each case is sent through the same proposal boundary used by Planner
augmentation:

```text
AgentRequest
-> LLMAssistedPlannerStrategy input builder
-> ModelRouterProposalProvider
-> ModelRouter
-> LLMPlanOutputValidator
-> ToolRegistry contracts
```

Measured fields:

- `valid_json`: the model returned JSON accepted by the Planner normalizer
- `valid_contract`: the proposal validates against real `ToolRegistry` payload
  contracts
- `expected_action_match`: `suggested_action` matches the expected action
- `expected_arguments_match`: `arguments` matches expected arguments
- `fallback_used`: model/provider fallback or deterministic fallback would be
  required
- `latency_ms`: model router latency

## Add Cases

Edit `agent_proposal_eval_cases.json`.

Each case has:

```json
{
  "id": "echo_basic_es",
  "input": "haz echo de hola",
  "expected": {
    "suggested_action": "echo",
    "arguments": {
      "text": "hola"
    },
    "valid_contract": true
  }
}
```

Use exact tool argument names from `ToolRegistry` contracts. Do not add aliases
such as `message` for `echo`; the real contract requires `text`.

## Run

From the repository root:

```bash
python -m runtime_lab.llm_lab.evals.run_agent_proposal_evals \
  --models llama3.1:8b,gpt-4o-mini \
  --backends local,openai
```

Optional flags:

- `--cases`: path to an eval cases JSON file
- `--output-dir`: directory for result artifacts
- `--timeout-ms`: model call timeout

Results are written to:

```text
runtime_lab/llm_lab/evals/results/agent_proposal_eval_<timestamp>.json
```

If `OPENAI_API_KEY` is missing, OpenAI rows are marked
`provider_unavailable`. The suite still completes.

## Ranking

Each model/backend pair receives a ranking item:

```json
{
  "model": "llama3.1:8b",
  "backend": "local",
  "score": 0.92,
  "valid_contract_rate": 1.0,
  "fallback_rate": 0.0,
  "avg_latency_ms": 650,
  "runtime_candidate": true
}
```

`score` is the average of:

- valid JSON rate
- valid contract rate
- expected action match rate
- expected arguments match rate

## Runtime Candidate

A model/backend pair is a `runtime_candidate` only when:

- `valid_contract_rate >= 0.95`
- `fallback_rate <= 0.10`
- there are no critical failures
- the provider is available

An experimental model can be useful for lab review even when it is not a
runtime candidate. Runtime candidate means the model is contract-compliant
enough to consider for controlled Planner augmentation.
