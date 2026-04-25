# LLM Tool Expansion Architecture

## Purpose

This document describes an experimental, isolated subsystem for controlled
LLM-assisted tool generation in NUCLEO. It is a lab design and set of isolated
services, not an active branch of the current stable runtime.

## Stable Path

The production path remains:

Request -> API/FastAPI -> AgentService -> AgentRuntime/Orchestrator -> Planner -> PolicyEngine -> ToolRegistry -> Tool -> AgentResponse

Existing tools keep their current behavior.

## Experimental Path

The repository contains services that can create structured proposals, store
them under `runtime_lab/proposals/`, register them in an isolated staging
registry, generate tool skeletons under `runtime_lab/generated_tools/`, and
record audit artifacts under `runtime_lab/audit/`.

Important current-state constraint: the stable Planner does not emit
`capability_gap_detected`. Its current contract is only `planned` or `no_plan`.
The `experimental_tool_generation` request field exists, but the stable
`/agent/run` flow does not use it to activate this path.

This path never registers the generated tool in the production `ToolRegistry`.

## Relationship to llm_lab

`runtime_lab/llm_lab/` is a separate lateral observation path for local
Mistral/Qwen chats and HARDENING reports. It does not execute this expansion
path, does not act as Planner, and does not register tools.

## Safety Properties

- No shell execution is introduced.
- No package installation is introduced.
- Generated tools are not auto-loaded by production runtime.
- Policy enforcement is unchanged for production tools.
- Audit trail is written for proposal creation, staging updates, generation, and orchestration.
