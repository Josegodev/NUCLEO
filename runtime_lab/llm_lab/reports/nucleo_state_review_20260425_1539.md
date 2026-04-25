# NUCLEO State Review

> Estado del documento: artefacto generado.
>
> Este informe refleja una ejecucion concreta del laboratorio en la fecha
> indicada. No es documentacion viva del comportamiento actual. Para el estado
> actual verificado, ver `runtime_lab/llm_lab/README.md`.
>
> Advertencia HARDENING: este informe conserva una ruta antigua bajo
> `/home/jose-gonzalez-oliva/IA/...` y texto obsoleto sobre
> `capability_gap_detected` y `dry_run`. Debe leerse solo como snapshot
> historico generado, no como contrato actual de NUCLEO.

Generated at: 2026-04-25T15:39:11+02:00

Repository: `/home/jose-gonzalez-oliva/IA/proyectos/nucleo/NUCLEO`

## Summary

- Files read: 68
- Total size: 153759 bytes
- Context size: 119997 characters
- Context truncated: yes
- Execution path: external `llm_lab`
- Runtime integration: none

## Files Read

| File | Bytes | SHA-256 short |
| --- | ---: | --- |
| `README.md` | 4392 | `a15c422894ab` |
| `app/policies/__init__.py` | 0 | `e3b0c44298fc` |
| `app/policies/engine.py` | 2409 | `30c5c40406de` |
| `app/policies/models.py` | 99 | `5118f594e21d` |
| `app/runtime/__init__.py` | 0 | `e3b0c44298fc` |
| `app/runtime/dispatcher.py` | 0 | `e3b0c44298fc` |
| `app/runtime/orchestrator.py` | 7420 | `d846c624b153` |
| `app/runtime/planner.py` | 6183 | `a563eb65d051` |
| `app/runtime/tracing.py` | 2636 | `cc0ff1b45fd7` |
| `app/tools/__init__.py` | 0 | `e3b0c44298fc` |
| `app/tools/base.py` | 566 | `7462548dbe1a` |
| `app/tools/local/disk_info_tool.py` | 3315 | `f61b23426a26` |
| `app/tools/local/echo_tool.py` | 520 | `362c9f47cbbe` |
| `app/tools/local/system_info_tool.py` | 752 | `caeadfc194a6` |
| `app/tools/registry.py` | 1659 | `61571b57e438` |
| `docs/EVOLUTION_MAP.md` | 3482 | `303ff40b3975` |
| `docs/architecture.md` | 4893 | `5353b1c71b9c` |
| `docs/architecture/llm_tool_expansion.md` | 1184 | `d9f6c702a179` |
| `docs/audits/docs_esp_sync_audit.md` | 4698 | `c0ee283f1eb9` |
| `docs/audits/documentation_consistency_audit.md` | 7240 | `4a69166ceccb` |
| `docs/audits/files_audit.md` | 1068 | `f44945781e2a` |
| `docs/audits/repo_audit.md` | 1974 | `a4cf8239ac6b` |
| `docs/modules/agent_service.md` | 750 | `c7e7b03b256e` |
| `docs/modules/audit_store.md` | 420 | `c66f5fe73a6c` |
| `docs/modules/base_tool.md` | 646 | `691a546cb9aa` |
| `docs/modules/orchestrator.md` | 2011 | `8a11ff1a6e68` |
| `docs/modules/planner.md` | 1283 | `d0dd522d5cec` |
| `docs/modules/policy_engine.md` | 914 | `1db089b5a807` |
| `docs/modules/staging_registry.md` | 440 | `16ded85cfc81` |
| `docs/modules/tool_generation_service.md` | 434 | `82fdafb58574` |
| `docs/modules/tool_proposal_service.md` | 512 | `de318fe790ae` |
| `docs/modules/tool_registry.md` | 874 | `8f43370c32cf` |
| `docs/operations/dev_state_snapshot.md` | 1356 | `bf4362d1f8ab` |
| `docs/operations/operational_state.md` | 2781 | `cb9ac6c92926` |
| `docs/operations/session_log.md` | 5576 | `a5779fb88641` |
| `docs/operations/session_log_docs_esp_sync.md` | 1208 | `b8007ddc04ce` |
| `docs/operations/session_log_docs_normalization.md` | 1953 | `b59ccf8283a9` |
| `docs/operations/session_log_llm_tool_expansion.md` | 896 | `d3e47be613ec` |
| `docs/planning/development_plan.md` | 2174 | `2b77502f3ebe` |
| `docs/vision/architecture_vision.md` | 2786 | `35b84f44d3c4` |
| `docs_esp/EVOLUTION_MAP.md` | 4161 | `0cf69ec19971` |
| `docs_esp/_deprecated/audits/files.audit.md` | 1542 | `2227e693c723` |
| `docs_esp/_deprecated/audits/repo.audit.md` | 2969 | `2617324684c5` |
| `docs_esp/architecture.md` | 5181 | `49e68d6c76cc` |
| `docs_esp/architecture/llm_tool_expansion.md` | 1402 | `a8439b9ce73b` |
| `docs_esp/audits/docs_esp_sync_audit.md` | 4822 | `11f39fd6cdfa` |
| `docs_esp/audits/documentation_consistency_audit.md` | 8216 | `ed1a8568244b` |
| `docs_esp/audits/files_audit.md` | 1272 | `25239e4a1384` |
| `docs_esp/audits/repo_audit.md` | 2311 | `84fe8edd7bbe` |
| `docs_esp/modules/agent_service.md` | 991 | `d40b086d377a` |
| `docs_esp/modules/audit_store.md` | 548 | `7954f61d3752` |
| `docs_esp/modules/base_tool.md` | 817 | `08c1e47af18f` |
| `docs_esp/modules/orchestrator.md` | 1946 | `7f316b8e524e` |
| `docs_esp/modules/planner.md` | 1556 | `39171c4596e0` |
| `docs_esp/modules/policy_engine.md` | 1131 | `86cca0235ca2` |
| `docs_esp/modules/staging_registry.md` | 571 | `ae6f26dd6adf` |
| `docs_esp/modules/tool_generation_service.md` | 597 | `18cd6b017a7b` |
| `docs_esp/modules/tool_proposal_service.md` | 629 | `a39c89fa6b69` |
| `docs_esp/modules/tool_registry.md` | 1083 | `80e53c616226` |
| `docs_esp/operations/dev_state_snapshot.md` | 1634 | `4fe3345690f0` |
| `docs_esp/operations/operational_state.md` | 3476 | `8054f81c1467` |
| `docs_esp/operations/session_log.md` | 3478 | `43df9ae2e01a` |
| `docs_esp/operations/session_log_docs_esp_sync.md` | 1286 | `4b9da55d0bfd` |
| `docs_esp/operations/session_log_docs_normalization.md` | 2322 | `54561eb5d2ca` |
| `docs_esp/operations/session_log_llm_tool_expansion.md` | 1165 | `e69287a3aaf3` |
| `docs_esp/planning/development_plan.md` | 2654 | `1582e10fca80` |
| `docs_esp/vision/architecture_vision.md` | 3304 | `85b50e8c0434` |
| `tests/test_runtime_tracing.py` | 11191 | `8119c258be3c` |

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
--- FILE: README.md | bytes=4392 | sha256_12=a15c422894ab ---
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

Existen módulos y artefactos de laboratorio aislados en `runtime_lab/`, pero no
forman parte del contrato estable actual del Planner. El Planner estable solo
devuelve `planned` o `no_plan`.

### No implementado todavía

- Integración real con LLM para planificación
- Promoción automática desde staging a producción
- Ejecución de tools generadas en el registry principal
- Persistencia operativa del runtime más allá de artefactos de laboratorio
- Exposición pública de trazas por API
- Persistencia de trazas fuera de memoria

## Quick start:

source .venv/bin/activate

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar el servidor

```bash
uvicorn app.main:app --reload
```

### 3. Abrir Swagger

```text
http://127.0.0.1:8000/docs
```

## Autenticación

El sistema utiliza API key por request mediante `Authorization: Bearer <token>`.

Clave de desarrollo disponible en la configuración actual:



## Ejemplo de uso

### Request

```json
{
  "user_input": "system info",
  "dry_run": true
}
```

### curl

```bash
curl -X POST http://127.0.0.1:8000/agent/run \
  -H "Authorization: Bearer dev-jose-key" \
  -H "Content-Type: application/json" \
  -d "{\"user_input\": \"system info\", \"dry_run\": true}"
```

### Response actual

```json
{
  "status": "dry_run_success",
  "message": "{'dry_run': True, 'executed': False, 'tool': 'system_info', 'payload': {}}",
  "result": {
    "dry_run": true,
    "executed": false,
    "tool": "system_info",
    "payload": {}
  }
}
```

En `dry_run=true`, el runtime ejecuta Planner, ToolRegistry y PolicyEngine,
pero no llama a `Tool.run(...)`. La respuesta indica la tool que se habría
ejecutado y marca `executed=false`.

## Flujo de ejecución

Cliente HTTP  
↓  
Uvicorn  
↓  
FastAPI (`/agent/run`)  
↓  
AgentService  
↓  
AgentRuntime  
↓  
Planner → ToolRegistry → PolicyEngine → Tool / dry_run  
↓  
AgentResponse

Si el Planner devuelve `no_plan`, el Runtime no consulta PolicyEngine y no
ejecuta ninguna tool. El Planner no autoriza y no ejecuta; solo propone.

La trazabilidad de ejecución existe como mecanismo interno en memoria del
runtime. No forma parte del contrato público de `/agent/run`, no se persiste y
no se expone todavía mediante endpoint.

## Referencias útiles

- `docs/architecture.md`
- `docs/vision/architecture_vision.md`
- `docs/EVOLUTION_MAP.md`
- `docs/audits/documentation_consistency_audit.md`


--- FILE: app/policies/__init__.py | bytes=0 | sha256_12=e3b0c44298fc ---


--- FILE: app/policies/engine.py | bytes=2409 | sha256_12=30c5c40406de ---
"""
NUCLEO - POLICY ENGINE

Componente responsable de validar si una acción propuesta por el planner
puede ser ejecutada.

Responsable de:
- Evaluar permisos de ejecución de tools
- Aplicar reglas de seguridad antes de la ejecución
- Considerar el contexto de ejecución autenticado
- Devolver decisiones estructuradas (PolicyDecision)

Flujo:
tool_name + payload + dry_run + context
    → evaluación de reglas
    → PolicyDecision (allow / deny)

Tipo de implementación:
- Whitelist estática (permitir solo tools explícitas)
- Estrategia "deny by default"
- Validación básica por usuario/rol

Salida:
PolicyDecision:
{
    decision: "allow" | "deny",
    reason: str
}

Notas:
- No ejecuta acciones, solo valida
- Runtime valida primero que la tool existe en ToolRegistry
- Diseñado para ser extensible (reglas más complejas en el futuro)

Limitaciones actuales:
- No evalúa payload en profundidad
- No diferencia todavía reglas avanzadas entre dry_run y ejecución real
- Control de roles aún básico

Arquitectura:
Capa de control dentro del pipeline:
planner → registry → policy → execution
"""

from app.policies.models import PolicyDecision
from app.schemas.context import ExecutionContext
from app.tools.registry import ToolRegistry
from app.tools.registry import registry as default_registry


class PolicyEngine:
    def __init__(self, tool_registry: ToolRegistry = default_registry) -> None:
        self._tool_registry = tool_registry

    def evaluate(
        self,
        tool_name: str,
        payload: dict,
        dry_run: bool,
        context: ExecutionContext,
    ) -> PolicyDecision:
        if not context.authenticated:
            return PolicyDecision(
                decision="deny",
                reason="unauthenticated request",
            )

        if self._tool_registry.get(tool_name) is None:
            return PolicyDecision(
                decision="deny",
                reason=f"tool '{tool_name}' is not allowed by policy",
            )

        if tool_name == "system_info" and "admin" not in context.roles:
            return PolicyDecision(
                decision="deny",
                reason=f"user '{context.username}' is not allowed to run 'system_info'",
            )

        return PolicyDecision(
            decision="allow",
            reason=f"{tool_name} tool is allowed for user '{context.username}'",
        )


--- FILE: app/policies/models.py | bytes=99 | sha256_12=5118f594e21d ---
from pydantic import BaseModel


class PolicyDecision(BaseModel):
    decision: str
    reason: str

--- FILE: app/runtime/__init__.py | bytes=0 | sha256_12=e3b0c44298fc ---


--- FILE: app/runtime/dispatcher.py | bytes=0 | sha256_12=e3b0c44298fc ---


--- FILE: app/runtime/orchestrator.py | bytes=7420 | sha256_12=d846c624b153 ---
"""
NUCLEO - AGENT RUNTIME (ORCHESTRATOR)

Motor central de ejecución de agentes.

Responsable de:
- Transformar una solicitud (AgentRequest) en un plan ejecutable
- Validar la ejecución mediante políticas (PolicyEngine)
- Resolver la herramienta adecuada (ToolRegistry)
- Ejecutar la acción correspondiente (Tool)
- Propagar el ExecutionContext a policy y tools
- Devolver una respuesta estructurada (AgentResponse)

Flujo:
AgentRequest
    → Planner (create_plan)
    → ToolRegistry (get tool)
    → PolicyEngine (evaluate)
    → Tool (run)
    → AgentResponse

Componentes:
- Planner: propone una acción candidata determinista
- ToolRegistry: mantiene catálogo de herramientas ejecutables
- PolicyEngine: controla permisos y seguridad
- Tools: implementaciones concretas de ejecución

Notas:
- Soporta modo 'dry_run' para simulación sin ejecución real
- Todas las acciones pasan por validación de políticas
- Diseñado para ser extensible (nuevas tools, nuevas policies)

Arquitectura:
Command Execution Pipeline con control de políticas.
"""

from app.schemas.context import ExecutionContext
from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.runtime.planner import Planner
from app.runtime.tracing import ExecutionStep, ExecutionTrace, InMemoryTracer, Tracer
from app.tools.registry import registry
from app.policies.engine import PolicyEngine

planner = Planner()
policy_engine = PolicyEngine(tool_registry=registry)
tracer = InMemoryTracer()


class AgentRuntime:
    def __init__(
        self,
        runtime_planner: Planner | None = None,
        runtime_policy_engine: PolicyEngine | None = None,
        tool_registry=registry,
        runtime_tracer: Tracer | None = None,
    ) -> None:
        self._planner = runtime_planner or planner
        self._policy_engine = runtime_policy_engine or policy_engine
        self._registry = tool_registry
        self._tracer = runtime_tracer or tracer

    def run(self, request: AgentRequest, context: ExecutionContext) -> AgentResponse:
        trace = self._safe_start_trace(context.request_id)
        try:
            plan = self._planner.create_plan(request)
            self._validate_planner_result(plan)
        except Exception as exc:
            self._safe_record_step(
                trace=trace,
                phase="planner",
                input={"user_input": request.user_input},
                output={},
                status="error",
                error=str(exc),
            )
            return AgentResponse(
                status="error",
                message=f"Planner failed to produce a valid result: {exc}",
            )

        self._safe_record_step(
            trace=trace,
            phase="planner",
            input={"user_input": request.user_input},
            output=plan.model_dump(),
            status="success",
        )

        if plan.status == "no_plan":
            return AgentResponse(
                status="no_plan",
                message=plan.reason,
            )

        tool_name = plan.tool_name
        tool_payload = plan.payload

        tool = self._registry.get(tool_name)
        self._safe_record_step(
            trace=trace,
            phase="registry",
            input={"tool": tool_name},
            output={
                "found": tool is not None,
                "tool": getattr(tool, "name", None),
            },
            status="success" if tool else "error",
            error=None if tool else f"Planner proposed unknown tool: {tool_name}",
        )
        if not tool:
            return AgentResponse(
                status="error",
                message=f"Planner proposed unknown tool: {tool_name}",
            )

        policy_decision = self._policy_engine.evaluate(
            tool_name=tool_name,
            payload=tool_payload,
            dry_run=request.dry_run,
            context=context,
        )
        self._safe_record_step(
            trace=trace,
            phase="policy",
            input={
                "tool": tool_name,
                "payload": tool_payload,
                "dry_run": request.dry_run,
                "context": {
                    "request_id": context.request_id,
                    "username": context.username,
                    "roles": context.roles,
                    "authenticated": context.authenticated,
                },
            },
            output=policy_decision.model_dump(),
            status="denied" if policy_decision.decision == "deny" else "success",
            error=policy_decision.reason if policy_decision.decision == "deny" else None,
        )

        if policy_decision.decision == "deny":
            return AgentResponse(
                status="blocked",
                message=policy_decision.reason,
            )

        if request.dry_run:
            result = {
                "dry_run": True,
                "executed": False,
                "tool": tool_name,
                "payload": tool_payload,
            }
            self._safe_record_step(
                trace=trace,
                phase="tool",
                input={"tool": tool_name, "payload": tool_payload, "dry_run": True},
                output={**result, "reason": "dry_run"},
                status="skipped",
            )
            return AgentResponse(
                status="dry_run_success",
                message=str(result),
                result=result,
            )

        try:
            result = tool.run(tool_payload, context=context)
        except Exception as exc:
            self._safe_record_step(
                trace=trace,
                phase="tool",
                input={"tool": tool_name, "payload": tool_payload, "dry_run": False},
                output={},
                status="error",
                error=str(exc),
            )
            raise

        self._safe_record_step(
            trace=trace,
            phase="tool",
            input={"tool": tool_name, "payload": tool_payload, "dry_run": False},
            output=result,
            status="success",
        )

        return AgentResponse(
            status="success",
            message=str(result),
            result=result,
        )

    def _validate_planner_result(self, plan: PlannedAction) -> None:
        if not isinstance(plan, PlannedAction):
            raise TypeError("Planner must return PlannedAction")

    def _safe_start_trace(self, request_id: str | None) -> ExecutionTrace | None:
        try:
            return self._tracer.start_trace(request_id=request_id)
        except Exception:
            return None

    def _safe_record_step(
        self,
        trace: ExecutionTrace | None,
        phase: str,
        input: dict,
        output: dict,
        status: str,
        error: str | None = None,
    ) -> None:
        if trace is None:
            return

        try:
            step = ExecutionStep(
                step_id="",
                phase=phase,
                input=input,
                output=output,
                status=status,
                error=error,
                timestamp="",
            )
            self._tracer.record_step(
                trace=trace,
                step=step,
            )
        except Exception:
            return


--- FILE: app/runtime/planner.py | bytes=6183 | sha256_12=a563eb65d051 ---
"""
NUCLEO - PLANNER

Componente responsable de transformar una solicitud de usuario
(AgentRequest) en un plan de ejecución estructurado.

Responsable de:
- Interpretar la entrada del usuario de forma determinista
- Proponer una acción estructurada candidata
- Construir el payload necesario para dicha herramienta

Flujo:
AgentRequest → normalización → tabla de reglas → PlannedAction

Tipo de implementación:
- Rule-based (determinista)
- Basado en una tabla explícita de reglas auditables

Salida:
PlannedAction con estructura estable:
{
    "tool_name": str | None,
    "payload": dict,
    "confidence": float,
    "reason": str,
    "status": "planned" | "no_plan"
}

Notas:
- No ejecuta lógica ni valida permisos
- No interactúa con tools directamente
- No inventa tools: solo planifica tools presentes en ToolRegistry
- Su salida es consumida por el runtime (orchestrator)

Limitaciones actuales:
- Matching simple mediante reglas explícitas
- No soporta múltiples acciones ni composición de tools
- No utiliza contexto ni memoria

Arquitectura:
Componente de decisión dentro del pipeline:
input → planner → registry → policy → execution
"""

from dataclasses import dataclass
from typing import Callable

from app.schemas.execution import PlannedAction
from app.schemas.requests import AgentRequest
from app.tools.registry import ToolRegistry
from app.tools.registry import registry as default_registry


PayloadBuilder = Callable[[AgentRequest], dict]
Matcher = Callable[[str, AgentRequest], bool]


@dataclass(frozen=True)
class PlannerRule:
    name: str
    tool_name: str
    matches: Matcher
    build_payload: PayloadBuilder
    confidence: float
    reason: str


class Planner:
    def __init__(
        self,
        tool_registry: ToolRegistry = default_registry,
        rules: list[PlannerRule] | None = None,
    ) -> None:
        self._tool_registry = tool_registry
        self._rules = rules or self._default_rules()

    def create_plan(self, request: AgentRequest) -> PlannedAction:
        structured_payload = request.payload or {}
        raw_input = request.user_input or ""
        normalized_input = raw_input.strip().lower()

        if request.tool:
            if not self._tool_exists(request.tool):
                return PlannedAction(
                    payload=structured_payload,
                    status="no_plan",
                    confidence=0.0,
                    reason=f"Explicit tool is not registered: {request.tool}",
                    source="explicit_request",
                )

            return PlannedAction(
                tool_name=request.tool,
                payload=structured_payload,
                status="planned",
                confidence=1.0,
                reason="Explicit tool requested by caller.",
                source="explicit_request",
            )

        for rule in self._rules:
            if not rule.matches(normalized_input, request):
                continue

            if not self._tool_exists(rule.tool_name):
                return PlannedAction(
                    payload=structured_payload,
                    status="no_plan",
                    confidence=0.0,
                    reason=f"Matched rule '{rule.name}', but tool is not registered: {rule.tool_name}",
                    source=f"rule:{rule.name}",
                )

            return PlannedAction(
                tool_name=rule.tool_name,
                payload=rule.build_payload(request),
                status="planned",
                confidence=rule.confidence,
                reason=rule.reason,
                source=f"rule:{rule.name}",
            )

        return PlannedAction(
            payload=structured_payload,
            status="no_plan",
            confidence=0.0,
            reason="No deterministic planner rule matched the request.",
            source="rule_table",
        )

    def _tool_exists(self, tool_name: str) -> bool:
        return self._tool_registry.get(tool_name) is not None

    def _default_rules(self) -> list[PlannerRule]:
        return [
            PlannerRule(
                name="disk_info",
                tool_name="disk_info",
                matches=lambda normalized_input, request: "disk info" in normalized_input
                or "disk" in normalized_input,
                build_payload=self._build_disk_payload,
                confidence=0.9,
                reason="Request matched deterministic disk information rule.",
            ),
            PlannerRule(
                name="system_info",
                tool_name="system_info",
                matches=lambda normalized_input, request: "system" in normalized_input
                or "info" in normalized_input,
                build_payload=lambda request: request.payload or {},
                confidence=0.85,
                reason="Request matched deterministic system information rule.",
            ),
        ]

    @staticmethod
    def _build_disk_payload(request: AgentRequest) -> dict:
        structured_payload = request.payload or {}
        disk_path_from_text = Planner._extract_path_from_text(request.user_input or "")
        return Planner._merge_disk_payload(structured_payload, disk_path_from_text)

    @staticmethod
    def _extract_path_from_text(user_input: str) -> str | None:
        marker = "path="
        lower_input = user_input.lower()
        marker_index = lower_input.find(marker)
        if marker_index == -1:
            return None

        path_value = user_input[marker_index + len(marker):].strip()
        if not path_value:
            return None

        for separator in (" ", ",", ";"):
            separator_index = path_value.find(separator)
            if separator_index != -1:
                path_value = path_value[:separator_index]
                break

        return path_value.strip() or None

    @staticmethod
    def _merge_disk_payload(payload: dict, path_from_text: str | None) -> dict:
        merged_payload = dict(payload)
        if "path" not in merged_payload and path_from_text:
            merged_payload["path"] = path_from_text
        return merged_payload


--- FILE: app/runtime/tracing.py | bytes=2636 | sha256_12=cc0ff1b45fd7 ---
"""
Minimal in-memory runtime tracing.

This module is intentionally internal to the runtime. It does not persist data,
does not call external services, and does not decide whether tools may run.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Callable, Literal

from pydantic import BaseModel, Field


TracePhase = Literal["planner", "policy", "registry", "tool"]
TraceStatus = Literal["success", "error", "denied", "skipped"]


class ExecutionStep(BaseModel):
    step_id: str
    phase: TracePhase
    input: dict
    output: dict
    status: TraceStatus
    error: str | None = None
    timestamp: str


class ExecutionTrace(BaseModel):
    trace_id: str
    request_id: str | None = None
    steps: list[ExecutionStep] = Field(default_factory=list)


class Tracer(ABC):
    @abstractmethod
    def start_trace(self, request_id: str | None = None) -> ExecutionTrace:
        raise NotImplementedError

    @abstractmethod
    def record_step(self, trace: ExecutionTrace, step: ExecutionStep) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_trace(self, trace_id: str) -> ExecutionTrace | None:
        raise NotImplementedError


class InMemoryTracer(Tracer):
    def __init__(
        self,
        timestamp_provider: Callable[[], str] | None = None,
    ) -> None:
        self._traces: dict[str, ExecutionTrace] = {}
        self._sequence = 0
        self._timestamp_provider = timestamp_provider or self._utc_timestamp

    def start_trace(self, request_id: str | None = None) -> ExecutionTrace:
        trace_id = self._build_trace_id(request_id)
        trace = ExecutionTrace(trace_id=trace_id, request_id=request_id)
        self._traces[trace_id] = trace
        return trace

    def record_step(self, trace: ExecutionTrace, step: ExecutionStep) -> None:
        step_number = len(trace.steps) + 1
        completed_step = step.model_copy(
            update={
                "step_id": step.step_id or f"{step_number:03d}-{step.phase}",
                "timestamp": step.timestamp or self._timestamp_provider(),
            }
        )
        trace.steps.append(completed_step)
        self._traces[trace.trace_id] = trace

    def get_trace(self, trace_id: str) -> ExecutionTrace | None:
        return self._traces.get(trace_id)

    def _build_trace_id(self, request_id: str | None) -> str:
        if request_id:
            return f"trace-{request_id}"

        self._sequence += 1
        return f"trace-{self._sequence:06d}"

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()


--- FILE: app/tools/__init__.py | bytes=0 | sha256_12=e3b0c44298fc ---


--- FILE: app/tools/base.py | bytes=566 | sha256_12=7462548dbe1a ---
"""
NUCLEO - BASE TOOL

Define la interfaz común que deben implementar todas las tools.

Contrato:
- Todas las tools deben implementar run(payload, context)
- El context contiene información de ejecución (usuario, request_id, etc.)
- Las tools NO deben encargarse de autenticación ni autorización
"""

from app.schemas.context import ExecutionContext


class BaseTool:
    name: str
    description: str
    read_only: bool
    risk_level: str

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        raise NotImplementedError

--- FILE: app/tools/local/disk_info_tool.py | bytes=3315 | sha256_12=f61b23426a26 ---
import os
import platform
import shutil

from app.schemas.context import ExecutionContext
from app.tools.base import BaseTool


class DiskInfoTool(BaseTool):
    """Return disk usage information for a path or mount point.

    This tool reports disk usage, not RAM or any other memory metric.

    Cross-platform behavior:
    - Uses ``platform.system()`` to detect the current operating system.
    - Defaults to ``"C:\\"`` on Windows when no path is provided.
    - Defaults to ``"/"`` on Linux and macOS when no path is provided.
    - Works with paths and mount points supported by the host OS.

    Limitations:
    - Does not distinguish disk type.
    - Does not enumerate multiple disks.
    - Does not measure RAM.
    """

    name = "disk_info"
    description = "Returns disk usage information for a path or mount point."
    read_only = True
    risk_level = "low"

    def run(self, payload: dict | None = None, context: ExecutionContext | None = None) -> dict:
        payload = payload or {}

        try:
            system_name = platform.system()
            requested_path = payload.get("path")
            target_path = requested_path or self._default_path(system_name)

            if not os.path.exists(target_path):
                return self._error_response(f"Path does not exist: {target_path}", target_path, system_name)

            usage = shutil.disk_usage(target_path)
            total_gb = self._bytes_to_gb(usage.total)
            used_gb = self._bytes_to_gb(usage.used)
            free_gb = self._bytes_to_gb(usage.free)
            free_percent = round((usage.free / usage.total) * 100, 2) if usage.total else 0.0

            return {
                "status": "ok",
                "message": f"Disk usage retrieved successfully for path: {target_path}",
                "data": {
                    "path": target_path,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "total_gb": total_gb,
                    "used_gb": used_gb,
                    "free_gb": free_gb,
                    "free_percent": free_percent,
                    "os": system_name,
                    "platform_details": platform.platform(),
                },
            }
        except Exception as exc:
            system_name = platform.system()
            target_path = payload.get("path") or self._default_path(system_name)
            return self._error_response(str(exc), target_path, system_name)

    def _default_path(self, system_name: str) -> str:
        return "C:\\" if system_name == "Windows" else "/"

    def _bytes_to_gb(self, value: int) -> float:
        return round(value / (1024**3), 2)

    def _error_response(self, message: str, path: str, system_name: str) -> dict:
        return {
            "status": "error",
            "message": message,
            "data": {
                "path": path,
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "total_gb": 0.0,
                "used_gb": 0.0,
                "free_gb": 0.0,
                "free_percent": 0.0,
                "os": system_name,
                "platform_details": platform.platform(),
            },
        }


--- FILE: app/tools/local/echo_tool.py | bytes=520 | sha256_12=362c9f47cbbe ---
from app.schemas.context import ExecutionContext
from app.tools.base import BaseTool


class EchoTool(BaseTool):
    name = "echo"
    description = "A simple tool that returns the payload it receives."
    read_only = True
    risk_level = "low"

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        return {
            "echo": payload,
            "requested_by": context.username if context else None,
            "request_id": context.request_id if context else None,
        }

--- FILE: app/tools/local/system_info_tool.py | bytes=752 | sha256_12=caeadfc194a6 ---
import platform
import socket

from app.schemas.context import ExecutionContext
from app.tools.base import BaseTool


class SystemInfoTool(BaseTool):
    name = "system_info"
    description = "Returns basic information about the local system."
    read_only = True
    risk_level = "low"

    def run(self, payload: dict, context: ExecutionContext | None = None) -> dict:
        return {
            "requested_by": context.username if context else None,
            "request_id": context.request_id if context else None,
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": socket.gethostname(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

--- FILE: app/tools/registry.py | bytes=1659 | sha256_12=61571b57e438 ---
"""
NUCLEO - TOOL REGISTRY

Catálogo central de herramientas disponibles en el sistema.

Responsable de:
- Registrar tools disponibles (BaseTool)
- Resolver tools por nombre
- Proporcionar acceso a las implementaciones de ejecución

Flujo:
tool_name (desde planner)
    → lookup en registry
    → instancia de tool
    → ejecución (tool.run)

Estructura interna:
dict[str, BaseTool]
{
    "tool_name": tool_instance
}

Funciones:
- register(tool): añade una tool al registro
- get(tool_name): obtiene una tool por nombre
- list_tools(): devuelve todas las tools registradas

Notas:
- Permite desacoplar runtime de implementaciones concretas
- Facilita la extensión sin modificar el núcleo
- Utiliza acceso O(1) mediante diccionario

Limitaciones actuales:
- No evita sobrescritura de tools con mismo nombre
- No valida tipos estrictamente
- No incluye metadata adicional de tools

Arquitectura:
Patrón Service Locator dentro del pipeline:
planner → registry → policy → tool
"""

from app.tools.base import BaseTool
from app.tools.local.disk_info_tool import DiskInfoTool
from app.tools.local.echo_tool import EchoTool
from app.tools.local.system_info_tool import SystemInfoTool


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, tool_name: str) -> BaseTool | None:
        return self._tools.get(tool_name)

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())


registry = ToolRegistry()
registry.register(EchoTool())
registry.register(SystemInfoTool())
registry.register(DiskInfoTool())


--- FILE: docs/EVOLUTION_MAP.md | bytes=3482 | sha256_12=303ff40b3975 ---
# Evolution Map

## Purpose

This document maps the transition from the currently verified system state to a more robust runtime, while distinguishing clearly between implemented, partial, experimental, and future capabilities.

## Current Verified State

The repository currently provides:

- FastAPI entrypoint for runtime execution
- `AgentService` as facade over `AgentRuntime`
- `AgentRuntime` as production orchestrator
- Rule-based `Planner`
- Name-based `PolicyEngine` with role check for `system_info`
- `ToolRegistry` for production tool lookup
- Production tools:
  - `echo`
  - `system_info`
- `ExecutionContext` propagated across API, runtime, policy, and tools
- `AgentResponse` with `status`, `message`, and optional `result`

## Current Experimental State

The repository also contains an isolated experimental lab subsystem:

- capability-gap signal from planner when explicitly requested
- deterministic proposal generation placeholder
- isolated staging registry
- lab-only skeleton generation
- audit artifact generation

This subsystem is implemented but not part of the stable production registry path.

## Main Remaining Weaknesses

### 1. Weak internal contracts

- planner output is still implicit
- tool payload contracts are still implicit
- tool output is not yet standardized beyond current response container

### 2. Incomplete execution control

- `dry_run` is still not structurally enforced for production execution
- policy does not evaluate payload deeply
- `read_only` and `risk_level` metadata are still not policy-enforced

### 3. Runtime robustness gaps

- limited structured exception handling in runtime
- no formal domain error taxonomy

### 4. Bootstrap coupling

- planner, policy engine, registry, and experimental services are still composed at module import time

### 5. Documentation and operational drift risk

- historical documents contain earlier snapshots that must be read as logs, not current truth
- `docs_esp/` is a maintained translation of `docs/`, but not the primary verified source

## Evolution Priorities

### Priority 1 - Reinforce contracts

- introduce typed execution plan
- define structured tool payload contracts
- define stronger tool result contracts
- strengthen `BaseTool` contract

### Priority 2 - Enforce execution control

- make `dry_run` meaningful
- use tool metadata in policy decisions
- prepare payload-aware policy checks

### Priority 3 - Improve runtime robustness

- add controlled error handling by pipeline stage
- standardize domain error responses
- improve traceability

### Priority 4 - Decouple composition from orchestration

- inject planner, registry, and policy into runtime
- move production and lab composition into dedicated bootstrap layer

### Priority 5 - Mature experimental lab

- real review workflow for staging registry
- richer artifact metadata
- explicit promotion process
- real LLM integration only behind controlled boundaries

## Not Yet Recommended

The following should still not be treated as production priorities before contracts and execution control are stronger:

- autonomous tool activation
- production self-extension
- uncontrolled LLM planner authority
- distributed execution
- implicit memory/state orchestration

## Target Outcome

A runtime with:

- explicit contracts
- controlled execution
- stable production registry
- isolated experimental lab
- traceable orchestration
- documentation that clearly separates current state from future vision


--- FILE: docs/architecture.md | bytes=4893 | sha256_12=5353b1c71b9c ---
# Architecture - Verified Current State

## Purpose

This document is the source of truth for architecture that can be verified directly in the current codebase. It describes implemented behavior, explicit experimental behavior, and known limitations when they are observable in code.

## Documentation Convention

This repository separates documentation into layers:

- Verified architecture: implemented and code-verifiable behavior
- Target architecture / vision: intended future design
- Operations: run state, execution rules, and historical logs
- Audits: critical evaluation, risks, gaps, and consistency checks
- Session logs: chronological record of decisions and changes

If a capability is experimental, partial, or future, it must be labeled explicitly.

## Verified Execution Flow

Stable runtime flow:

AgentRequest  
→ AgentService  
→ AgentRuntime  
→ Planner  
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse

The runtime also records an internal in-memory execution trace for each
execution. This trace is not part of the public API response contract.

## Verified Endpoints

- `GET /` -> health response
- `GET /tools` -> list registered production tools
- `POST /agent/run` -> execute agent runtime

## Verified Component Responsibilities

### API

- Receives HTTP requests
- Resolves authentication at request boundary
- Builds `ExecutionContext`
- Delegates to `AgentService`

### AgentService

- Thin service facade over `AgentRuntime`
- Propagates `AgentRequest` and `ExecutionContext`
- Does not own planning, policy, or tool execution

### AgentRuntime

- Coordinates the runtime pipeline
- Calls planner
- Resolves tools through production registry
- Calls policy engine
- Executes production tools
- Records internal planner, policy, and tool steps through the runtime tracer
- Returns `AgentResponse`

### Planner

- Performs simple rule-based planning
- Acts as a deterministic intent-to-candidate-action adapter
- Returns a typed `PlannedAction`
- Does not authorize or execute tools
- Can emit either:
  - `planned`
  - `no_plan`

### PolicyEngine

- Requires authenticated execution context
- Allows `echo`
- Allows `system_info` only for `admin`
- Denies all other production tools by name

### ToolRegistry

- Stores production tool instances in a dictionary
- Resolves tools by `tool.name`
- Is separate from staging and experimental registries

### Production Tools

Currently registered at import time in the production runtime:

- `echo`
- `system_info`
- `disk_info`

### AgentResponse

Current runtime response model contains:

- `status`
- `message`
- `result` optional

`message` is still populated with `str(result)` for backward compatibility.

## Verified Current Contracts

### AgentRequest

Current fields:

- `user_input: str`
- `dry_run: bool = True`
- `experimental_tool_generation: bool = False`

### Planner Output

The planner returns `PlannedAction`.

Current fields:

- `status`
- `tool_name`
- `payload`
- `confidence`
- `reason`
- `source`

`status` can be:

- `planned`
- `no_plan`

`no_plan` is a valid result. It means no deterministic rule matched, so runtime
must not execute any tool.

### PolicyDecision

Current fields:

- `decision`
- `reason`

### Runtime Trace

Internal-only tracing is implemented in `app/runtime/tracing.py`.

`ExecutionTrace` contains:

- `trace_id`
- `request_id`
- `steps`

Each `ExecutionStep` contains:

- `step_id`
- `phase` (`planner`, `policy`, `registry`, or `tool`)
- `input`
- `output`
- `status` (`success`, `denied`, `error`, or `skipped`)
- `error`
- `timestamp`

The first implementation is `InMemoryTracer`. It has no disk persistence and no
external integration.

## Verified Experimental Subsystem

Experimental proposal and staging modules still exist in isolated code and
`runtime_lab/`, but they are not part of the current stable Planner contract.

The current Planner returns only:

- `planned`
- `no_plan`

Experimental generated tools are not auto-registered in the production
`ToolRegistry`.

## Verified Constraints and Limitations

- Planner output is still implicit and not runtime-validated
- `dry_run` is structurally enforced by the runtime: policy is evaluated, the
  tool step is traced, and the production tool is not executed
- Policy is still largely name-based
- Tool metadata such as `read_only` and `risk_level` are not yet enforced by policy
- Production bootstrap still happens at module import time in `orchestrator.py`
- Error handling in runtime is still limited

## Explicitly Not Verified

The following must not be described as implemented production behavior:

- Real LLM-backed planning
- Auto-extension of production registry
- Dynamic package installation
- Arbitrary shell execution
- Autonomous promotion from staging to production

Those behaviors are either not implemented or only documented as future direction elsewhere.


--- FILE: docs/architecture/llm_tool_expansion.md | bytes=1184 | sha256_12=d9f6c702a179 ---
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


--- FILE: docs/audits/docs_esp_sync_audit.md | bytes=4698 | sha256_12=c0ee283f1eb9 ---
# docs_esp Sync Audit

## Date

2026-04-19

## Purpose

Record the synchronization of `docs_esp/` with `docs/` so that the Spanish tree becomes a complete, maintained translation of the primary documentation set.

## Scope

- full inventory of `docs/`
- full inventory of `docs_esp/`
- one-to-one mapping between both trees
- controlled translation of missing or outdated content
- normalization of divergent filenames in `docs_esp/`

## Rule Applied

- `docs/` remains the source of truth
- `docs_esp/` must reflect `docs/` faithfully
- system component names remain in English
- unpaired legacy content is moved to `_deprecated/`

## Files Mapped

- `docs/architecture.md` -> `docs_esp/architecture.md`
- `docs/EVOLUTION_MAP.md` -> `docs_esp/EVOLUTION_MAP.md`
- `docs/vision/architecture_vision.md` -> `docs_esp/vision/architecture_vision.md`
- `docs/architecture/llm_tool_expansion.md` -> `docs_esp/architecture/llm_tool_expansion.md`
- `docs/planning/development_plan.md` -> `docs_esp/planning/development_plan.md`
- `docs/operations/operational_state.md` -> `docs_esp/operations/operational_state.md`
- `docs/operations/dev_state_snapshot.md` -> `docs_esp/operations/dev_state_snapshot.md`
- `docs/operations/session_log.md` -> `docs_esp/operations/session_log.md`
- `docs/operations/session_log_docs_normalization.md` -> `docs_esp/operations/session_log_docs_normalization.md`
- `docs/operations/session_log_llm_tool_expansion.md` -> `docs_esp/operations/session_log_llm_tool_expansion.md`
- `docs/operations/session_log_docs_esp_sync.md` -> `docs_esp/operations/session_log_docs_esp_sync.md`
- `docs/modules/agent_service.md` -> `docs_esp/modules/agent_service.md`
- `docs/modules/orchestrator.md` -> `docs_esp/modules/orchestrator.md`
- `docs/modules/planner.md` -> `docs_esp/modules/planner.md`
- `docs/modules/policy_engine.md` -> `docs_esp/modules/policy_engine.md`
- `docs/modules/tool_registry.md` -> `docs_esp/modules/tool_registry.md`
- `docs/modules/base_tool.md` -> `docs_esp/modules/base_tool.md`
- `docs/modules/tool_proposal_service.md` -> `docs_esp/modules/tool_proposal_service.md`
- `docs/modules/tool_generation_service.md` -> `docs_esp/modules/tool_generation_service.md`
- `docs/modules/staging_registry.md` -> `docs_esp/modules/staging_registry.md`
- `docs/modules/audit_store.md` -> `docs_esp/modules/audit_store.md`
- `docs/audits/repo_audit.md` -> `docs_esp/audits/repo_audit.md`
- `docs/audits/files_audit.md` -> `docs_esp/audits/files_audit.md`
- `docs/audits/documentation_consistency_audit.md` -> `docs_esp/audits/documentation_consistency_audit.md`
- `docs/audits/docs_esp_sync_audit.md` -> `docs_esp/audits/docs_esp_sync_audit.md`

## Files Created in docs_esp

- `docs_esp/architecture/llm_tool_expansion.md`
- `docs_esp/operations/session_log_docs_normalization.md`
- `docs_esp/operations/session_log_llm_tool_expansion.md`
- `docs_esp/operations/session_log_docs_esp_sync.md`
- `docs_esp/modules/tool_proposal_service.md`
- `docs_esp/modules/tool_generation_service.md`
- `docs_esp/modules/staging_registry.md`
- `docs_esp/modules/audit_store.md`
- `docs_esp/audits/repo_audit.md`
- `docs_esp/audits/files_audit.md`
- `docs_esp/audits/documentation_consistency_audit.md`
- `docs_esp/audits/docs_esp_sync_audit.md`

## Files Updated in docs_esp

- `docs_esp/architecture.md`
- `docs_esp/EVOLUTION_MAP.md`
- `docs_esp/vision/architecture_vision.md`
- `docs_esp/planning/development_plan.md`
- `docs_esp/operations/operational_state.md`
- `docs_esp/operations/dev_state_snapshot.md`
- `docs_esp/operations/session_log.md`
- `docs_esp/modules/agent_service.md`
- `docs_esp/modules/orchestrator.md`
- `docs_esp/modules/planner.md`
- `docs_esp/modules/policy_engine.md`
- `docs_esp/modules/tool_registry.md`
- `docs_esp/modules/base_tool.md`

## Files Moved to Deprecated

- `docs_esp/audits/repo.audit.md` -> `docs_esp/_deprecated/audits/repo.audit.md`
- `docs_esp/audits/files.audit.md` -> `docs_esp/_deprecated/audits/files.audit.md`

## Issues Found

- `docs_esp/` did not cover the full `docs/` tree
- legacy filenames in `docs_esp/audits/` no longer matched primary naming
- experimental module coverage was incomplete
- earlier mirror notes were not enough to guarantee semantic parity

## Decisions Taken

- sync `docs_esp/` structurally one-to-one with `docs/`
- add a header to every translated file with source path and last sync date
- keep component and module names in English
- keep `docs/` as the primary verified source even after sync

## Unverifiable Content

- no new technical claims were introduced beyond what `docs/` already stated
- when `docs/` marks a capability as partial or not verified, `docs_esp/` preserves the same certainty level


--- FILE: docs/audits/documentation_consistency_audit.md | bytes=7240 | sha256_12=4a69166ceccb ---
# Documentation Consistency Audit

## Scope

Full Markdown audit for NUCLEO repository documentation, excluding third-party or environment-vendored Markdown under `.venv/`.

## Documentary Convention Applied

Documentation is normalized into these layers:

- Verified architecture
- Target architecture / vision
- Operations
- Audit
- Session log

Primary source of truth:

- `docs/`

Maintained translation:

- `docs_esp/`

When conflict exists between documentation and code, code is treated as the higher-confidence source.

## Inventory of Markdown Files

### Root

- `README.md` -> repository overview, quick start, verified runtime summary -> operation + entrypoint overview

### Primary docs

- `docs/architecture.md` -> verified architecture
- `docs/EVOLUTION_MAP.md` -> evolution roadmap from current state
- `docs/vision/architecture_vision.md` -> target architecture
- `docs/planning/development_plan.md` -> planned technical priorities
- `docs/operations/operational_state.md` -> current operational state
- `docs/operations/dev_state_snapshot.md` -> point-in-time implementation snapshot
- `docs/operations/session_log.md` -> historical engineering log
- `docs/operations/session_log_llm_tool_expansion.md` -> session log for lab subsystem
- `docs/modules/agent_service.md` -> module documentation
- `docs/modules/orchestrator.md` -> module documentation
- `docs/modules/planner.md` -> module documentation
- `docs/modules/policy_engine.md` -> module documentation
- `docs/modules/tool_registry.md` -> module documentation
- `docs/modules/base_tool.md` -> module documentation
- `docs/modules/tool_proposal_service.md` -> experimental module documentation
- `docs/modules/tool_generation_service.md` -> experimental module documentation
- `docs/modules/staging_registry.md` -> experimental module documentation
- `docs/modules/audit_store.md` -> experimental module documentation
- `docs/architecture/llm_tool_expansion.md` -> experimental architecture note
- `docs/audits/repo_audit.md` -> repository structure audit
- `docs/audits/files_audit.md` -> coverage audit
- `docs/audits/documentation_consistency_audit.md` -> documentation consistency audit

### Maintained translation

- `docs_esp/architecture.md`
- `docs_esp/EVOLUTION_MAP.md`
- `docs_esp/vision/architecture_vision.md`
- `docs_esp/architecture/llm_tool_expansion.md`
- `docs_esp/planning/development_plan.md`
- `docs_esp/operations/operational_state.md`
- `docs_esp/operations/dev_state_snapshot.md`
- `docs_esp/operations/session_log.md`
- `docs_esp/operations/session_log_docs_normalization.md`
- `docs_esp/operations/session_log_llm_tool_expansion.md`
- `docs_esp/operations/session_log_docs_esp_sync.md`
- `docs_esp/modules/agent_service.md`
- `docs_esp/modules/orchestrator.md`
- `docs_esp/modules/planner.md`
- `docs_esp/modules/policy_engine.md`
- `docs_esp/modules/tool_registry.md`
- `docs_esp/modules/base_tool.md`
- `docs_esp/modules/tool_proposal_service.md`
- `docs_esp/modules/tool_generation_service.md`
- `docs_esp/modules/staging_registry.md`
- `docs_esp/modules/audit_store.md`
- `docs_esp/audits/repo_audit.md`
- `docs_esp/audits/files_audit.md`
- `docs_esp/audits/documentation_consistency_audit.md`
- `docs_esp/audits/docs_esp_sync_audit.md`

## Contradictions Detected

### 1. Architecture current state vs historical auth notes

Conflict:
- `docs/architecture.md` mixed verified runtime notes with a historical auth-design section.

Decision:
- Normalize `docs/architecture.md` into verified architecture only.
- Keep auth as part of verified current state, not as a future note.

### 2. Response structure

Conflict:
- older docs stated response was only `status + message`
- code now includes optional `result`

Decision:
- all primary docs updated to describe `result` as current verified behavior
- historical logs preserved as logs, not current truth

### 3. ExecutionContext status

Conflict:
- some operational docs said “do not introduce ExecutionContext yet”
- code already includes request-scoped execution context

Decision:
- primary operational docs updated to current verified state
- historical statements retained only inside session log as historical context

### 4. Experimental lab path vs production path

Conflict:
- older docs did not mention experimental lab
- new docs described it, but not always distinguished from production flow

Decision:
- primary docs now separate:
  - stable production runtime
  - isolated experimental lab

### 5. Policy behavior

Conflict:
- several docs described whitelist-only policy
- code now also checks authentication and admin role for `system_info`

Decision:
- primary docs updated to reflect current verified policy behavior

### 6. Planner behavior

Conflict:
- older docs described only `system_info` / `echo` branch
- code now also has opt-in capability-gap signaling

Decision:
- primary docs updated to describe both:
  - stable production behavior
  - experimental opt-in branch

### 7. docs vs docs_esp

Conflict:
- `docs_esp/` was partial and could contradict primary docs

Decision:
- synchronize `docs_esp/` as a maintained translation of `docs/`
- keep `docs/` as the primary verified source

## Contradictions Not Fully Resolved

### runtime_lab persistence operability

Reason:
- code implements file-backed lab persistence
- repository session could not fully verify artifact writing behavior in current sandbox environment

Decision:
- document as implemented code path
- avoid claiming full operational verification

### dispatcher role

Reason:
- `runtime/dispatcher.py` exists but is not integrated in runtime flow

Decision:
- describe it as present but not integrated

## Redundant or Overlapping Documents

- `docs/operations/operational_state.md` and `docs/operations/dev_state_snapshot.md` overlap but now serve different scopes:
  - operational state = current operating model
  - dev snapshot = point-in-time implementation snapshot
- `docs/architecture.md` and `docs/vision/architecture_vision.md` overlap in topic but now differ clearly by time horizon
- `docs_esp/` overlaps with `docs/`, but is now treated as a maintained translation, not the primary verified documentation

## Recommended Documentation Hierarchy

1. `README.md` -> repository entry
2. `docs/architecture.md` -> verified architecture
3. `docs/vision/architecture_vision.md` -> future design
4. `docs/operations/*` -> state and logs
5. `docs/modules/*` -> component-level detail
6. `docs/audits/*` -> critical evaluation
7. `docs_esp/*` -> maintained translation

## Files Modified During Normalization

- `README.md`
- `docs/architecture.md`
- `docs/vision/architecture_vision.md`
- `docs/EVOLUTION_MAP.md`
- `docs/operations/operational_state.md`
- `docs/operations/dev_state_snapshot.md`
- `docs/operations/session_log.md`
- `docs/planning/development_plan.md`
- `docs/modules/agent_service.md`
- `docs/modules/orchestrator.md`
- `docs/modules/planner.md`
- `docs/modules/policy_engine.md`
- `docs/modules/tool_registry.md`
- `docs/modules/base_tool.md`
- `docs/audits/repo_audit.md`
- `docs/audits/files_audit.md`
- `docs/audits/documentation_consistency_audit.md`
- `docs/operations/session_log_docs_normalization.md`
- `docs_esp/*.md` files marked as translation mirror


--- FILE: docs/audits/files_audit.md | bytes=1068 | sha256_12=f44945781e2a ---
# Files Audit

## Layer

Audit

## Purpose

Track which technical files and modules are covered by documentation or repository audit.

## Covered Production Runtime Modules

- `app/services/agent_service.py`
- `app/runtime/orchestrator.py`
- `app/runtime/planner.py`
- `app/policies/engine.py`
- `app/tools/base.py`
- `app/tools/registry.py`

## Covered Experimental Lab Modules

- `app/services/tool_proposal/tool_proposal_service.py`
- `app/services/tool_generation/tool_generation_service.py`
- `app/services/staging/staging_registry.py`
- `app/services/audit/audit_store.py`
- `app/domain/tool_proposals/models.py`
- `app/domain/staging/models.py`
- `app/schemas/tool_proposal.py`

## Structurally Reviewed

- `app/main.py`
- `app/api/routes/*`
- `app/api/deps/auth.py`
- `app/schemas/*`
- `app/runtime/dispatcher.py`
- `runtime_lab/*`

## Summary

Repository coverage is sufficient to describe the stable execution path and the current isolated lab path. The main remaining documentation risk is historical drift across files rather than lack of module coverage.


--- FILE: docs/audits/repo_audit.md | bytes=1974 | sha256_12=a4cf8239ac6b ---
# Repo Audit

## Layer

Audit

## Purpose

Evaluate repository structure, module boundaries, naming consistency, and fit between physical layout and architectural intent.

## Current Repository Shape

High-level structure verified in the repository:

- `app/`
- `docs/`
- `docs_esp/`
- `runtime_lab/`

### Application structure

- `api/` -> HTTP routes and auth boundary
- `services/` -> service-layer and lab services
- `runtime/` -> orchestration and planning
- `policies/` -> execution control
- `tools/` -> production tools
- `schemas/` -> request, response, and experimental schemas
- `domain/` -> lab domain entities

### Documentation structure

- `docs/architecture.md` -> verified architecture
- `docs/vision/` -> target vision
- `docs/operations/` -> operational state and session logs
- `docs/audits/` -> audits
- `docs/modules/` -> per-module documentation
- `docs/planning/` -> development roadmap

### Experimental runtime-lab structure

- `runtime_lab/proposals/`
- `runtime_lab/generated_tools/`
- `runtime_lab/staging_registry/`
- `runtime_lab/audit/`

## Structural Strengths

- Clear separation between production runtime and lab artifacts
- Reasonable package boundaries for current scale
- Documentation structure can support multiple documentary layers

## Structural Risks

- Production runtime composition is still embedded in runtime module
- `docs_esp/` is now maintained as a translation tree, but can still drift if updates are not synchronized
- `runtime_lab/` persistence is operationally separate but still colocated in repo workspace

## Naming Assessment

Current primary names are coherent and should remain stable:

- runtime
- orchestrator
- planner
- policy engine
- tool registry
- tool
- staging
- audit
- proposal
- lab / runtime_lab

## Overall Assessment

The repository is still structurally coherent, but documentation drift and import-time composition remain the main architecture-level risks rather than raw directory disorder.


--- FILE: docs/modules/agent_service.md | bytes=750 | sha256_12=c7e7b03b256e ---
# AgentService

## Layer

Verified architecture

## Purpose

Provide a stable service-layer facade between API routes and runtime orchestration.

## Verified Current Behavior

`AgentService` currently:

- instantiates `AgentRuntime`
- exposes `run(request, context)`
- delegates execution directly to runtime

It does not currently own:

- planning
- policy
- tool execution
- lab proposal generation logic

## Strengths

- Keeps API thin
- Preserves a stable entrypoint
- Clean place for future tracing or orchestration hooks

## Current Limitations

- Runtime dependency is still constructed directly
- No independent error normalization boundary yet

## Status Label

- Service facade: implemented
- Dependency injection boundary: not implemented


--- FILE: docs/modules/audit_store.md | bytes=420 | sha256_12=c66f5fe73a6c ---
# AuditStore

## Responsibility

`AuditStore` persists simple structured audit events for the experimental tool-expansion
workflow.

## Event fields

- event
- timestamp
- proposal_id
- action
- result
- artifact_paths
- metadata

## Output

Each event is written as a JSON file under `runtime_lab/audit/`.

## Notes

- The store is append-only at this stage.
- Audit artifacts support review and post-hoc traceability.


--- FILE: docs/modules/base_tool.md | bytes=646 | sha256_12=691a546cb9aa ---
# BaseTool

## Layer

Verified architecture

## Purpose

Define the common conceptual interface for production tools.

## Verified Current Behavior

`BaseTool` currently declares:

- `name`
- `description`
- `read_only`
- `risk_level`
- `run(payload, context=None)`

Concrete tools are expected to implement `run(...)`.

## Important Current Reality

- `BaseTool` is not a strict abstract base class
- metadata is not validated at construction time
- metadata is not yet enforced by policy
- input/output contracts remain implicit

## Status Label

- Common tool contract concept: implemented
- Strong typed contract enforcement: not implemented


--- FILE: docs/modules/orchestrator.md | bytes=2011 | sha256_12=8a11ff1a6e68 ---
# AgentRuntime

## Layer

Verified architecture

## Purpose

Central execution orchestrator of the production runtime.

## Verified Current Behavior

`AgentRuntime.run(request, context)` currently:

1. starts an internal in-memory execution trace
2. asks the planner for a `PlannedAction`
3. records the planner step
4. validates that the planner returned `PlannedAction`
5. if the plan is `no_plan`, returns a controlled `no_plan` response
6. otherwise extracts candidate `tool_name` and `payload`
7. resolves the tool from production `ToolRegistry`
8. records the registry step
9. if missing, records the registry step as `error` and returns `error`
10. asks `PolicyEngine` for authorization
11. records the policy step
12. if denied, returns `blocked`
14. if `dry_run=True`, records a tool step as `skipped` with `executed=False` and does not run the tool
15. otherwise executes `tool.run(payload, context=context)`
16. records success or error for the tool step
17. returns `AgentResponse`

## Internal Trace Contract

Tracing is implemented in `app/runtime/tracing.py` and is intentionally
in-memory only.

`ExecutionTrace`:

- `trace_id`
- `request_id`
- `steps`

`ExecutionStep`:

- `step_id`
- `phase`: `planner`, `policy`, `registry`, or `tool`
- `input`
- `output`
- `status`: `success`, `denied`, `error`, or `skipped`
- `error`
- `timestamp`

Tracer failures are isolated from authorization and execution decisions. A
tracing failure must not cause a denied tool to execute and must not hide a real
tool error.

## Current Strengths

- Clear production pipeline
- Explicit policy check before production tool execution
- Explicit handling of missing production tool
- Minimal internal trace for planner, policy, registry, and tool stages

## Current Limitations

- Runtime composition still happens at import time
- Limited exception handling
- Response still duplicates data between `message` and `result`

## Status Label

- Production path: implemented
- Full contract hardening: not implemented


--- FILE: docs/modules/planner.md | bytes=1283 | sha256_12=d0dd522d5cec ---
# Planner

## Layer

Verified architecture

## Purpose

Transform an `AgentRequest` into a deterministic candidate action.

The planner proposes. It does not authorize, resolve runtime truth, or execute.

## Verified Current Behavior

The planner currently:

1. normalizes `request.user_input` with `strip().lower()`
2. if `request.tool` is set and the tool exists in `ToolRegistry`, returns `planned`
3. evaluates a small explicit table of deterministic rules
4. if a rule matches and its tool exists in `ToolRegistry`, returns `planned`
5. otherwise returns `no_plan`

## Contract Observed in Code

Current output is `PlannedAction`.

Fields:

- `status`
- `tool_name`
- `payload`
- `confidence`
- `reason`
- `source`

Statuses:

- `planned`
- `no_plan`

`no_plan` is expected when no deterministic rule matches.

## Strengths

- Deterministic
- Side-effect free in production path
- Easy to read
- Rules are table-driven and auditable
- Planner checks rule targets against `ToolRegistry`
- Runtime receives a typed contract instead of an implicit dict

## Current Limitations

- Matching logic is weak and heuristic-based
- Strong coupling to literal production tool names remains

## Status Label

- Production planning: implemented
- Real LLM-assisted planning: not implemented


--- FILE: docs/modules/policy_engine.md | bytes=914 | sha256_12=1db089b5a807 ---
# PolicyEngine

## Layer

Verified architecture

## Purpose

Validate whether a planned production tool execution is allowed before reaching the execution stage.

## Verified Current Behavior

`PolicyEngine.evaluate(...)` currently:

- denies unauthenticated requests
- allows `echo`
- allows `system_info` only when `admin` is present in roles
- denies any other tool name

It returns a `PolicyDecision` with:

- `decision`
- `reason`

## What It Does Not Currently Do

- it does not deeply evaluate payload
- it does not enforce meaningful `dry_run`
- it does not use `read_only` or `risk_level`
- it does not govern lab artifact generation directly

## Strengths

- deny-by-default shape
- clear separation from execution
- authenticated context is part of decision path

## Status Label

- Production authorization: implemented
- Metadata-aware policy: not implemented
- Lab promotion control: not implemented


--- FILE: docs/modules/staging_registry.md | bytes=440 | sha256_12=16ded85cfc81 ---
# StagingRegistry

## Responsibility

`StagingRegistry` is a JSON-backed isolated registry for experimental proposals.

## Supported statuses

- `draft`
- `generated`
- `reviewed`
- `approved`
- `rejected`

## Persistence

Registry state is stored in `runtime_lab/staging_registry/registry.json`.

## Notes

- This registry is intentionally separate from `app/tools/registry.py`.
- Approval in staging does not imply production activation.


--- FILE: docs/modules/tool_generation_service.md | bytes=434 | sha256_12=82fdafb58574 ---
# ToolGenerationService

## Responsibility

`ToolGenerationService` converts an experimental proposal into lab-only artifacts:

- Python tool skeleton
- Placeholder test file
- Minimal metadata

## Output

Artifacts are written under `runtime_lab/generated_tools/<tool_name>/`.

## Notes

- Generated files are not auto-registered in production.
- Output is intended for review, not direct execution rollout.
- Generation is audited.


--- FILE: docs/modules/tool_proposal_service.md | bytes=512 | sha256_12=de318fe790ae ---
# ToolProposalService

## Responsibility

`ToolProposalService` creates deterministic experimental proposals when the planner
detects a capability gap. The current version does not call a real LLM; it acts as a
stable placeholder that emits structured proposal JSON.

## Output

The service writes proposal artifacts to `runtime_lab/proposals/<proposal_id>.json`.

## Notes

- The proposal is descriptive, not executable.
- Proposal generation is audited.
- The service is isolated from the production registry.


--- FILE: docs/modules/tool_registry.md | bytes=874 | sha256_12=8f43370c32cf ---
# ToolRegistry

## Layer

Verified architecture

## Purpose

Resolve production tools by name from the current in-memory production registry.

## Verified Current Behavior

`ToolRegistry` stores tool instances in a dictionary keyed by `tool.name`.

Supported operations:

- `register(tool)`
- `get(tool_name)`
- `list_tools()`

## Important Distinction

This registry is the production registry. It is separate from:

- `runtime_lab/`
- staging registry
- proposal store
- generated tool skeletons

Generated lab tools are not auto-registered here.

## Current Limitations

- duplicate names overwrite silently
- tool contract is not strongly validated at registration time
- runtime mutation and bootstrap-time mutation are not clearly separated

## Status Label

- Production registry: implemented
- Staging / promotion integration: not implemented in production registry


--- FILE: docs/operations/dev_state_snapshot.md | bytes=1356 | sha256_12=bf4362d1f8ab ---
# Development State Snapshot - NUCLEO

## Snapshot Date

2026-04-19

## Purpose

Capture a concise point-in-time view of repository state after the introduction of the experimental lab path and the documentation normalization pass.

## Verified Current Runtime Shape

- FastAPI backend
- request-scoped API key authentication
- `ExecutionContext` propagation
- production runtime:
  - planner
  - policy
  - registry
  - tools
- production tools:
  - `echo`
  - `system_info`
- response carries:
  - `status`
  - `message`
  - `result` optional

## Verified Experimental Additions

- `app/domain/tool_proposals/`
- `app/domain/staging/`
- `app/services/tool_proposal/`
- `app/services/tool_generation/`
- `app/services/staging/`
- `app/services/audit/`
- `runtime_lab/`

These additions are isolated from production registry activation.

## Current Gaps

- planner contract still implicit
- dry-run not yet enforced structurally
- runtime error model still limited
- lab artifact persistence behavior depends on environment write permissions and has not been fully validated in this repository session

## Documentation Convention Snapshot

- `docs/` = primary source of truth
- `docs_esp/` = maintained translation of `docs/`, but not the primary source of verified truth
- new consistency audit stored in `docs/audits/documentation_consistency_audit.md`


--- FILE: docs/operations/operational_state.md | bytes=2781 | sha256_12=cb9ac6c92926 ---
# Operational State - NUCLEO

## Purpose

Describe the current operational state of the system using only behavior that is verified in code or directly implied by repository structure.

## Current Objective

Operate a minimal, controlled modular agent runtime on FastAPI while keeping the production execution path understandable and isolated from experimental lab capabilities.

## Current Verified Architecture

Production flow:

AgentRequest  
→ AgentService  
→ AgentRuntime  
→ Planner  
→ ToolRegistry  
→ PolicyEngine  
→ Tool  
→ AgentResponse

## Components in Current Operation

### API

- FastAPI application
- `POST /agent/run`
- `GET /tools`
- `GET /`

### AgentService

- Thin facade over runtime
- Delegates execution with request and execution context

### Runtime

- Coordinates planner, policy, registry, tool execution
- Validates planner output before registry, policy, or tool execution
- Returns `no_plan` without executing tools when planner has no deterministic match

### Planner

- Rule-based
- Uses a small explicit table of deterministic rules
- Returns typed `PlannedAction`
- Emits `planned` or `no_plan`
- Does not authorize or execute tools

### PolicyEngine

- Deny-by-default on production tool names
- Allows `echo`
- Allows `system_info` only for admin context

### Production Tools

- `echo`
- `system_info`
- `disk_info`

### Experimental Lab

- Proposal generation service
- Tool skeleton generation service
- Staging registry
- Audit store
- All isolated under `runtime_lab/`

## Verified Technical Characteristics

- `ExecutionContext` is currently part of the runtime pipeline
- `AgentResponse` currently exposes structured `result`
- Production tool registration happens in the production tool registry
- Planner output is typed as `PlannedAction`
- `dry_run` is structurally enforced: tools are not executed
- Production policy does not deeply evaluate payload
- Experimental generated tools are not auto-registered in production

## Operational Constraints

- Single-machine local execution is the current explicit operating model
- Production and lab paths coexist in the codebase but must remain separated
- Experimental generation is request-gated, not ambient behavior
- Runtime simplicity is still prioritized over aggressive expansion

## Open Issues

- No complete payload validation per tool
- No full structured runtime error taxonomy
- Runtime trace is in-memory only and not exposed through API
- No production promotion workflow for lab-generated tools

## Working Rules

- Keep production runtime stable first
- Treat `docs/architecture.md` as source of truth for verified behavior
- Treat `docs/vision/architecture_vision.md` as future-only
- Treat experimental lab as isolated and non-production by default


--- FILE: docs/operations/session_log.md | bytes=5576 | sha256_12=a5779fb88641 ---
# Session Log

## 2026-04-10

- Implemented runtime orchestration.
- Added `echo` and `system_info` tools.
- Introduced a first policy layer.
- Attempted execution-context integration.
- Rolled back the first context attempt due to excessive refactor scope.

## 2026-04-11

- Audited:
  - `main.py`
  - `api/routes/agent.py`
  - `runtime/orchestrator.py`
- Clarified runtime structure:
  - API → AgentService → Runtime → Planner → Policy → Registry → Tool → Response
- Identified limitations:
  - no execution tracing
  - global dependencies in runtime
  - simple planner
  - basic policy engine
  - response not structured

## 2026-04-12

- Continued system audit over:
  - planner
  - policy engine
  - tool registry
  - base tool
  - tool implementations
- Verified planner → policy → registry → tool flow.
- Restructured tools toward `tools/local/`.
- Added reserved or preparatory directories:
  - `clients/`
  - `audit/`
  - `runtime/dispatcher.py`
- Introduced `AgentService` as a separate service layer.

## 2026-04-13

- Completed technical audit of:
  - AgentService
  - AgentRuntime
  - Planner
  - PolicyEngine
  - ToolRegistry
  - BaseTool
- Identified critical gaps:
  - implicit contracts
  - no enforced dry-run
  - limited runtime error handling
  - unstructured tool output
  - name-based policy
- Reorganized documentation into:
  - architecture
  - vision
  - planning
  - operations
  - audits

## 2026-04-13 - Authentication and ExecutionContext Integration

- Implemented request-scoped API-key authentication.
- Added `ExecutionContext`.
- Propagated context through:
  - route dependency
  - AgentService
  - AgentRuntime
  - PolicyEngine
  - tools
- Verified role-aware policy behavior for `system_info`.

## 2026-04-18 - Structured Result Preservation

- Modified:
  - `app/schemas/responses.py`
  - `app/runtime/orchestrator.py`
- Preserved structured tool output in `AgentResponse.result`.
- Kept `message=str(result)` for backward compatibility.

## 2026-04-19 - Experimental LLM Tool Expansion Skeleton

- Added isolated experimental modules for:
  - tool proposals
  - tool generation
  - staging registry
  - audit store
- Added `experimental_tool_generation` request flag.
- Added planner capability-gap signaling.
- Added controlled runtime branch for:
  - proposal creation
  - staging registration
  - skeleton generation
  - audit artifact generation
- Kept production tool registry unchanged.
- Real LLM integration remains unimplemented.

## 2026-04-19 - Documentation Normalization

- Audited Markdown documentation across the repository.
- Defined documentation layers:
  - verified architecture
  - target vision
  - operations
  - audits
  - session logs
- Normalized primary docs under `docs/`.
- Marked `docs_esp/` as translation mirror rather than primary verified source.
- Added:
  - `docs/audits/documentation_consistency_audit.md`
  - `docs/operations/session_log_docs_normalization.md`

## 2026-04-19 - `disk_info` Tool Integration

- Implemented:
  - `app/tools/local/disk_info_tool.py`
  - `DiskInfoTool`
  - `name = "disk_info"`
- Confirmed tool contract:
  - read-only tool
  - standard library only
  - uses `shutil.disk_usage`
  - cross-platform default path behavior:
    - Windows → `C:\\`
    - Linux/macOS → `/`
- Corrected semantic naming from `memory_info` to `disk_info`.
- Updated planner behavior to support:
  - explicit `tool` + `payload`
  - `disk_info` resolution from text input
  - optional `path=...` extraction without overriding structured payload
- Updated policy whitelist to allow `disk_info`.
- Resolved runtime failure `Planner requested unknown tool: disk_info`.
- Identified and fixed registry wiring issue:
  - duplicated `ToolRegistry()` instances
  - missing `DiskInfoTool()` registration
  - centralized shared registry instance for runtime and API routes
- Validated end-to-end flow:
  - API → Planner → Policy → Registry → Tool → Response
- Recorded successful real execution result for `path = C:\\`:
  - `total_gb = 236.55`
  - `used_gb = 228.43`
  - `free_gb = 8.11`
  - `free_percent = 3.43`
  - `os = Windows`
- Documented pending improvement:
  - API response remains double-encapsulated
  - `message` contains serialized JSON
  - `result` contains the actual structured payload
- Marked `disk_info` integration as functional.
- Next steps:
  - clean response layer
  - add more local system-observation tools

## 2026-04-23

- Recovered system baseline after rollback
- Identified critical issues:
  - PolicyDecision not closed
  - Policy/Registry drift risk
  - Missing deterministic runner
- Entering HARDENING phase (contracts + determinism)

## 2026-04-25

- Added minimal internal runtime tracing:
  - `ExecutionTrace`
  - `ExecutionStep`
  - `Tracer`
  - `InMemoryTracer`
- Integrated tracing in `AgentRuntime` for:
  - planner result
  - policy decision
  - registry resolution
  - tool execution or dry-run skip
- Kept trace internal and out of the public `AgentResponse` contract.
- Enforced `dry_run=True` as non-executing runtime behavior while still tracing
  the intended tool step as `skipped`.
- Added unittest coverage for allowed, denied, dry-run, unknown-tool, tool-error,
  tracer-failure, and API response-contract behavior.
- Hardened planner contract:
  - added typed `PlannedAction`
  - reduced planner statuses to `planned` and `no_plan`
  - made `no_plan` a valid non-executing result
  - made runtime stop before policy when planner output is invalid
  - made runtime validate `ToolRegistry` before policy authorization


--- FILE: docs/operations/session_log_docs_esp_sync.md | bytes=1208 | sha256_12=b8007ddc04ce ---
# Session Log - docs_esp Sync

## Date

2026-04-19

## Objective

Synchronize `docs_esp/` with `docs/` so that the Spanish tree becomes a complete, consistent, maintained translation of the primary NUCLEO documentation.

## Scope

- complete inventory of `docs/`
- complete inventory of `docs_esp/`
- one-to-one mapping across both trees
- controlled translation of missing or outdated content
- normalization of divergent legacy filenames in `docs_esp/`

## Synchronized Files

25 translated equivalents to the primary `docs/` tree, plus movement of two legacy audit files into `_deprecated/`.

## Problems Found

- `docs_esp/` did not cover the full `docs/` tree
- legacy filenames remained in `docs_esp/audits/`
- experimental module coverage was incomplete
- earlier translation-mirror notes did not provide enough maintainability by themselves

## Criteria Applied

- semantic fidelity one-to-one with `docs/`
- explanation and context translated into Spanish
- component names, module names, and code identifiers preserved in English
- exact preservation of implementation status labels:
  - implemented
  - experimental
  - partial
  - future
- `docs/` retained as the primary source in case of doubt


--- FILE: docs/operations/session_log_docs_normalization.md | bytes=1953 | sha256_12=b59ccf8283a9 ---
# Session Log - Documentation Normalization

## Date

2026-04-19

## Objective

Audit and normalize repository Markdown documentation so that the same component is described consistently across files and current verified behavior is separated from future vision.

## Files Reviewed

- `README.md`
- all primary docs under `docs/`
- all translation mirror docs under `docs_esp/`

## Files Modified

- `README.md`
- `docs/architecture.md`
- `docs/vision/architecture_vision.md`
- `docs/EVOLUTION_MAP.md`
- `docs/operations/operational_state.md`
- `docs/operations/dev_state_snapshot.md`
- `docs/operations/session_log.md`
- `docs/planning/development_plan.md`
- `docs/modules/agent_service.md`
- `docs/modules/orchestrator.md`
- `docs/modules/planner.md`
- `docs/modules/policy_engine.md`
- `docs/modules/tool_registry.md`
- `docs/modules/base_tool.md`
- `docs/audits/repo_audit.md`
- `docs/audits/files_audit.md`
- `docs/audits/documentation_consistency_audit.md`
- translation-mirror notes added across `docs_esp/`

## Unification Criteria

- code over documentation when conflict existed
- `docs/` treated as primary source of truth
- explicit labels for:
  - implemented
  - experimental
  - future
  - historical log
- stable terminology for:
  - runtime
  - orchestrator
  - planner
  - policy engine
  - tool registry
  - tool
  - staging
  - proposal
  - audit
  - lab / runtime_lab

## Contradictions Resolved

- response shape updated to include structured `result`
- `ExecutionContext` reflected as current verified behavior
- policy behavior updated to include auth and admin rule for `system_info`
- planner documentation updated to include experimental capability-gap branch
- architecture and vision separated cleanly

## Open Uncertainties

- full runtime_lab persistence behavior was not fully operationally verified in this sandbox session
- `docs_esp/` synchronization depends on future changes continuing to update both trees together


--- FILE: docs/operations/session_log_llm_tool_expansion.md | bytes=896 | sha256_12=d3e47be613ec ---
# Session Log - LLM Tool Expansion

## Scope

Initial experimental implementation of controlled tool proposal and skeleton generation.

## Implemented

- Deterministic proposal generation placeholder
- Isolated staging registry
- File-based audit store
- Tool skeleton generation in runtime lab
- Minimal planner/orchestrator integration behind request opt-in

## Verification Note

The code path is implemented in the repository, but full end-to-end operational verification of runtime-lab file persistence was not completed in the current sandbox session. It should therefore be read as implemented code with partial operational verification, not as a fully exercised production-ready workflow.

## Explicitly not implemented

- Real LLM integration
- Production tool auto-registration
- Dynamic package installation
- Arbitrary shell execution
- Automatic policy promotion for generated tools


--- FILE: docs/planning/development_plan.md | bytes=2174 | sha256_12=2b77502f3ebe ---
# Development Plan - NUCLEO

## Purpose

Define the next technical steps from the currently verified repository state without presenting future goals as implemented behavior.

## Current Base

Verified today:

- stable production runtime path
- request-scoped authentication with execution context
- structured `result` preserved in response
- isolated experimental lab for tool proposal and skeleton generation

## Current Priorities

### Priority 1 - Contract Reinforcement

Objective:
Reduce implicit contracts in production runtime.

Actions:

- introduce typed execution plan
- define stronger tool payload contracts
- define stronger tool result contract
- strengthen `BaseTool`

### Priority 2 - Execution Control

Objective:
Make execution semantics safer and more explicit.

Actions:

- enforce meaningful `dry_run`
- use `read_only` and `risk_level` in policy decisions
- prepare payload-aware restrictions

### Priority 3 - Runtime Robustness

Objective:
Make the production runtime resilient under failure.

Actions:

- add controlled exception handling by pipeline stage
- standardize error responses
- improve domain-level traceability

### Priority 4 - Composition Cleanup

Objective:
Separate bootstrap from orchestration.

Actions:

- inject planner, policy engine, and registry into runtime
- move composition logic out of orchestrator module
- prepare a dedicated bootstrap layer

### Priority 5 - Experimental Lab Maturation

Objective:
Make the lab path reviewable and operationally clearer without promoting it to production.

Actions:

- improve proposal schema quality
- improve staging review workflow
- improve generated artifact metadata
- add explicit approval/promotion design without activation

## Explicitly Future, Not Current

The following are not current production capabilities:

- real LLM-backed planning
- autonomous tool activation
- production self-extension
- dynamic package installation
- arbitrary shell execution
- production memory/state orchestration

## Guiding Principle

Stabilize before expanding.

The production runtime should become more explicit and controlled before experimental capabilities become more ambitious.


--- FILE: docs/vision/architecture_vision.md | bytes=2786 | sha256_12=35b84f44d3c4 ---
# Architecture Vision

## Purpose

This document describes the target architecture of NUCLEO. It is intentionally future-oriented and must not be read as a statement of verified current behavior.

For implemented behavior, see:

- `docs/architecture.md`

## Target Direction

NUCLEO should evolve toward a modular agent runtime with:

- explicit internal contracts
- controlled execution semantics
- typed execution planning
- richer policy enforcement
- auditable orchestration
- isolated experimental surfaces for LLM-assisted capability growth

## Target Flow

Request  
→ API  
→ AgentService  
→ Runtime  
→ Planner  
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse

The target shape preserves the stable pipeline, but strengthens contract quality and operational control at each stage.

## Target Component Design

### API

- Transport boundary only
- Authentication and request validation at edge
- No business execution logic

### AgentService

- Stable application entrypoint
- Runtime facade
- Future tracing and orchestration hooks

### Runtime

- Central orchestration layer
- Explicit plan handling
- Controlled failure semantics
- Isolated branching between production runtime and experimental lab flows

### Planner

- Evolve from ad hoc rules to more explicit planning structures
- Support declarative rules first
- Support optional LLM-assisted proposal logic later
- Never become the final authority for execution

### PolicyEngine

- Move from name-based checks to metadata-aware and payload-aware control
- Enforce meaningful `dry_run`
- Preserve deny-by-default behavior

### ToolRegistry

- Keep production registry distinct from staging or lab registries
- Strengthen registration contracts and metadata validation

### Tools

- Typed input/output contracts
- Clear metadata semantics
- Safer execution boundaries

### Experimental Lab

- Remain isolated from production runtime
- Support proposal generation, skeleton generation, staging review, and auditability
- Never auto-promote to production without explicit review

## Design Principles

- explicit control over execution
- no hidden authority shifts toward models or generated artifacts
- separation of concerns
- stable production path
- isolated experimental path
- traceability before autonomy

## Known Gap Between Current State and Vision

Current code already contains a first experimental lab path, but the target architecture is still not complete. In particular, the following remain future or partial:

- typed execution plan
- strict runtime plan validation
- full dry-run enforcement
- payload-aware policy
- complete traceability of production execution
- real LLM-backed planning under controlled conditions
- formal promotion workflow from staging to production


--- FILE: docs_esp/EVOLUTION_MAP.md | bytes=4161 | sha256_12=0cf69ec19971 ---
> Archivo origen: `docs/EVOLUTION_MAP.md`
> Última sincronización: `2026-04-19`

# Mapa de evolución

## Propósito

Este documento traza la transición desde el estado actualmente verificado del sistema hacia un runtime más robusto, distinguiendo con claridad entre capacidades implementadas, parciales, experimentales y futuras.

## Estado actual verificado

El repositorio ofrece actualmente:

- entrypoint FastAPI para ejecución del runtime
- `AgentService` como fachada sobre `AgentRuntime`
- `AgentRuntime` como orquestador de producción
- `Planner` basado en reglas
- `PolicyEngine` name-based con comprobación de rol para `system_info`
- `ToolRegistry` para resolución de tools de producción
- tools de producción:
  - `echo`
  - `system_info`
- `ExecutionContext` propagado a través de API, runtime, policy y tools
- `AgentResponse` con `status`, `message` y `result` opcional

## Estado experimental actual

El repositorio también contiene un subsistema experimental de laboratorio aislado:

- señal de capability gap desde el planner cuando se solicita explícitamente
- placeholder determinista para generación de proposals
- staging registry aislado
- generación de skeletons solo de laboratorio
- generación de artefactos de audit

Este subsistema está implementado, pero no forma parte de la ruta estable del registry de producción.

## Principales debilidades pendientes

### 1. Contratos internos débiles

- la salida del planner sigue siendo implícita
- los contratos de payload de las tools siguen siendo implícitos
- la salida de las tools aún no está estandarizada más allá del contenedor actual de respuesta

### 2. Control de ejecución incompleto

- `dry_run` sigue sin imponerse de forma estructural en producción
- la policy no evalúa el payload en profundidad
- los metadatos `read_only` y `risk_level` aún no se aplican desde policy

### 3. Gaps de robustez del runtime

- manejo limitado de excepciones estructuradas en runtime
- no existe una taxonomía formal de errores de dominio

### 4. Acoplamiento de bootstrap

- planner, policy engine, registry y servicios experimentales siguen componiéndose en tiempo de importación del módulo

### 5. Riesgo de deriva documental y operativa

- los documentos históricos contienen snapshots anteriores y deben leerse como logs, no como verdad actual
- `docs_esp/` es ahora una traducción mantenida de `docs/`, pero `docs/` sigue siendo la fuente primaria verificada

## Prioridades de evolución

### Prioridad 1 - Reforzar contratos

- introducir un execution plan tipado
- definir contratos estructurados de payload para tools
- definir contratos más sólidos para resultados de tools
- reforzar el contrato de `BaseTool`

### Prioridad 2 - Imponer control de ejecución

- hacer que `dry_run` tenga efecto real
- usar metadatos de tools en decisiones de policy
- preparar comprobaciones de policy sensibles al payload

### Prioridad 3 - Mejorar la robustez del runtime

- añadir manejo controlado de errores por etapa del pipeline
- estandarizar respuestas de error de dominio
- mejorar la trazabilidad

### Prioridad 4 - Desacoplar composición y orquestación

- inyectar planner, registry y policy en el runtime
- mover la composición de producción y del laboratorio a una capa de bootstrap dedicada

### Prioridad 5 - Madurar el laboratorio experimental

- workflow real de review para el staging registry
- metadatos más ricos en artefactos
- proceso explícito de promoción
- integración real con LLM solo detrás de límites controlados

## Aún no recomendado

Lo siguiente no debe tratarse todavía como prioridad de producción antes de reforzar contratos y control de ejecución:

- activación autónoma de tools
- autoextensión de producción
- autoridad no controlada del planner soportado por LLM
- ejecución distribuida
- orquestación implícita de memoria/estado

## Resultado objetivo

Un runtime con:

- contratos explícitos
- ejecución controlada
- registry de producción estable
- laboratorio experimental aislado
- orquestación trazable
- documentación que separe con claridad el estado actual de la visión futura


--- FILE: docs_esp/_deprecated/audits/files.audit.md | bytes=1542 | sha256_12=2227e693c723 ---
﻿> Nota de consistencia documental (2026-04-19): docs_esp/ es actualmente un espejo parcial en español. La fuente primaria de verdad documental del repositorio es docs/. Si hay discrepancia con el código o con docs/, prevalece docs/ y la arquitectura verificada en código.

# AuditorÃ­a de archivos

## PropÃ³sito

Registrar quÃ© partes del repositorio han sido auditadas.

Este documento no duplica auditorÃ­as detalladas.  
Solo indica cobertura y referencias.

---

## MÃ³dulos auditados

- `app/services/agent_service.py` â†’ ver `docs/modules/agent_service.md`  
- `app/runtime/orchestrator.py` â†’ ver `docs/modules/orchestrator.md`  
- `app/runtime/planner.py` â†’ ver `docs/modules/planner.md`  
- `app/policies/engine.py` â†’ ver `docs/modules/policy_engine.md`  
- `app/tools/base.py` â†’ ver `docs/modules/base_tool.md`  
- `app/tools/registry.py` â†’ ver `docs/modules/tool_registry.md`  

---

## Revisados estructuralmente

- `app/main.py`  
- `app/api/routes/*`  
- `app/policies/models.py`  
- `app/schemas/*`  
- `app/runtime/dispatcher.py`  

(cubiertos en `repo_audit.md`)

---

## Resumen

El sistema es modular y estÃ¡ correctamente separado, pero depende en gran medida de contratos implÃ­citos:

- el contrato planner â†’ runtime no estÃ¡ validado  
- la entrada/salida de las tools no estÃ¡ estructurada  
- la policy no aplica modos de ejecuciÃ³n  
- el runtime no gestiona fallos  

La arquitectura es sÃ³lida, pero aÃºn se encuentra en fase bootstrap.

--- FILE: docs_esp/_deprecated/audits/repo.audit.md | bytes=2969 | sha256_12=2617324684c5 ---
﻿> Nota de consistencia documental (2026-04-19): docs_esp/ es actualmente un espejo parcial en español. La fuente primaria de verdad documental del repositorio es docs/. Si hay discrepancia con el código o con docs/, prevalece docs/ y la arquitectura verificada en código.

# AuditorÃ­a del repositorio

## PropÃ³sito

Este documento evalÃºa el repositorio como estructura de cÃ³digo:
- organizaciÃ³n de directorios  
- lÃ­mites entre mÃ³dulos  
- consistencia de nombres  
- riesgos de escalabilidad en la estructura del proyecto  
- alineaciÃ³n entre la estructura fÃ­sica y la arquitectura prevista  

EstÃ¡ basado en la implementaciÃ³n actual auditada.

---

## Estructura actual del repositorio

Estructura de alto nivel (auditada):

## Estructura del repositorio (real)

```text
app/
  -main.py                    â†’ Punto de entrada FastAPI; inicializa la app y registra rutas

  api/
    routes/
      agent.py              â†’ POST `/agent/run`; ejecuta el agente vÃ­a AgentService
      health.py             â†’ GET `/health`; endpoint de estado (liveness)
      tools.py              â†’ GET `/tools`; expone tools registradas

  -services/
    agent_service.py        â†’ Fachada ligera; delega la ejecuciÃ³n en AgentRuntime

  -runtime/
    orchestrator.py         â†’ Pipeline de ejecuciÃ³n central; coordina planner, policy y tools
    planner.py              â†’ LÃ³gica de decisiÃ³n basada en reglas; mapea user_input â†’ tool + payload
    dispatcher.py           â†’ (planificado) router de ejecuciÃ³n; decidirÃ¡ dÃ³nde/cÃ³mo se ejecutan las tools

  -policies/
    engine.py               â†’ Control de ejecuciÃ³n; permite/deniega en base al nombre de la tool
    models.py               â†’ Esquema PolicyDecision (decision + reason)

  -tools/
    base.py                 â†’ DefiniciÃ³n de interfaz de tool (BaseTool)
    registry.py             â†’ Registro de tools; resuelve tools por nombre
    local/                  â†’ Implementaciones concretas (ej. echo, system_info)

  -schemas/
    requests.py             â†’ Modelo AgentRequest (contrato de entrada)
    responses.py            â†’ Modelo AgentResponse (contrato de salida)
    execution.py            â†’ Modelos de ejecuciÃ³n (PlanStep, ToolResult)

docs/
  -architecture.md           â†’ Comportamiento verificado del sistema (fuente de verdad)
  -evolution_map.md          â†’ Roadmap tÃ©cnico y prioridades de evoluciÃ³n

  -modules/                  â†’ AuditorÃ­a por mÃ³dulo (runtime, planner, etc.)
  -audits/                   â†’ AuditorÃ­as de repositorio y archivos
  -operations/               â†’ Estado operativo, session log, snapshots
  -planning/                 â†’ Plan de desarrollo y siguientes pasos
  -vision/                   â†’ Arquitectura objetivo (diseÃ±o futuro)

--- FILE: docs_esp/architecture.md | bytes=5181 | sha256_12=49e68d6c76cc ---
> Archivo origen: `docs/architecture.md`
> Última sincronización: `2026-04-19`

# Arquitectura - Estado actual verificado

## Propósito

Este documento es la fuente de verdad para la arquitectura que puede verificarse directamente en el código actual. Describe comportamiento implementado, comportamiento experimental explícito y limitaciones conocidas cuando son observables en el repositorio.

## Convención documental

Este repositorio separa la documentación en capas:

- Arquitectura verificada: comportamiento implementado y verificable en código
- Arquitectura objetivo / visión: diseño futuro previsto
- Operación: estado de ejecución, reglas operativas y logs históricos
- Auditorías: evaluación crítica, riesgos, gaps y comprobaciones de consistencia
- Session logs: registro cronológico de decisiones y cambios

Si una capacidad es experimental, parcial o futura, debe etiquetarse de forma explícita.

## Flujo de ejecución verificado

Flujo estable del runtime:

AgentRequest  
-> AgentService  
-> AgentRuntime  
-> Planner  
-> PolicyEngine  
-> ToolRegistry  
-> Tool  
-> AgentResponse

## Endpoints verificados

- `GET /` -> respuesta de health
- `GET /tools` -> lista de tools de producción registradas
- `POST /agent/run` -> ejecuta el runtime del agente

## Responsabilidades verificadas de los componentes

### API

- Recibe peticiones HTTP
- Resuelve la autenticación en el borde de la request
- Construye `ExecutionContext`
- Delega en `AgentService`

### AgentService

- Fachada ligera de servicio sobre `AgentRuntime`
- Propaga `AgentRequest` y `ExecutionContext`
- No asume planificación, policy ni ejecución de tools

### AgentRuntime

- Coordina el pipeline del runtime
- Invoca al planner
- Invoca al policy engine
- Resuelve tools a través del registry de producción
- Ejecuta tools de producción
- Devuelve `AgentResponse`

### Planner

- Realiza planificación simple basada en reglas
- Devuelve un `dict` implícito
- Puede emitir:
  - un plan de tool de producción
  - una señal experimental `capability_gap_detected` cuando se solicita explícitamente

### PolicyEngine

- Requiere un `ExecutionContext` autenticado
- Permite `echo`
- Permite `system_info` solo para `admin`
- Deniega cualquier otra tool de producción por nombre

### ToolRegistry

- Almacena instancias de tools de producción en un diccionario
- Resuelve tools por `tool.name`
- Está separado de staging y de los registries experimentales

### Tools de producción

Actualmente registradas en tiempo de importación en el runtime de producción:

- `echo`
- `system_info`

### AgentResponse

El modelo de respuesta actual del runtime contiene:

- `status`
- `message`
- `result` opcional

`message` sigue rellenándose con `str(result)` por compatibilidad hacia atrás.

## Contratos actuales verificados

### AgentRequest

Campos actuales:

- `user_input: str`
- `dry_run: bool = True`
- `experimental_tool_generation: bool = False`

### Salida del Planner

El planner sigue devolviendo un `dict` implícito. El contrato aún no está tipado de forma fuerte en el runtime estable.

Claves observadas:

- `tool`
- `payload`
- `mode`

Cuando se activa la detección experimental de gaps, pueden aparecer claves adicionales:

- `original_input`
- `capability_gap`

### PolicyDecision

Campos actuales:

- `decision`
- `reason`

## Subsistema experimental verificado

Existe un subsistema experimental para propuesta controlada de tools y generación de skeletons, implementado en módulos aislados y en `runtime_lab/`.

### Flujo experimental

Esta ruta es opt-in y no modifica el registry de producción:

AgentRequest con `experimental_tool_generation=True`  
-> Planner puede emitir `capability_gap_detected`  
-> AgentRuntime gestiona el gap  
-> ToolProposalService crea una proposal estructurada  
-> StagingRegistry guarda el estado aislado de staging  
-> ToolGenerationService crea un skeleton solo de laboratorio  
-> AuditStore registra eventos del laboratorio  
-> AgentResponse devuelve un resultado controlado de `capability_gap`

### Regla arquitectónica importante

Las tools experimentales generadas no se auto-registran en el `ToolRegistry` de producción.

## Restricciones y limitaciones verificadas

- La salida del planner sigue siendo implícita y no está validada en runtime
- `dry_run` sigue propagándose, pero no está impuesto de forma estructural para la ejecución de tools de producción
- La policy sigue siendo en gran parte name-based
- Metadatos de tools como `read_only` y `risk_level` aún no se aplican desde policy
- El bootstrap de producción sigue ocurriendo en tiempo de importación en `orchestrator.py`
- El manejo de errores en runtime sigue siendo limitado

## Explícitamente no verificado

Lo siguiente no debe describirse como comportamiento implementado en producción:

- Planificación real soportada por LLM
- Autoextensión del registry de producción
- Instalación dinámica de paquetes
- Ejecución arbitraria de shell
- Promoción autónoma desde staging a producción

Esos comportamientos no están implementados o solo aparecen documentados como dirección futura en otros documentos.


--- FILE: docs_esp/architecture/llm_tool_expansion.md | bytes=1402 | sha256_12=a8439b9ce73b ---
> Archivo origen: `docs/architecture/llm_tool_expansion.md`
> Última sincronización: `2026-04-19`

# Arquitectura de expansión de tools con LLM

## Propósito

Este documento describe un subsistema experimental y aislado para generación controlada de tools asistida por LLM en NUCLEO. El diseño amplía el runtime existente sin sustituir el pipeline estable de producción.

## Ruta estable

La ruta de producción permanece así:

API -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> Tool

Las tools existentes conservan su comportamiento actual.

## Ruta experimental

Cuando el planner detecta un capability gap y la request habilita explícitamente el flujo de laboratorio, NUCLEO crea una proposal estructurada, la almacena en `runtime_lab/proposals/`, la registra en un staging registry aislado, genera un skeleton de tool bajo `runtime_lab/generated_tools/` y registra artefactos de audit bajo `runtime_lab/audit/`.

Esta ruta nunca registra la tool generada en el `ToolRegistry` de producción.

## Propiedades de seguridad

- No se introduce ejecución de shell.
- No se introduce instalación de paquetes.
- Las tools generadas no se auto-cargan en el runtime de producción.
- El enforcement de policy no cambia para las tools de producción.
- Se escribe un audit trail para creación de proposals, actualizaciones de staging, generación y orquestación.


--- FILE: docs_esp/audits/docs_esp_sync_audit.md | bytes=4822 | sha256_12=11f39fd6cdfa ---
> Archivo origen: `docs/audits/docs_esp_sync_audit.md`
> Última sincronización: `2026-04-19`

# Auditoría de sincronización de docs_esp

## Alcance

Sincronización estructural y de contenido entre `docs/` y `docs_esp/` para que `docs_esp/` funcione como traducción completa y mantenida de la documentación primaria.

## Regla aplicada

- `docs/` es la fuente de verdad
- `docs_esp/` debe reflejar `docs/` de forma fiel
- los nombres de componentes se mantienen en inglés cuando son nombres propios del sistema
- el contenido sin correspondencia se mueve a `_deprecated/` o `_review/`

## Mapa de correspondencia 1:1

- `docs/architecture.md` -> `docs_esp/architecture.md`
- `docs/EVOLUTION_MAP.md` -> `docs_esp/EVOLUTION_MAP.md`
- `docs/vision/architecture_vision.md` -> `docs_esp/vision/architecture_vision.md`
- `docs/architecture/llm_tool_expansion.md` -> `docs_esp/architecture/llm_tool_expansion.md`
- `docs/planning/development_plan.md` -> `docs_esp/planning/development_plan.md`
- `docs/operations/operational_state.md` -> `docs_esp/operations/operational_state.md`
- `docs/operations/dev_state_snapshot.md` -> `docs_esp/operations/dev_state_snapshot.md`
- `docs/operations/session_log.md` -> `docs_esp/operations/session_log.md`
- `docs/operations/session_log_docs_normalization.md` -> `docs_esp/operations/session_log_docs_normalization.md`
- `docs/operations/session_log_llm_tool_expansion.md` -> `docs_esp/operations/session_log_llm_tool_expansion.md`
- `docs/operations/session_log_docs_esp_sync.md` -> `docs_esp/operations/session_log_docs_esp_sync.md`
- `docs/modules/agent_service.md` -> `docs_esp/modules/agent_service.md`
- `docs/modules/orchestrator.md` -> `docs_esp/modules/orchestrator.md`
- `docs/modules/planner.md` -> `docs_esp/modules/planner.md`
- `docs/modules/policy_engine.md` -> `docs_esp/modules/policy_engine.md`
- `docs/modules/tool_registry.md` -> `docs_esp/modules/tool_registry.md`
- `docs/modules/base_tool.md` -> `docs_esp/modules/base_tool.md`
- `docs/modules/tool_proposal_service.md` -> `docs_esp/modules/tool_proposal_service.md`
- `docs/modules/tool_generation_service.md` -> `docs_esp/modules/tool_generation_service.md`
- `docs/modules/staging_registry.md` -> `docs_esp/modules/staging_registry.md`
- `docs/modules/audit_store.md` -> `docs_esp/modules/audit_store.md`
- `docs/audits/repo_audit.md` -> `docs_esp/audits/repo_audit.md`
- `docs/audits/files_audit.md` -> `docs_esp/audits/files_audit.md`
- `docs/audits/documentation_consistency_audit.md` -> `docs_esp/audits/documentation_consistency_audit.md`
- `docs/audits/docs_esp_sync_audit.md` -> `docs_esp/audits/docs_esp_sync_audit.md`

## Archivos creados en docs_esp

- `docs_esp/architecture/llm_tool_expansion.md`
- `docs_esp/operations/session_log_docs_normalization.md`
- `docs_esp/operations/session_log_llm_tool_expansion.md`
- `docs_esp/operations/session_log_docs_esp_sync.md`
- `docs_esp/modules/tool_proposal_service.md`
- `docs_esp/modules/tool_generation_service.md`
- `docs_esp/modules/staging_registry.md`
- `docs_esp/modules/audit_store.md`
- `docs_esp/audits/repo_audit.md`
- `docs_esp/audits/files_audit.md`
- `docs_esp/audits/documentation_consistency_audit.md`
- `docs_esp/audits/docs_esp_sync_audit.md`

## Archivos actualizados en docs_esp

- `docs_esp/architecture.md`
- `docs_esp/EVOLUTION_MAP.md`
- `docs_esp/vision/architecture_vision.md`
- `docs_esp/planning/development_plan.md`
- `docs_esp/operations/operational_state.md`
- `docs_esp/operations/dev_state_snapshot.md`
- `docs_esp/operations/session_log.md`
- `docs_esp/modules/agent_service.md`
- `docs_esp/modules/orchestrator.md`
- `docs_esp/modules/planner.md`
- `docs_esp/modules/policy_engine.md`
- `docs_esp/modules/tool_registry.md`
- `docs_esp/modules/base_tool.md`

## Archivos movidos a deprecated

- `docs_esp/audits/repo.audit.md` -> `docs_esp/_deprecated/audits/repo.audit.md`
- `docs_esp/audits/files.audit.md` -> `docs_esp/_deprecated/audits/files.audit.md`

## Discrepancias detectadas

- `docs_esp/` no cubría todos los documentos existentes en `docs/`
- `docs_esp/audits/` usaba nombres heredados (`repo.audit.md`, `files.audit.md`) que ya no coincidían con la estructura primaria
- varios documentos en `docs_esp/` reflejaban un estado previo, no la narrativa documental actual

## Decisiones tomadas

- sincronizar `docs_esp/` con estructura 1:1 respecto a `docs/`
- añadir cabecera en cada archivo traducido con archivo origen y fecha de sincronización
- mantener nombres de componentes y módulos en inglés
- mantener `docs/` como fuente primaria de verdad, incluso tras la sincronización

## Contenido no verificable

- no se añadió contenido nuevo no presente en `docs/`
- cuando `docs/` ya marcaba una capacidad como parcial o no verificada, `docs_esp/` conserva exactamente ese mismo nivel de certeza


--- FILE: docs_esp/audits/documentation_consistency_audit.md | bytes=8216 | sha256_12=ed1a8568244b ---
> Archivo origen: `docs/audits/documentation_consistency_audit.md`
> Última sincronización: `2026-04-19`

# Auditoría de consistencia documental

## Alcance

Auditoría completa de Markdown de la documentación de NUCLEO, excluyendo Markdown de terceros o vendorizado bajo `.venv/`.

## Convención documental aplicada

La documentación se normaliza en estas capas:

- arquitectura verificada
- arquitectura objetivo / visión
- operación
- auditoría
- session log

Fuente primaria de verdad:

- `docs/`

Traducción mantenida:

- `docs_esp/`

Cuando existe conflicto entre documentación y código, el código se trata como la fuente de mayor confianza.

## Inventario de archivos Markdown

### Raíz

- `README.md` -> visión general del repositorio, arranque rápido y resumen del runtime verificado -> operación + visión general de entrada

### Documentación primaria

- `docs/architecture.md` -> arquitectura verificada
- `docs/EVOLUTION_MAP.md` -> roadmap de evolución desde el estado actual
- `docs/vision/architecture_vision.md` -> arquitectura objetivo
- `docs/planning/development_plan.md` -> prioridades técnicas planificadas
- `docs/operations/operational_state.md` -> estado operativo actual
- `docs/operations/dev_state_snapshot.md` -> snapshot puntual de implementación
- `docs/operations/session_log.md` -> log histórico de ingeniería
- `docs/operations/session_log_llm_tool_expansion.md` -> session log del subsistema de laboratorio
- `docs/modules/agent_service.md` -> documentación de módulo
- `docs/modules/orchestrator.md` -> documentación de módulo
- `docs/modules/planner.md` -> documentación de módulo
- `docs/modules/policy_engine.md` -> documentación de módulo
- `docs/modules/tool_registry.md` -> documentación de módulo
- `docs/modules/base_tool.md` -> documentación de módulo
- `docs/modules/tool_proposal_service.md` -> documentación de módulo experimental
- `docs/modules/tool_generation_service.md` -> documentación de módulo experimental
- `docs/modules/staging_registry.md` -> documentación de módulo experimental
- `docs/modules/audit_store.md` -> documentación de módulo experimental
- `docs/architecture/llm_tool_expansion.md` -> nota de arquitectura experimental
- `docs/audits/repo_audit.md` -> auditoría de estructura del repositorio
- `docs/audits/files_audit.md` -> auditoría de cobertura
- `docs/audits/documentation_consistency_audit.md` -> auditoría de consistencia documental

### Traducción mantenida

- `docs_esp/architecture.md`
- `docs_esp/EVOLUTION_MAP.md`
- `docs_esp/vision/architecture_vision.md`
- `docs_esp/architecture/llm_tool_expansion.md`
- `docs_esp/planning/development_plan.md`
- `docs_esp/operations/operational_state.md`
- `docs_esp/operations/dev_state_snapshot.md`
- `docs_esp/operations/session_log.md`
- `docs_esp/operations/session_log_docs_normalization.md`
- `docs_esp/operations/session_log_llm_tool_expansion.md`
- `docs_esp/operations/session_log_docs_esp_sync.md`
- `docs_esp/modules/agent_service.md`
- `docs_esp/modules/orchestrator.md`
- `docs_esp/modules/planner.md`
- `docs_esp/modules/policy_engine.md`
- `docs_esp/modules/tool_registry.md`
- `docs_esp/modules/base_tool.md`
- `docs_esp/modules/tool_proposal_service.md`
- `docs_esp/modules/tool_generation_service.md`
- `docs_esp/modules/staging_registry.md`
- `docs_esp/modules/audit_store.md`
- `docs_esp/audits/repo_audit.md`
- `docs_esp/audits/files_audit.md`
- `docs_esp/audits/documentation_consistency_audit.md`
- `docs_esp/audits/docs_esp_sync_audit.md`

## Contradicciones detectadas

### 1. Estado actual de arquitectura frente a notas históricas de auth

Conflicto:
- `docs/architecture.md` mezclaba notas de runtime verificado con una sección histórica de diseño de auth.

Decisión:
- Normalizar `docs/architecture.md` como arquitectura verificada únicamente.
- Mantener auth como parte del estado actual verificado, no como nota futura.

### 2. Estructura de la respuesta

Conflicto:
- documentos anteriores afirmaban que la respuesta solo tenía `status + message`
- el código actual incluye `result` opcional

Decisión:
- todos los documentos primarios se actualizaron para describir `result` como comportamiento actual verificado
- los logs históricos se conservan como logs, no como verdad actual

### 3. Estado de ExecutionContext

Conflicto:
- algunos documentos operativos decían "do not introduce ExecutionContext yet"
- el código ya incluye execution context por request

Decisión:
- los documentos operativos primarios se actualizaron al estado actual verificado
- las afirmaciones históricas se conservan solo dentro del session log como contexto histórico

### 4. Ruta experimental de laboratorio frente a ruta de producción

Conflicto:
- documentos anteriores no mencionaban el laboratorio experimental
- documentos nuevos lo describían, pero no siempre lo separaban claramente de producción

Decisión:
- los documentos primarios ahora separan:
  - runtime estable de producción
  - laboratorio experimental aislado

### 5. Comportamiento de Policy

Conflicto:
- varios documentos describían una policy solo basada en whitelist
- el código ahora también comprueba autenticación y rol admin para `system_info`

Decisión:
- los documentos primarios se actualizaron para reflejar el comportamiento actual verificado de policy

### 6. Comportamiento del Planner

Conflicto:
- documentos anteriores describían solo la rama `system_info` / `echo`
- el código ahora también tiene señalización opt-in de capability gap

Decisión:
- los documentos primarios se actualizaron para describir ambas:
  - comportamiento estable de producción
  - rama experimental opt-in

### 7. `docs/` frente a `docs_esp/`

Conflicto:
- `docs_esp/` era parcial y podía contradecir a `docs/`

Decisión:
- sincronizar `docs_esp/` como traducción mantenida de `docs/`
- mantener `docs/` como fuente primaria verificada

## Contradicciones no completamente resueltas

### Operatividad de la persistencia en runtime_lab

Motivo:
- el código implementa persistencia respaldada por ficheros para el laboratorio
- la sesión del repositorio no pudo verificar completamente el comportamiento de escritura de artefactos en el entorno de sandbox actual

Decisión:
- documentarlo como ruta de código implementada
- evitar afirmar verificación operativa completa

### Rol de dispatcher

Motivo:
- `runtime/dispatcher.py` existe, pero no está integrado en el flujo principal del runtime

Decisión:
- describirlo como presente, pero no integrado

## Documentos redundantes o solapados

- `docs/operations/operational_state.md` y `docs/operations/dev_state_snapshot.md` se solapan, pero ahora sirven a ámbitos distintos:
  - operational state = modelo operativo actual
  - dev snapshot = snapshot puntual de implementación
- `docs/architecture.md` y `docs/vision/architecture_vision.md` se solapan en tema, pero ahora difieren claramente por horizonte temporal
- `docs_esp/` se superpone con `docs/`, pero ahora se trata como traducción mantenida, no como fuente primaria verificada

## Jerarquía documental recomendada

1. `README.md` -> entrada al repositorio
2. `docs/architecture.md` -> arquitectura verificada
3. `docs/vision/architecture_vision.md` -> diseño futuro
4. `docs/operations/*` -> estado y logs
5. `docs/modules/*` -> detalle por componente
6. `docs/audits/*` -> evaluación crítica
7. `docs_esp/*` -> traducción mantenida

## Archivos modificados durante la normalización

- `README.md`
- `docs/architecture.md`
- `docs/vision/architecture_vision.md`
- `docs/EVOLUTION_MAP.md`
- `docs/operations/operational_state.md`
- `docs/operations/dev_state_snapshot.md`
- `docs/operations/session_log.md`
- `docs/planning/development_plan.md`
- `docs/modules/agent_service.md`
- `docs/modules/orchestrator.md`
- `docs/modules/planner.md`
- `docs/modules/policy_engine.md`
- `docs/modules/tool_registry.md`
- `docs/modules/base_tool.md`
- `docs/audits/repo_audit.md`
- `docs/audits/files_audit.md`
- `docs/audits/documentation_consistency_audit.md`
- `docs/operations/session_log_docs_normalization.md`
- los archivos `docs_esp/*.md` se marcaron primero como mirror de traducción y después se sincronizaron


--- FILE: docs_esp/audits/files_audit.md | bytes=1272 | sha256_12=25239e4a1384 ---
> Archivo origen: `docs/audits/files_audit.md`
> Última sincronización: `2026-04-19`

# Auditoría de ficheros

## Capa

Auditoría

## Propósito

Registrar qué ficheros técnicos y módulos están cubiertos por documentación o por auditoría del repositorio.

## Módulos cubiertos del runtime de producción

- `app/services/agent_service.py`
- `app/runtime/orchestrator.py`
- `app/runtime/planner.py`
- `app/policies/engine.py`
- `app/tools/base.py`
- `app/tools/registry.py`

## Módulos cubiertos del laboratorio experimental

- `app/services/tool_proposal/tool_proposal_service.py`
- `app/services/tool_generation/tool_generation_service.py`
- `app/services/staging/staging_registry.py`
- `app/services/audit/audit_store.py`
- `app/domain/tool_proposals/models.py`
- `app/domain/staging/models.py`
- `app/schemas/tool_proposal.py`

## Revisado estructuralmente

- `app/main.py`
- `app/api/routes/*`
- `app/api/deps/auth.py`
- `app/schemas/*`
- `app/runtime/dispatcher.py`
- `runtime_lab/*`

## Resumen

La cobertura del repositorio es suficiente para describir la ruta estable de ejecución y la ruta actual aislada de laboratorio. El principal riesgo documental que permanece es la deriva histórica entre archivos, más que la falta de cobertura de módulos.


--- FILE: docs_esp/audits/repo_audit.md | bytes=2311 | sha256_12=84fe8edd7bbe ---
> Archivo origen: `docs/audits/repo_audit.md`
> Última sincronización: `2026-04-19`

# Auditoría del repositorio

## Capa

Auditoría

## Propósito

Evaluar la estructura del repositorio, los límites entre módulos, la consistencia de nombres y el ajuste entre el layout físico y la intención arquitectónica.

## Forma actual del repositorio

Estructura de alto nivel verificada en el repositorio:

- `app/`
- `docs/`
- `docs_esp/`
- `runtime_lab/`

### Estructura de aplicación

- `api/` -> rutas HTTP y frontera de auth
- `services/` -> capa de servicio y servicios del laboratorio
- `runtime/` -> orquestación y planificación
- `policies/` -> control de ejecución
- `tools/` -> tools de producción
- `schemas/` -> schemas de request, response y experimentales
- `domain/` -> entidades de dominio del laboratorio

### Estructura de documentación

- `docs/architecture.md` -> arquitectura verificada
- `docs/vision/` -> visión objetivo
- `docs/operations/` -> estado operativo y session logs
- `docs/audits/` -> auditorías
- `docs/modules/` -> documentación por módulo
- `docs/planning/` -> roadmap de desarrollo

### Estructura experimental de runtime-lab

- `runtime_lab/proposals/`
- `runtime_lab/generated_tools/`
- `runtime_lab/staging_registry/`
- `runtime_lab/audit/`

## Fortalezas estructurales

- separación clara entre runtime de producción y artefactos del laboratorio
- límites razonables de paquetes para la escala actual
- la estructura documental puede soportar múltiples capas documentales

## Riesgos estructurales

- la composición del runtime de producción sigue embebida en el módulo de runtime
- existen mirrors documentales (`docs_esp/`) que pueden derivar
- la persistencia de `runtime_lab/` está operativamente separada, pero sigue colocalizada en el workspace del repo

## Evaluación de nombres

Los nombres primarios actuales son coherentes y deberían permanecer estables:

- runtime
- orchestrator
- planner
- policy engine
- tool registry
- tool
- staging
- audit
- proposal
- lab / runtime_lab

## Evaluación general

El repositorio sigue siendo estructuralmente coherente, pero la deriva documental y la composición en tiempo de importación siguen siendo los principales riesgos a nivel de arquitectura, más que el desorden de directorios en sí.


--- FILE: docs_esp/modules/agent_service.md | bytes=991 | sha256_12=d40b086d377a ---
> Archivo origen: `docs/modules/agent_service.md`
> Última sincronización: `2026-04-19`

# AgentService

## Capa

Arquitectura verificada

## Propósito

Proporcionar una fachada estable de capa de servicio entre las rutas de API y la orquestación del runtime.

## Comportamiento actual verificado

`AgentService` actualmente:

- instancia `AgentRuntime`
- expone `run(request, context)`
- delega la ejecución directamente al runtime

Actualmente no asume:

- planificación
- policy
- ejecución de tools
- lógica de generación de proposals del laboratorio

## Fortalezas

- mantiene la API ligera
- preserva un entrypoint estable
- es un lugar limpio para futuros hooks de tracing u orquestación

## Limitaciones actuales

- la dependencia del runtime sigue construyéndose directamente
- todavía no existe una frontera independiente de normalización de errores

## Etiqueta de estado

- Fachada de servicio: implementada
- Frontera de inyección de dependencias: no implementada


--- FILE: docs_esp/modules/audit_store.md | bytes=548 | sha256_12=7954f61d3752 ---
> Archivo origen: `docs/modules/audit_store.md`
> Última sincronización: `2026-04-19`

# AuditStore

## Responsabilidad

`AuditStore` persiste eventos simples y estructurados de audit para el workflow experimental de expansión de tools.

## Campos del evento

- event
- timestamp
- proposal_id
- action
- result
- artifact_paths
- metadata

## Salida

Cada evento se escribe como un archivo JSON bajo `runtime_lab/audit/`.

## Notas

- El store es append-only en esta fase.
- Los artefactos de audit soportan review y trazabilidad a posteriori.


--- FILE: docs_esp/modules/base_tool.md | bytes=817 | sha256_12=08c1e47af18f ---
> Archivo origen: `docs/modules/base_tool.md`
> Última sincronización: `2026-04-19`

# BaseTool

## Capa

Arquitectura verificada

## Propósito

Definir la interfaz conceptual común para las tools de producción.

## Comportamiento actual verificado

`BaseTool` actualmente declara:

- `name`
- `description`
- `read_only`
- `risk_level`
- `run(payload, context=None)`

Se espera que las tools concretas implementen `run(...)`.

## Realidad actual importante

- `BaseTool` no es una clase base abstracta estricta
- los metadatos no se validan en tiempo de construcción
- los metadatos aún no se aplican desde policy
- los contratos de entrada/salida siguen siendo implícitos

## Etiqueta de estado

- Concepto común de contrato de tool: implementado
- Enforcement fuerte de contratos tipados: no implementado


--- FILE: docs_esp/modules/orchestrator.md | bytes=1946 | sha256_12=7f316b8e524e ---
> Archivo origen: `docs/modules/orchestrator.md`
> Última sincronización: `2026-04-19`

# AgentRuntime

## Capa

Arquitectura verificada

## Propósito

Orquestador central de ejecución del runtime de producción, con una rama aislada mínima para el manejo experimental de capability gaps.

## Comportamiento actual verificado

`AgentRuntime.run(request, context)` actualmente:

1. pide un plan al planner
2. si el plan señala `capability_gap_detected`, deriva a la ruta aislada del laboratorio
3. en caso contrario extrae `tool` y `payload` de producción
4. pide autorización al `PolicyEngine`
5. si la policy deniega,

```
