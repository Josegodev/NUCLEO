# NUCLEO State Review

> Estado del documento: artefacto generado.
>
> Este informe refleja una ejecucion concreta del laboratorio en la fecha
> indicada. No es documentacion viva del comportamiento actual. Para el estado
> actual verificado, ver `runtime_lab/llm_lab/README.md`.

Generated at: 2026-04-25T18:49:38+02:00

Repository: `/home/jose-gonzalez-oliva/NUCLEO`

## Summary

- Files read: 68
- Total size: 154767 bytes
- Context size: 1998 characters
- Context truncated: yes
- Execution path: external `llm_lab`
- Runtime integration: none

## Files Read

| File | Bytes | SHA-256 short |
| --- | ---: | --- |
| `README.md` | 4408 | `761eb6ea8b78` |
| `app/policies/__init__.py` | 0 | `e3b0c44298fc` |
| `app/policies/engine.py` | 2482 | `b98896689cd7` |
| `app/policies/models.py` | 99 | `5118f594e21d` |
| `app/runtime/__init__.py` | 0 | `e3b0c44298fc` |
| `app/runtime/dispatcher.py` | 0 | `e3b0c44298fc` |
| `app/runtime/orchestrator.py` | 7420 | `ddda6f4e0909` |
| `app/runtime/planner.py` | 6186 | `d9eefb76702f` |
| `app/runtime/tracing.py` | 2636 | `cc0ff1b45fd7` |
| `app/tools/__init__.py` | 0 | `e3b0c44298fc` |
| `app/tools/base.py` | 566 | `7462548dbe1a` |
| `app/tools/local/disk_info_tool.py` | 3315 | `f61b23426a26` |
| `app/tools/local/echo_tool.py` | 520 | `362c9f47cbbe` |
| `app/tools/local/system_info_tool.py` | 752 | `caeadfc194a6` |
| `app/tools/registry.py` | 1662 | `9b2f787fee1a` |
| `docs/EVOLUTION_MAP.md` | 3454 | `bf944c69d7cb` |
| `docs/architecture.md` | 4966 | `f63fb5f5029d` |
| `docs/architecture/llm_tool_expansion.md` | 1184 | `d9f6c702a179` |
| `docs/audits/docs_esp_sync_audit.md` | 4698 | `c0ee283f1eb9` |
| `docs/audits/documentation_consistency_audit.md` | 7240 | `4a69166ceccb` |
| `docs/audits/files_audit.md` | 1068 | `f44945781e2a` |
| `docs/audits/repo_audit.md` | 1974 | `a4cf8239ac6b` |
| `docs/modules/agent_service.md` | 750 | `c7e7b03b256e` |
| `docs/modules/audit_store.md` | 420 | `c66f5fe73a6c` |
| `docs/modules/base_tool.md` | 646 | `691a546cb9aa` |
| `docs/modules/orchestrator.md` | 2011 | `9c65f9b6f842` |
| `docs/modules/planner.md` | 1283 | `d0dd522d5cec` |
| `docs/modules/policy_engine.md` | 977 | `0f5b68468be1` |
| `docs/modules/staging_registry.md` | 440 | `16ded85cfc81` |
| `docs/modules/tool_generation_service.md` | 434 | `82fdafb58574` |
| `docs/modules/tool_proposal_service.md` | 512 | `de318fe790ae` |
| `docs/modules/tool_registry.md` | 874 | `8f43370c32cf` |
| `docs/operations/dev_state_snapshot.md` | 1524 | `8649cc643b63` |
| `docs/operations/operational_state.md` | 3226 | `1baeeec31a9e` |
| `docs/operations/session_log.md` | 5576 | `a5779fb88641` |
| `docs/operations/session_log_docs_esp_sync.md` | 1208 | `b8007ddc04ce` |
| `docs/operations/session_log_docs_normalization.md` | 1953 | `b59ccf8283a9` |
| `docs/operations/session_log_llm_tool_expansion.md` | 896 | `d3e47be613ec` |
| `docs/planning/development_plan.md` | 2174 | `2b77502f3ebe` |
| `docs/vision/architecture_vision.md` | 2786 | `35b84f44d3c4` |
| `docs_esp/EVOLUTION_MAP.md` | 4108 | `ac9ea13006c5` |
| `docs_esp/_deprecated/audits/files.audit.md` | 1542 | `2227e693c723` |
| `docs_esp/_deprecated/audits/repo.audit.md` | 2969 | `2617324684c5` |
| `docs_esp/architecture.md` | 4970 | `9b8abd4358f4` |
| `docs_esp/architecture/llm_tool_expansion.md` | 1402 | `a8439b9ce73b` |
| `docs_esp/audits/docs_esp_sync_audit.md` | 4822 | `11f39fd6cdfa` |
| `docs_esp/audits/documentation_consistency_audit.md` | 8216 | `ed1a8568244b` |
| `docs_esp/audits/files_audit.md` | 1272 | `25239e4a1384` |
| `docs_esp/audits/repo_audit.md` | 2311 | `84fe8edd7bbe` |
| `docs_esp/modules/agent_service.md` | 991 | `d40b086d377a` |
| `docs_esp/modules/audit_store.md` | 548 | `7954f61d3752` |
| `docs_esp/modules/base_tool.md` | 817 | `08c1e47af18f` |
| `docs_esp/modules/orchestrator.md` | 1668 | `065e09b9da57` |
| `docs_esp/modules/planner.md` | 1509 | `caf53e5ab91c` |
| `docs_esp/modules/policy_engine.md` | 1189 | `ee6b37ff5c9e` |
| `docs_esp/modules/staging_registry.md` | 571 | `ae6f26dd6adf` |
| `docs_esp/modules/tool_generation_service.md` | 597 | `18cd6b017a7b` |
| `docs_esp/modules/tool_proposal_service.md` | 629 | `a39c89fa6b69` |
| `docs_esp/modules/tool_registry.md` | 1083 | `80e53c616226` |
| `docs_esp/operations/dev_state_snapshot.md` | 1824 | `d510c664f087` |
| `docs_esp/operations/operational_state.md` | 3229 | `f0fd30c9e6cf` |
| `docs_esp/operations/session_log.md` | 3478 | `43df9ae2e01a` |
| `docs_esp/operations/session_log_docs_esp_sync.md` | 1286 | `4b9da55d0bfd` |
| `docs_esp/operations/session_log_docs_normalization.md` | 2322 | `54561eb5d2ca` |
| `docs_esp/operations/session_log_llm_tool_expansion.md` | 1165 | `e69287a3aaf3` |
| `docs_esp/planning/development_plan.md` | 2654 | `1582e10fca80` |
| `docs_esp/vision/architecture_vision.md` | 3304 | `85b50e8c0434` |
| `tests/test_runtime_tracing.py` | 11971 | `4df7d12db42a` |

## Local LLM Output

```text
LOCAL_LLM_NOT_CALLED

The HARDENING prompt was generated successfully, but this script did not call a local model yet. Wire this function to a local llm_lab model runner when you want that behavior.
```

## Prompt Sent Or Prepared

```text
You are reviewing the current NUCLEO repository state.

Scope:
- This is an external llm_lab review path, not part of NUCLEO runtime.
- Do not propose LLM integration into AgentService, Runtime, Planner, PolicyEngine, ToolRegistry, or Tools.
- Do not expand architecture.
- Focus on HARDENING only.

Review goals:
- Contracts between PolicyDecision, PolicyEngine, runtime/orchestrator, and ToolRegistry.
- Determinism in execution.
- Explicit validation.
- Error handling.
- Tests.
- Documentation consistency.

Output rules:
- Classify each finding as CRITICAL, INFORMATIVE, or PREMATURE.
- Point to exact files from the provided context.
- Prefer the smallest reasonable change.
- If evidence is missing, say so.

Context truncated: yes

NUCLEO CONTEXT:
--- FILE: README.md | bytes=4408 | sha256_12=761eb6ea8b78 ---
# NUCLEO

NUCLEO es un runtime de agentes modulares construido sobre FastAPI. Su objetivo es ejecutar peticiones de usuario mediante un pipeline controlado y auditable, evitando comportamientos opacos y separando con claridad decisión, validación y ejecución.

## Estado documental

La documentación del repositorio sigue esta convención:

- `docs/architecture.md` describe arquitectura verificada en código.
- `docs/vision/architecture_vision.md` describe arquitectura objetivo.
- `docs/operations/` recoge estado operativo y session logs.
- `docs/audits/` recoge evaluaciones críticas y consistencia documental.

Si un documento describe una capacidad futura o experimental, debe indicarlo explícitamente.

## Arquitectura verificada

El flujo estable actual es:

Request  
→ API  
→ AgentService  
→ AgentRuntime  
→ Planner  
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse

### Componentes verificados

- `Planner` adapta intención a una acción candidata determinista.
- `ToolRegistry` es la fuente de verdad de tools ejecutables.
- `PolicyEngine` autoriza la ejecución según autenticación, rol y nombre de tool.
- `Tool` ejecuta la acción real.
- `AgentResponse` devuelve `status`, `message` y `result` opcional.

## Estado actual del runtime

### Implementado actualmente

- API FastAPI funcional
- Endpoint `POST /agent/run`
- Endpoint `GET /tools`
- Endpoint `GET /`
- Autenticación por API key por request
- `ExecutionContext` propagado por runtime, policy y tools
- Tools de producción:
  - `echo`
  - `system_info`
  - `disk_info`
- Resultado estructurado conservado en `AgentResponse.result`
- Fase HARDENING en curso:
  - contratos runtime-policy-registry más explícitos
  - Planner devuelve `planned` o `no_plan`
  - `no_plan` no ejecuta tools
  - `dry_run` no ejecuta la tool real
  - trazabilidad interna mínima en memoria para el runtime

### Experimental, no producción

Existen módulos y artefactos de lab

```
