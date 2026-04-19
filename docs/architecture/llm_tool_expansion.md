# LLM Tool Expansion Architecture

## Purpose

This document describes an experimental, isolated subsystem for controlled LLM-assisted
tool generation in NUCLEO. The design extends the existing runtime without replacing the
stable production pipeline.

## Stable Path

The production path remains:

API -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> Tool

Existing tools keep their current behavior.

## Experimental Path

When the planner detects a capability gap and the request explicitly enables the lab flow,
NUCLEO creates a structured proposal, stores it under `runtime_lab/proposals/`, registers
it in an isolated staging registry, generates a tool skeleton under
`runtime_lab/generated_tools/`, and records audit artifacts under `runtime_lab/audit/`.

This path never registers the generated tool in the production `ToolRegistry`.

## Safety Properties

- No shell execution is introduced.
- No package installation is introduced.
- Generated tools are not auto-loaded by production runtime.
- Policy enforcement is unchanged for production tools.
- Audit trail is written for proposal creation, staging updates, generation, and orchestration.
