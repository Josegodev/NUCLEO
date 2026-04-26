# Runtime Lab Audit References

This directory contains audit notes produced during NUCLEO HARDENING.

The repositories cloned under `external/` are reference material only.

## External reference repositories

- Shimmy  
  Source: https://github.com/Michael-A-Kuykendall/shimmy  
  Local path: `external/shimmy`  
  Purpose: external inference backend candidate review.  
  Status: read-only reference.  
  Must not be imported by NUCLEO runtime.

- llm-council  
  Source: https://github.com/karpathy/llm-council  
  Local path: `external/llm-council`  
  Purpose: conceptual reference for multi-model / council-style orchestration experiments.  
  Status: read-only reference.  
  Must not be imported by NUCLEO runtime.

## Boundary rule

These repositories are not part of the NUCLEO execution path:

```text
Request → FastAPI → AgentService → AgentRuntime → Planner → PolicyEngine → ToolRegistry → Tool → AgentResponse